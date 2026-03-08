from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from scraper_core.http_client import fetch_response

REVIEWER_COLUMNS = ["store_name", "reviewer_name", "reviewer_id", "reviewer_url"]
INTEGRATED_COLUMNS = ["reviewer_name", "reviewer_id", "reviewer_url"]
LEGACY_REVIEWER_COLUMN_MAP = {
    "reviewr_name": "reviewer_name",
    "reviewr_id": "reviewer_id",
    "reviewr_url": "reviewer_url",
}
def _safe_store_filename(store_name: str, fallback_index: int) -> str:
    cleaned = str(store_name).strip()
    for token in ["/", "\\", "\n", "\r", "\t"]:
        cleaned = cleaned.replace(token, "")
    return cleaned or f"store_{fallback_index}"


def _empty_reviewer_row(store_name: str) -> dict[str, str]:
    return {
        "store_name": store_name,
        "reviewer_name": "",
        "reviewer_id": "",
        "reviewer_url": "",
    }


def _extract_reviewer_row(store_name: str, tag) -> Optional[dict[str, str]]:
    if tag.name == "a":
        anchor = tag
        reviewer_name = tag.get_text(strip=True)
    else:
        anchor = tag.find("a")
        if anchor is None:
            return None
        name_span = tag.find("span")
        reviewer_name = (
            name_span.get_text(strip=True)
            if name_span is not None
            else anchor.get_text(strip=True)
        )

    reviewer_href = anchor.get("href")
    if not reviewer_href:
        return None

    reviewer_url = urljoin("https://tabelog.com/", reviewer_href)
    reviewer_id = reviewer_href.replace("/rvwr/", "").replace("/", "")
    return {
        "store_name": store_name,
        "reviewer_name": reviewer_name,
        "reviewer_id": reviewer_id,
        "reviewer_url": reviewer_url,
    }


def normalize_reviewer_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        old: new
        for old, new in LEGACY_REVIEWER_COLUMN_MAP.items()
        if old in df.columns
    }
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def collect_store_reviewers(
    store_name: str,
    store_url: str,
    sleep_seconds: float = 2.0,
    request_timeout: float = 20.0,
    max_pages: Optional[int] = None,
) -> pd.DataFrame:
    rows = []
    normalized_store_url = str(store_url).strip()
    if not normalized_store_url:
        rows.append(_empty_reviewer_row(store_name))
        return pd.DataFrame(rows, columns=REVIEWER_COLUMNS)

    if not normalized_store_url.endswith("/"):
        normalized_store_url += "/"

    page_num = 1
    while True:
        if max_pages is not None and page_num > max_pages:
            break

        list_url = f"{normalized_store_url}dtlrvwlst?PG={page_num}"
        print(f"[collect] store={store_name} page={page_num} url={list_url}")
        response = fetch_response(
            list_url,
            timeout=request_timeout,
            retries=2,
            backoff_seconds=1.0,
            sleep_after=sleep_seconds,
        )
        if response is None:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        reviewer_tags = soup.select("a.rvw-item__rvwr-name[href*='/rvwr/']")
        if not reviewer_tags:
            # Backward compatibility with old markup.
            reviewer_tags = soup.find_all("p", class_="rvw-item__rvwr-name")
        if not reviewer_tags:
            break

        found_reviewer = False
        for name_tag in reviewer_tags:
            row = _extract_reviewer_row(store_name, name_tag)
            if row is None:
                continue
            found_reviewer = True
            print(row["reviewer_url"], row["reviewer_name"], row["reviewer_id"])
            rows.append(row)

        if not found_reviewer:
            break

        page_num += 1

    if not rows:
        rows.append(_empty_reviewer_row(store_name))
    return pd.DataFrame(rows, columns=REVIEWER_COLUMNS)


def collect_reviewer_csvs(
    input_csv_path: str,
    output_dir: str,
    sleep_seconds: float = 2.0,
    request_timeout: float = 20.0,
    max_stores: Optional[int] = None,
    max_pages: Optional[int] = None,
) -> int:
    restaurants_info = pd.read_csv(input_csv_path).fillna("")
    required_columns = {"store_name", "tabelog_url"}
    missing_columns = required_columns - set(restaurants_info.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"missing required columns: {missing}")

    if max_stores is not None and max_stores < 1:
        raise ValueError("max_stores must be >= 1")
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be >= 1")

    stores = restaurants_info[["store_name", "tabelog_url"]].drop_duplicates()
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    for row in stores.itertuples(index=False):
        if max_stores is not None and processed_count >= max_stores:
            break
        store_name, store_url = row
        reviewer_df = collect_store_reviewers(
            store_name,
            store_url,
            sleep_seconds=sleep_seconds,
            request_timeout=request_timeout,
            max_pages=max_pages,
        )
        filename = _safe_store_filename(store_name, processed_count + 1)
        output_file = output_dir_path / f"{filename}.csv"
        reviewer_df.to_csv(output_file, index=False)
        processed_count += 1

    print(f"[collect] completed stores={processed_count}")
    return processed_count


def integrate_reviewer_csvs(source_dir: str, output_csv_path: str) -> int:
    source_dir_path = Path(source_dir)
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames = []
    if source_dir_path.exists():
        for file_path in sorted(source_dir_path.glob("*.csv")):
            try:
                reviewer_info = pd.read_csv(file_path).fillna("")
            except pd.errors.EmptyDataError:
                continue

            reviewer_info = normalize_reviewer_columns(reviewer_info)
            reviewer_info = reviewer_info.reindex(columns=REVIEWER_COLUMNS, fill_value="")
            reviewer_info = reviewer_info.drop(columns="store_name")
            frames.append(reviewer_info)

    if frames:
        integrated = pd.concat(frames, ignore_index=True)
        integrated = integrated[
            integrated["reviewer_url"].astype(str).str.strip() != ""
        ]
        integrated = integrated.drop_duplicates(subset="reviewer_url")
        integrated = integrated.reindex(columns=INTEGRATED_COLUMNS)
    else:
        integrated = pd.DataFrame(columns=INTEGRATED_COLUMNS)

    integrated.to_csv(output_path, index=False)
    print(f"[integrate] completed reviewers={len(integrated)}")
    return len(integrated)
