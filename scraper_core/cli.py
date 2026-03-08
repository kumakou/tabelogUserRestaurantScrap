import argparse
from dataclasses import dataclass
from typing import Optional

from scraper_core.local_user_rate_pipeline import calculate_local_user_rates
from scraper_core.reviewer_pipeline import collect_reviewer_csvs, integrate_reviewer_csvs
from scraper_core.reviewer_stats_pipeline import collect_reviewer_stats_csv
from scraper_core.visited_store_pipeline import collect_reviewer_visited_store_csvs


@dataclass(frozen=True)
class CollectDefaults:
    input_csv_path: str
    output_dir: str
    sleep_seconds: float = 2.0
    request_timeout: float = 20.0


@dataclass(frozen=True)
class IntegrateDefaults:
    source_dir: str
    output_csv_path: str


@dataclass(frozen=True)
class ReviewerStatsDefaults:
    input_csv_path: Optional[str]
    output_csv_path: str
    sleep_seconds: float = 1.0
    request_timeout: float = 20.0


@dataclass(frozen=True)
class LocalRateDefaults:
    users_info_csv_path: Optional[str]
    store_reviews_dir: str
    output_dir: str
    threshold: float = 0.5


@dataclass(frozen=True)
class VisitedStoreDefaults:
    input_csv_path: Optional[str]
    output_dir: str
    test_mode: bool = False
    begin_page: int = 1
    end_page: int = 60
    sleep_seconds: float = 1.0
    request_timeout: float = 20.0
    start_index: int = 63


def run_collect_cli(defaults: CollectDefaults) -> None:
    parser = argparse.ArgumentParser(
        description="Collect reviewers from store list CSV."
    )
    if defaults.input_csv_path:
        parser.add_argument("--input-csv", default=defaults.input_csv_path)
    else:
        parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", default=defaults.output_dir)
    parser.add_argument("--sleep-seconds", type=float, default=defaults.sleep_seconds)
    parser.add_argument("--request-timeout", type=float, default=defaults.request_timeout)
    parser.add_argument("--max-stores", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    collect_reviewer_csvs(
        input_csv_path=args.input_csv,
        output_dir=args.output_dir,
        sleep_seconds=args.sleep_seconds,
        request_timeout=args.request_timeout,
        max_stores=args.max_stores,
        max_pages=args.max_pages,
    )


def run_integrate_cli(defaults: IntegrateDefaults) -> None:
    parser = argparse.ArgumentParser(description="Integrate reviewer CSV files.")
    parser.add_argument("--source-dir", default=defaults.source_dir)
    parser.add_argument("--output-csv", default=defaults.output_csv_path)
    args = parser.parse_args()

    integrate_reviewer_csvs(
        source_dir=args.source_dir,
        output_csv_path=args.output_csv,
    )


def run_reviewer_stats_cli(defaults: ReviewerStatsDefaults) -> None:
    parser = argparse.ArgumentParser(
        description="Collect reviewer nationwide/local stats."
    )
    if defaults.input_csv_path:
        parser.add_argument("--input-csv", default=defaults.input_csv_path)
    else:
        parser.add_argument("--input-csv", default=None)
    parser.add_argument("--output-csv", default=defaults.output_csv_path)
    parser.add_argument("--sleep-seconds", type=float, default=defaults.sleep_seconds)
    parser.add_argument("--request-timeout", type=float, default=defaults.request_timeout)
    parser.add_argument("--max-reviewers", type=int, default=None)
    args = parser.parse_args()

    collect_reviewer_stats_csv(
        input_csv_path=args.input_csv,
        output_csv_path=args.output_csv,
        sleep_seconds=args.sleep_seconds,
        request_timeout=args.request_timeout,
        max_reviewers=args.max_reviewers,
    )


def run_local_rate_cli(defaults: LocalRateDefaults) -> None:
    parser = argparse.ArgumentParser(
        description="Calculate local user rate per restaurant."
    )
    if defaults.users_info_csv_path:
        parser.add_argument("--users-info-csv", default=defaults.users_info_csv_path)
    else:
        parser.add_argument("--users-info-csv", default=None)
    parser.add_argument("--store-reviews-dir", default=defaults.store_reviews_dir)
    parser.add_argument("--output-dir", default=defaults.output_dir)
    parser.add_argument("--threshold", type=float, default=defaults.threshold)
    args = parser.parse_args()

    calculate_local_user_rates(
        users_info_csv_path=args.users_info_csv,
        store_reviews_dir=args.store_reviews_dir,
        output_dir=args.output_dir,
        threshold=args.threshold,
    )


def run_visited_store_cli(defaults: VisitedStoreDefaults) -> None:
    parser = argparse.ArgumentParser(
        description="Collect visited store detail per reviewer."
    )
    if defaults.input_csv_path:
        parser.add_argument("--input-csv", default=defaults.input_csv_path)
    else:
        parser.add_argument("--input-csv", default=None)
    parser.add_argument("--output-dir", default=defaults.output_dir)
    parser.add_argument("--test-mode", action="store_true", default=defaults.test_mode)
    parser.add_argument("--begin-page", type=int, default=defaults.begin_page)
    parser.add_argument("--end-page", type=int, default=defaults.end_page)
    parser.add_argument("--sleep-seconds", type=float, default=defaults.sleep_seconds)
    parser.add_argument("--request-timeout", type=float, default=defaults.request_timeout)
    parser.add_argument("--max-reviewers", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=defaults.start_index)
    args = parser.parse_args()

    collect_reviewer_visited_store_csvs(
        input_csv_path=args.input_csv,
        output_dir=args.output_dir,
        max_reviewers=args.max_reviewers,
        test_mode=args.test_mode,
        begin_page=args.begin_page,
        end_page=args.end_page,
        sleep_seconds=args.sleep_seconds,
        request_timeout=args.request_timeout,
        start_index=args.start_index,
    )
