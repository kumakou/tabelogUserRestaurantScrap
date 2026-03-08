from pathlib import Path
from typing import Optional

import pandas as pd

from scraper_core.reviewer_pipeline import normalize_reviewer_columns

LOCAL_RATE_SUMMARY_COLUMNS = ["store_name", "local_user", "zenkoku_user", "rate"]
LOCAL_RATE_DETAIL_COLUMNS = [
    "store_name",
    "reviewer_name",
    "reviewer_url",
    "zenkoku_num",
    "hakodate_num",
    "rate",
]


def _resolve_users_info_path(users_info_csv_path: Optional[str]) -> Path:
    if users_info_csv_path:
        return Path(users_info_csv_path)

    default_candidates = [
        Path("./output_user_info/total_userinfo.csv"),
        Path("./output_user_info/userinfo17.csv"),
    ]
    for candidate in default_candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("users info csv not found in output_user_info")


def calculate_local_user_rates(
    users_info_csv_path: Optional[str],
    store_reviews_dir: str,
    output_dir: str,
    threshold: float = 0.5,
) -> int:
    users_info_path = _resolve_users_info_path(users_info_csv_path)
    users_df = pd.read_csv(users_info_path).fillna("")
    users_df = normalize_reviewer_columns(users_df)
    users_df = users_df.reindex(
        columns=["reviewer_name", "reviewer_url", "zenkoku_num", "hakodate_num", "rate"],
        fill_value="",
    )

    store_reviews_path = Path(store_reviews_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for csv_path in sorted(store_reviews_path.glob("*.csv")):
        store_df = pd.read_csv(csv_path).fillna("")
        store_df = normalize_reviewer_columns(store_df)
        if "store_name" not in store_df.columns or store_df.empty:
            continue

        store_name = str(store_df["store_name"].iloc[0])
        local_user = 0
        zenkoku_user = 0
        detail_rows = []

        for reviewer in store_df.itertuples(index=False):
            reviewer_name = str(getattr(reviewer, "reviewer_name", "")).strip()
            reviewer_url = str(getattr(reviewer, "reviewer_url", "")).strip()
            zenkoku_num = 0
            hakodate_num = 0
            rate = 0.0

            if reviewer_url:
                matched = users_df[users_df["reviewer_url"] == reviewer_url]
                if not matched.empty:
                    zenkoku_num = float(matched["zenkoku_num"].iloc[0])
                    hakodate_num = float(matched["hakodate_num"].iloc[0])
                    rate = float(matched["rate"].iloc[0])
                    if rate > threshold:
                        local_user += 1
                    else:
                        zenkoku_user += 1

            detail_rows.append(
                [store_name, reviewer_name, reviewer_url, zenkoku_num, hakodate_num, rate]
            )

        local_user_rate = (
            local_user / zenkoku_user if (local_user and zenkoku_user) else 0.0
        )
        summary_rows.append([store_name, local_user, zenkoku_user, local_user_rate])

        detail_df = pd.DataFrame(detail_rows, columns=LOCAL_RATE_DETAIL_COLUMNS)
        detail_df.to_csv(
            output_path / f"{store_name.replace('/', '')}.csv",
            index=False,
        )

    summary_df = pd.DataFrame(summary_rows, columns=LOCAL_RATE_SUMMARY_COLUMNS)
    summary_df.to_csv(output_path / "local_rate.csv", index=False)
    print(f"[local-rate] completed stores={len(summary_df)}")
    return len(summary_df)
