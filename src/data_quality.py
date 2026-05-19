"""Data quality checks for CourseInsight processed data."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict, List

import pandas as pd

try:
    from src.config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import log_step, read_csv, write_csv
except ImportError:  # pragma: no cover
    from config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from utils import log_step, read_csv, write_csv


def check_rating_range(reviews: pd.DataFrame, column: str = "rating") -> pd.Series:
    """Return a boolean mask for ratings within the inclusive 1 to 5 range."""
    return pd.to_numeric(reviews[column], errors="coerce").between(1, 5)


def check_course_code_format(courses: pd.DataFrame) -> pd.Series:
    """Return a boolean mask for course codes matching uppercase letters plus three digits."""
    return courses["course_code"].astype(str).str.match(r"^[A-Z]{3}\d{3}$", na=False)


def check_enrollment_capacity(offerings: pd.DataFrame) -> pd.Series:
    """Return a boolean mask for enrolled_count less than or equal to capacity."""
    return pd.to_numeric(offerings["enrolled_count"], errors="coerce") <= pd.to_numeric(
        offerings["capacity"], errors="coerce"
    )


def _build_result(check_name: str, table_name: str, valid_mask: pd.Series, total_count: int) -> dict:
    """Build a standardized data quality result row."""
    failed_count = int((~valid_mask.fillna(False)).sum()) if total_count > 0 else 1
    failure_rate = failed_count / total_count if total_count > 0 else 1.0
    return {
        "check_name": check_name,
        "table_name": table_name,
        "status": "PASS" if failed_count == 0 else "FAIL",
        "failed_count": failed_count,
        "total_count": total_count,
        "failure_rate": round(failure_rate, 4),
        "check_time": datetime.now().isoformat(timespec="seconds"),
    }


def _non_empty_result(table_name: str, df: pd.DataFrame) -> dict:
    """Build a non-empty table check result."""
    valid = pd.Series([len(df) > 0])
    return _build_result("table_row_count_gt_0", table_name, valid, 1)


def load_processed_data() -> Dict[str, pd.DataFrame]:
    """Load processed CSV files required for data quality checks."""
    return {
        "courses": read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["courses"]),
        "instructors": read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["instructors"]),
        "semesters": read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["semesters"]),
        "offerings": read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["offerings"]),
        "reviews": read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["reviews"]),
    }


def run_data_quality_checks(data: Dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Run all configured data quality checks and return a report DataFrame."""
    if data is None:
        data = load_processed_data()

    courses = data["courses"]
    reviews = data["reviews"]
    offerings = data["offerings"]
    results: List[dict] = []

    results.append(
        _build_result("course_id_unique", "courses_clean", ~courses["course_id"].duplicated(), len(courses))
    )
    results.append(
        _build_result("review_id_unique", "reviews_clean", ~reviews["review_id"].duplicated(), len(reviews))
    )
    results.append(
        _build_result("course_code_not_null", "courses_clean", courses["course_code"].notna(), len(courses))
    )
    results.append(
        _build_result(
            "review_text_not_null",
            "reviews_clean",
            reviews["review_text"].notna() & (reviews["review_text"].astype(str).str.len() > 0),
            len(reviews),
        )
    )
    for column in ["rating", "difficulty", "workload"]:
        results.append(_build_result(f"{column}_between_1_and_5", "reviews_clean", check_rating_range(reviews, column), len(reviews)))
    results.append(
        _build_result("course_code_format", "courses_clean", check_course_code_format(courses), len(courses))
    )
    results.append(
        _build_result(
            "enrolled_count_lte_capacity",
            "course_offerings_clean",
            check_enrollment_capacity(offerings),
            len(offerings),
        )
    )
    for table_name, df in data.items():
        results.append(_non_empty_result(f"{table_name}_clean", df))

    return pd.DataFrame(results)


def save_data_quality_report(report: pd.DataFrame) -> None:
    """Save the data quality report to processed data."""
    output_path = PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"]
    write_csv(report, output_path)
    log_step(f"Data quality report saved to {output_path}")


def main() -> pd.DataFrame:
    """Run and persist the data quality report."""
    log_step("Running data quality checks")
    report = run_data_quality_checks()
    save_data_quality_report(report)
    return report


if __name__ == "__main__":
    main()
