from pathlib import Path
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

from scraper_core.http_client import fetch_response
from scraper_core.reviewer_pipeline import normalize_reviewer_columns

VISITED_STORE_COLUMNS = [
    "reviewer_name",
    "reviewer_url",
    "store_id",
    "store_name",
    "store_address",
    "store_genre",
    "store_tellnum",
    "store_closedday",
    "store_homepage",
    "store_dinner_price_range",
    "store_lunch_price_range",
    "store_score",
]


def _resolve_reviewer_input_path(input_csv_path: Optional[str]) -> Path:
    if input_csv_path:
        return Path(input_csv_path)

    default_candidates = [
        Path("./seasonal_reviewer_flow/integrate_reviewer/all_reviewer.csv"),
        Path("./seasonal_reviewer_flow/integrate_reviewer/all_reviewr.csv"),
    ]
    for candidate in default_candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("integrated reviewer csv not found")


def _reviewer_list_url(reviewer_url: str, page_num: int, test_mode: bool) -> str:
    base = reviewer_url.rstrip("/") + "/"
    if test_mode:
        return f"{base}visited_restaurants/list?PG={page_num}&select_sort_flg=1"
    return f"{base}visited_restaurants/list?PG={page_num}&Srt=D&SrtT=rvcn"


def _parse_store_genre(raw_genre_text: str) -> str:
    normalized = raw_genre_text.replace(" ", "").replace("　", "")
    parts = normalized.split("/")
    return parts[1] if len(parts) > 1 else normalized


def _extract_store_detail(
    reviewer_name: str,
    reviewer_url: str,
    store_id_num: int,
    item_url: str,
    genre_text: str,
    sleep_seconds: float,
    request_timeout: float,
) -> Optional[dict]:
    response = fetch_response(
        item_url,
        timeout=request_timeout,
        retries=2,
        backoff_seconds=1.0,
        sleep_after=sleep_seconds,
    )
    if response is None:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    name_tag = soup.find("h2", class_="display-name")
    store_name = name_tag.span.get_text(strip=True) if name_tag and name_tag.span else ""

    rating_tag = soup.find("b", class_="c-rating__val")
    store_score = rating_tag.span.get_text(strip=True) if rating_tag and rating_tag.span else ""

    address_tag = soup.find("p", class_="rstinfo-table__address")
    store_address = address_tag.get_text(strip=True) if address_tag else ""

    store_genre = _parse_store_genre(genre_text)

    tellnum = "-"
    tell_tags = soup.find_all("strong", class_="rstinfo-table__tel-num")
    if tell_tags:
        tellnum = tell_tags[-1].get_text(strip=True)

    closedday_tag = soup.find("dd", class_="rdheader-subinfo__closed-text")
    closedday = closedday_tag.get_text(strip=True) if closedday_tag else ""

    homepage = ""
    homepage_tag = soup.find("p", class_="homepage")
    if homepage_tag and homepage_tag.find("span"):
        homepage = homepage_tag.find("span").get_text(strip=True)

    dinner_price = ""
    lunch_price = ""
    price_tags = soup.find_all("a", class_="rdheader-budget__price-target")
    if len(price_tags) >= 1:
        dinner_price = price_tags[0].get_text(strip=True)
    if len(price_tags) >= 2:
        lunch_price = price_tags[1].get_text(strip=True)

    return {
        "reviewer_name": reviewer_name,
        "reviewer_url": reviewer_url,
        "store_id": str(store_id_num),
        "store_name": store_name,
        "store_address": store_address,
        "store_genre": store_genre,
        "store_tellnum": tellnum,
        "store_closedday": closedday,
        "store_homepage": homepage,
        "store_dinner_price_range": dinner_price,
        "store_lunch_price_range": lunch_price,
        "store_score": store_score,
    }


def collect_single_reviewer_visited_stores(
    reviewer_name: str,
    reviewer_url: str,
    test_mode: bool = False,
    begin_page: int = 1,
    end_page: int = 60,
    sleep_seconds: float = 1.0,
    request_timeout: float = 20.0,
) -> pd.DataFrame:
    rows = []
    store_id_num = 0
    page_num = begin_page

    while page_num <= end_page:
        list_url = _reviewer_list_url(reviewer_url, page_num, test_mode=test_mode)
        print(f"[visited] reviewer={reviewer_name} page={page_num} url={list_url}")
        list_response = fetch_response(
            list_url,
            timeout=request_timeout,
            retries=2,
            backoff_seconds=1.0,
            sleep_after=sleep_seconds,
        )
        if list_response is None:
            break

        soup = BeautifulSoup(list_response.content, "html.parser")
        item_links = soup.find_all("a", class_="simple-rvw__rst-name-target")
        genre_tags = soup.find_all("p", class_="simple-rvw__area-catg")
        if not item_links:
            break

        iter_links = item_links[:1] if test_mode else item_links
        for idx, link in enumerate(iter_links):
            item_url = link.get("href", "").strip()
            if not item_url:
                continue
            genre_text = genre_tags[idx].get_text(strip=True) if idx < len(genre_tags) else ""
            store_id_num += 1
            row = _extract_store_detail(
                reviewer_name=reviewer_name,
                reviewer_url=reviewer_url,
                store_id_num=store_id_num,
                item_url=item_url,
                genre_text=genre_text,
                sleep_seconds=sleep_seconds,
                request_timeout=request_timeout,
            )
            if row is not None:
                rows.append(row)

        if test_mode:
            break
        page_num += 1

    return pd.DataFrame(rows, columns=VISITED_STORE_COLUMNS)


def collect_reviewer_visited_store_csvs(
    input_csv_path: Optional[str],
    output_dir: str,
    max_reviewers: Optional[int] = None,
    test_mode: bool = False,
    begin_page: int = 1,
    end_page: int = 60,
    sleep_seconds: float = 1.0,
    request_timeout: float = 20.0,
    start_index: int = 63,
) -> int:
    input_path = _resolve_reviewer_input_path(input_csv_path)
    reviewers_df = pd.read_csv(input_path).fillna("")
    reviewers_df = normalize_reviewer_columns(reviewers_df)
    reviewers_df = reviewers_df.reindex(
        columns=["reviewer_name", "reviewer_url"],
        fill_value="",
    )

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    processed = 0
    file_index = start_index
    for reviewer in reviewers_df.itertuples(index=False):
        if max_reviewers is not None and processed >= max_reviewers:
            break

        reviewer_name = str(reviewer.reviewer_name).strip()
        reviewer_url = str(reviewer.reviewer_url).strip()
        if not reviewer_url:
            continue

        file_index += 1
        visited_df = collect_single_reviewer_visited_stores(
            reviewer_name=reviewer_name,
            reviewer_url=reviewer_url,
            test_mode=test_mode,
            begin_page=begin_page,
            end_page=end_page,
            sleep_seconds=sleep_seconds,
            request_timeout=request_timeout,
        )
        visited_df.to_csv(output_dir_path / f"user{file_index}.csv", index=False)
        processed += 1
        print(f"[visited] completed reviewer={reviewer_name} rows={len(visited_df)}")

    print(f"[visited] completed reviewers={processed}")
    return processed
