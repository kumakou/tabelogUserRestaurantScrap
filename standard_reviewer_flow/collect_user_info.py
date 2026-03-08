from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper_core.cli import ReviewerStatsDefaults, run_reviewer_stats_cli


def main() -> None:
    run_reviewer_stats_cli(
        ReviewerStatsDefaults(
            input_csv_path="./output_integrate/all_reviewer.csv",
            output_csv_path="./output_user_info/reviewer_stats.csv",
            sleep_seconds=1.0,
            request_timeout=20.0,
        )
    )


if __name__ == "__main__":
    main()
