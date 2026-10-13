"""Record-level validation before publishing analytics and recommendations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import pandas as pd

try:
    from src.config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import log_step, read_csv, write_csv
except ImportError:  # pragma: no cover
    from config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from utils import log_step, read_csv, write_csv


class DataQualityError(ValueError):
    """Raised when processed data fails the publication quality gate."""


def assert_quality(report: pd.DataFrame) -> None:
    """Reject a missing report or any failed check before building the warehouse."""
    if report.empty or "status" not in report or report["status"].ne("PASS").any():
        failed = (
            report.loc[report["status"].ne("PASS"), "check_name"].tolist()
            if {"status", "check_name"}.issubset(report.columns)
            else []
        )
        raise DataQualityError(
            "Data quality gate failed: " + (", ".join(failed) or "empty or invalid report")
        )


def _column(df: pd.DataFrame, column: str) -> pd.Series:
    return df[column] if column in df else pd.Series(pd.NA, index=df.index, dtype="object")


def _text_present(values: pd.Series) -> pd.Series:
    text = values.astype("string").str.strip()
    return text.notna() & ~text.str.lower().isin(["", "nan", "nat", "none", "null", "<na>"])


def _positive_integer(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.gt(0) & numeric.mod(1).eq(0)


def check_rating_range(reviews: pd.DataFrame, column: str = "rating") -> pd.Series:
    return pd.to_numeric(_column(reviews, column), errors="coerce").between(1, 5).fillna(False)


def check_course_code_format(courses: pd.DataFrame) -> pd.Series:
    return _column(courses, "course_code").astype("string").str.fullmatch(r"[A-Z]{3}\d{3}", na=False)


def check_enrollment_capacity(offerings: pd.DataFrame) -> pd.Series:
    enrolled = pd.to_numeric(_column(offerings, "enrolled_count"), errors="coerce")
    capacity = pd.to_numeric(_column(offerings, "capacity"), errors="coerce")
    return (
        capacity.gt(0)
        & capacity.mod(1).eq(0)
        & enrolled.ge(0)
        & enrolled.mod(1).eq(0)
        & enrolled.le(capacity)
    ).fillna(False)


def _build_result(check_name: str, table_name: str, valid_mask: pd.Series, total_count: int) -> dict:
    """Empty record checks have zero failures; table presence is checked separately."""
    failed_count = int((~valid_mask.fillna(False).astype(bool)).sum())
    return {
        "check_name": check_name,
        "table_name": table_name,
        "status": "PASS" if failed_count == 0 else "FAIL",
        "failed_count": failed_count,
        "total_count": total_count,
        "failure_rate": round(failed_count / total_count, 4) if total_count else 0.0,
        "check_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _non_empty_result(table_name: str, df: pd.DataFrame) -> dict:
    result = _build_result(
        "table_row_count_gt_0", table_name, pd.Series(True, index=df.index, dtype=bool), len(df)
    )
    result["status"] = "PASS" if len(df) else "FAIL"
    return result


def load_processed_data() -> Dict[str, pd.DataFrame]:
    return {
        key: read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES[key])
        for key in ["courses", "instructors", "semesters", "offerings", "reviews"]
    }


def run_data_quality_checks(data: Dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Validate required values, IDs, dates, ranges, references, and review context."""
    if data is None:
        data = load_processed_data()
    data = {
        key: data.get(key, pd.DataFrame())
        for key in ["courses", "instructors", "semesters", "offerings", "reviews"]
    }
    results = []

    def add(name: str, table: str, mask: pd.Series) -> None:
        results.append(_build_result(name, f"{table}_clean", mask, len(data[table])))

    keys = {
        "courses": "course_id",
        "instructors": "instructor_id",
        "semesters": "semester_id",
        "offerings": "offering_id",
        "reviews": "review_id",
    }
    required_text = {
        "courses": ["course_code", "course_name", "department", "campus"],
        "instructors": ["instructor_name", "department"],
        "semesters": ["term"],
        "offerings": ["delivery_mode"],
        "reviews": ["review_text"],
    }
    for table, key in keys.items():
        df = data[table]
        values = _column(df, key)
        add(f"{key}_valid", table, _positive_integer(values))
        add(f"{key}_unique", table, values.notna() & ~values.duplicated(keep=False))
        for column in required_text[table]:
            add(f"{column}_not_null", table, _text_present(_column(df, column)))
        results.append(_non_empty_result(f"{table}_clean", df))

    courses, semesters, offerings, reviews = (
        data[key] for key in ["courses", "semesters", "offerings", "reviews"]
    )
    add("course_code_format", "courses", check_course_code_format(courses))
    add("course_code_unique", "courses", ~_column(courses, "course_code").duplicated(keep=False))
    add(
        "course_level_valid",
        "courses",
        pd.to_numeric(_column(courses, "course_level"), errors="coerce").isin([100, 200, 300, 400]),
    )
    credits = pd.to_numeric(_column(courses, "credit"), errors="coerce")
    add("credit_valid", "courses", credits.gt(0) & credits.lt(float("inf")))
    for column in ["rating", "difficulty", "workload", "usefulness"]:
        add(f"{column}_between_1_and_5", "reviews", check_rating_range(reviews, column))
    add("enrolled_count_lte_capacity", "offerings", check_enrollment_capacity(offerings))
    add(
        "delivery_mode_valid",
        "offerings",
        _column(offerings, "delivery_mode").isin(["In-person", "Online", "Hybrid"]),
    )
    add("term_valid", "semesters", _column(semesters, "term").isin(["Spring", "Summer", "Fall", "Winter"]))

    dates = {}
    for table, columns in {"semesters": ["start_date", "end_date"], "reviews": ["review_date"]}.items():
        for column in columns:
            parsed = pd.to_datetime(_column(data[table], column), errors="coerce", utc=True)
            dates[column] = parsed
            add(f"{column}_valid", table, parsed.notna())
    add("semester_date_order", "semesters", dates["start_date"].le(dates["end_date"]))
    add(
        "semester_year_matches",
        "semesters",
        dates["start_date"].dt.year.eq(pd.to_numeric(_column(semesters, "year"), errors="coerce")),
    )

    for table in ["offerings", "reviews"]:
        for dimension, key in [
            ("courses", "course_id"),
            ("instructors", "instructor_id"),
            ("semesters", "semester_id"),
        ]:
            values = _column(data[table], key)
            add(
                f"{key}_references_{dimension}",
                table,
                _positive_integer(values) & values.isin(_column(data[dimension], key).dropna()),
            )

    context = ["course_id", "instructor_id", "semester_id"]
    offering_keys = set(zip(*[_column(offerings, key) for key in context]))
    matched = pd.Series(
        [key in offering_keys for key in zip(*[_column(reviews, key) for key in context])],
        index=reviews.index,
        dtype=bool,
    )
    matched &= pd.concat([_column(reviews, key).notna() for key in context], axis=1).all(axis=1)
    add("review_matches_offering", "reviews", matched)
    # Only unique semester IDs are safe lookup keys; duplicates already fail above.
    semester_bounds = (
        pd.DataFrame(
            {
                "semester_id": _column(semesters, "semester_id"),
                "start": dates["start_date"],
                "end": dates["end_date"],
            }
        )
        .dropna(subset=["semester_id"])
        .drop_duplicates("semester_id")
        .set_index("semester_id")
    )
    review_semesters = _column(reviews, "semester_id")
    starts = pd.to_datetime(
        review_semesters.map(semester_bounds["start"].to_dict()), errors="coerce", utc=True
    )
    ends = pd.to_datetime(review_semesters.map(semester_bounds["end"].to_dict()), errors="coerce", utc=True)
    add(
        "review_date_within_semester",
        "reviews",
        dates["review_date"].ge(starts) & dates["review_date"].le(ends),
    )
    return pd.DataFrame(results)


def save_data_quality_report(report: pd.DataFrame) -> None:
    output_path = PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"]
    write_csv(report, output_path)
    log_step(f"Data quality report saved to {output_path}")


def main() -> pd.DataFrame:
    log_step("Running data quality checks")
    report = run_data_quality_checks()
    save_data_quality_report(report)
    return report


if __name__ == "__main__":
    main()
