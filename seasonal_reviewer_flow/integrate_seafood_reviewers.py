from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper_core.cli import IntegrateDefaults, run_integrate_cli


def main() -> None:
    run_integrate_cli(
        IntegrateDefaults(
            source_dir="./seasonal_reviewer_flow/output_restaurant_review",
            output_csv_path="./seasonal_reviewer_flow/integrate_reviewer/all_reviewer.csv",
        )
    )


if __name__ == "__main__":
    main()
