from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper_core.cli import LocalRateDefaults, run_local_rate_cli


def main() -> None:
    run_local_rate_cli(
        LocalRateDefaults(
            users_info_csv_path="./output_user_info/reviewer_stats.csv",
            store_reviews_dir="./output",
            output_dir="./output_restaurant_local_rate",
            threshold=0.5,
        )
    )


if __name__ == "__main__":
    main()
