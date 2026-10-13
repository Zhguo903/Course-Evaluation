"""Build a validated local CourseInsight warehouse in one command."""

from __future__ import annotations

import argparse

from src.data_quality import assert_quality, main as run_data_quality
from src.etl import run_etl
from src.generate_mock_data import generate_all
from src.nlp_tags import generate_course_tags
from src.utils import log_step
from src.warehouse import build_warehouse


def main(*, generate: bool = True) -> None:
    """Build synthetic inputs by default, or reuse existing raw CSVs explicitly."""
    log_step("Starting CourseInsight pipeline")
    if generate:
        generate_all()
    run_etl()
    report = run_data_quality()
    # Always save the diagnostic report, but never publish invalid detail records.
    assert_quality(report)
    generate_course_tags()
    build_warehouse()
    log_step("Pipeline completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Reuse CSVs in data/raw instead of replacing them with synthetic data.",
    )
    args = parser.parse_args()
    main(generate=not args.skip_generate)
