from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper_core.cli import IntegrateDefaults, run_integrate_cli


def main() -> None:
    run_integrate_cli(
        IntegrateDefaults(
            source_dir="./output",
            output_csv_path="./output_integrate/all_reviewer.csv",
        )
    )


if __name__ == "__main__":
    main()
