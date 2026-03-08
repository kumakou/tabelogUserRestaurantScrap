import re
from pathlib import Path
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

from scraper_core.http_client import fetch_response
from scraper_core.reviewer_pipeline import normalize_reviewer_columns

REVIEWER_STATS_COLUMNS = [
    "reviewer_name",
    "reviewer_id",
    "reviewer_url",
    "zenkoku_num",
    "hakodate_num",
    "rate",
]


def _parse_count(raw_value: str) -> int:
    matches = re.findall(r"\d+", str(raw_value).replace(",", ""))
    if not matches:
        return 0
    return int("".join(matches))


def _extract_zenkoku_num(soup: BeautifulSoup) -> int:
    tag = soup.find("span", class_="rvwr-navi__count")
    return _parse_count(tag.get_text(strip=True)) if tag else 0


def _extract_hakodate_num(soup: BeautifulSoup) -> int:
    nums = soup.find_all("span", class_="c-page-count__num")
    if not nums:
        return 0
    if len(nums) >= 3:
        return _parse_count(nums[2].get_text(strip=True))
    return _parse_count(nums[-1].get_text(strip=True))


def _resolve_input_path(input_csv_path: Optional[str]) -> Path:
    if input_csv_path:
        return Path(input_csv_path)

    default_candidates = [
        Path("./output_integrate/all_reviewer.csv"),
        Path("./output_integrate/all_reviewr.csv"),
    ]
    for candidate in default_candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("integrated reviewer csv not found in output_integrate")


def collect_reviewer_stats_csv(
    input_csv_path: Optional[str],
    output_csv_path: str,
    sleep_seconds: float = 1.0,
    request_timeout: float = 20.0,
    max_reviewers: Optional[int] = None,
) -> int:
    input_path = _resolve_input_path(input_csv_path)
    reviewers_df = pd.read_csv(input_path).fillna("")
    reviewers_df = normalize_reviewer_columns(reviewers_df)
    reviewers_df = reviewers_df.reindex(
        columns=["reviewer_name", "reviewer_id", "reviewer_url"],
        fill_value="",
    )

    rows = []
    for idx, reviewer in enumerate(reviewers_df.itertuples(index=False), start=1):
        if max_reviewers is not None and idx > max_reviewers:
            break

        reviewer_name = str(reviewer.reviewer_name).strip()
        reviewer_url = str(reviewer.reviewer_url).strip()
        if not reviewer_url:
            continue

        base_response = fetch_response(
            reviewer_url,
            timeout=request_timeout,
            retries=2,
            backoff_seconds=1.0,
            sleep_after=sleep_seconds,
        )
        if base_response is None:
            continue
        zenkoku_num = _extract_zenkoku_num(
            BeautifulSoup(base_response.content, "html.parser")
        )

        hakodate_url = (
            reviewer_url.rstrip("/")
            + "/visited_restaurants/list?pal=hokkaido&LstPrf=A0105&LstAre=A010501"
        )
        hakodate_response = fetch_response(
            hakodate_url,
            timeout=request_timeout,
            retries=2,
            backoff_seconds=1.0,
            sleep_after=sleep_seconds,
        )
        hakodate_num = (
            _extract_hakodate_num(BeautifulSoup(hakodate_response.content, "html.parser"))
            if hakodate_response is not None
            else 0
        )

        reviewer_id = reviewer_url.replace("https://tabelog.com/rvwr/", "").replace(
            "/", ""
        )
        rate = (hakodate_num / zenkoku_num) if zenkoku_num else 0.0
        print(
            f"[stats] {idx}: reviewer={reviewer_name} "
            f"zenkoku={zenkoku_num} hakodate={hakodate_num}"
        )
        rows.append(
            [
                reviewer_name,
                reviewer_id,
                reviewer_url,
                zenkoku_num,
                hakodate_num,
                rate,
            ]
        )

    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats_df = pd.DataFrame(rows, columns=REVIEWER_STATS_COLUMNS)
    stats_df.to_csv(output_path, index=False)
    print(f"[stats] completed reviewers={len(stats_df)}")
    return len(stats_df)
