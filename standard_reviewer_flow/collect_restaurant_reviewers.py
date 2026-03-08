from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper_core.cli import CollectDefaults, run_collect_cli


def main() -> None:
    run_collect_cli(
        CollectDefaults(
            input_csv_path="",
            output_dir="./output",
            sleep_seconds=2.0,
        )
    )


if __name__ == "__main__":
    main()
