"""Record-level validation before publishing analytics and recommendations."""

from __future__ import annotations

import json
from urllib.parse import urlparse

from datetime import datetime, timezone
from typing import Dict

import pandas as pd

try:
    from src.catalog import validate_catalog
    from src.config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import log_step, read_csv, write_csv
except ImportError:  # pragma: no cover
    from catalog import validate_catalog
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
    return (
        _column(courses, "course_code")
        .astype("string")
        .str.fullmatch(r"(?:[A-Z]{3}\d{3}(?:[HY][15])?|[A-Z]{3}[A-D]\d{2}[HY]3)", na=False)
    )


def _valid_breadth(value: object) -> bool:
    """BR IDs are metadata, not a claim that the student has fulfilled BR."""
    if isinstance(value, list):
        categories = value
    elif pd.isna(value) or str(value).strip() == "":
        categories = []
    else:
        try:
            categories = json.loads(str(value))
        except (TypeError, ValueError):
            return False
    return (
        isinstance(categories, list)
        and all(type(category) is int and 1 <= category <= 5 for category in categories)
        and len(categories) == len(set(categories))
    )


def _valid_requirement_categories(value: object) -> bool:
    if isinstance(value, list):
        categories = value
    elif pd.isna(value):
        return False
    else:
        try:
            categories = json.loads(str(value))
        except (TypeError, ValueError):
            return False
    return (
        isinstance(categories, list)
        and all(isinstance(category, str) and bool(category.strip()) for category in categories)
        and len(categories) == len(set(categories))
    )


def _empty_categories(value: object) -> bool:
    if isinstance(value, list):
        return value == []
    if pd.isna(value):
        return True
    try:
        return json.loads(str(value)) == []
    except (TypeError, ValueError):
        return False


def _official_source_matches(url: object, code: object) -> bool:
    if pd.isna(url) or pd.isna(code):
        return False
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return False
    source_host = {
        "1": "artsci.calendar.utoronto.ca",
        "5": "utm.calendar.utoronto.ca",
        "3": "utsc.calendar.utoronto.ca",
    }.get(str(code)[-1:])
    return (
        parsed.scheme == "https"
        and parsed.netloc == source_host
        and parsed.path.rstrip("/").lower() == f"/course/{str(code).lower()}"
    )


def _official_metadata_consistent(record: dict) -> bool:
    """Apply the same raw-text/category validation to imports and snapshots."""
    source = record.get("metadata_source")
    if not isinstance(source, str) or source != "official_calendar":
        return True
    normalized = record.copy()
    # CSV readers represent blank optional requirement text as NaN. Restore its
    # empty-string representation without rewriting any nonempty requirement.
    for field in [
        "prerequisite",
        "corequisite",
        "exclusion",
        "recommended_preparation",
        "enrolment_requirements",
        "requirement_notes",
        "breadth_requirements",
        "distribution_requirements",
    ]:
        value = normalized.get(field)
        if pd.api.types.is_scalar(value) and pd.isna(value):
            normalized[field] = ""
    try:
        validate_catalog([normalized])
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return True


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
    add("breadth_categories_valid", "courses", _column(courses, "breadth_categories").map(_valid_breadth))
    official = _column(courses, "metadata_source").eq("official_calendar").fillna(False)
    add(
        "official_metadata_consistent",
        "courses",
        pd.Series(
            [_official_metadata_consistent(record) for record in courses.to_dict("records")],
            index=courses.index,
            dtype=bool,
        ),
    )
    codes = _column(courses, "course_code").astype("string")
    add(
        "official_course_code_format",
        "courses",
        ~official | codes.str.fullmatch(r"(?:[A-Z]{3}[1-4]\d{2}[HY][15]|[A-Z]{3}[A-D]\d{2}[HY]3)", na=False),
    )
    source_matches = pd.Series(
        [_official_source_matches(url, code) for url, code in zip(_column(courses, "source_url"), codes)],
        index=courses.index,
        dtype=bool,
    )
    add("official_course_source_url", "courses", ~official | source_matches)
    retrieved = pd.to_datetime(
        _column(courses, "source_retrieved_at"), format="mixed", errors="coerce", utc=True
    )
    add("official_source_retrieved_at", "courses", ~official | retrieved.notna())
    campus_for_code = codes.str[-1].map({"1": "St. George", "5": "Mississauga", "3": "Scarborough"})
    add("official_course_campus", "courses", ~official | _column(courses, "campus").eq(campus_for_code))
    system_for_code = codes.str[-1].map({"1": "artsci_breadth", "5": "utm_distribution", "3": "utsc_breadth"})
    add(
        "official_requirement_system",
        "courses",
        ~official | _column(courses, "requirement_system").eq(system_for_code),
    )
    add(
        "official_requirement_categories",
        "courses",
        ~official
        | _column(courses, "requirement_categories").map(_valid_requirement_categories).astype(bool),
    )
    sg_or_empty = codes.str[-1].eq("1") | _column(courses, "breadth_categories").map(
        _empty_categories
    ).astype(bool)
    add("official_sg_breadth_categories_only", "courses", ~official | sg_or_empty)
    credits_for_code = codes.str[-2].map({"H": 0.5, "Y": 1.0})
    add(
        "official_course_credit",
        "courses",
        ~official | pd.to_numeric(_column(courses, "credit"), errors="coerce").eq(credits_for_code),
    )
    levels_for_code = codes.str[3].map(
        {"1": 100, "2": 200, "3": 300, "4": 400, "A": 100, "B": 200, "C": 300, "D": 400}
    )
    add(
        "official_course_level",
        "courses",
        ~official | pd.to_numeric(_column(courses, "course_level"), errors="coerce").eq(levels_for_code),
    )
    prerequisite = _column(courses, "prerequisite").astype("string").str.strip().fillna("")
    status = _column(courses, "prerequisite_status")
    consistent_status = (prerequisite.ne("") & status.eq("listed")) | (
        prerequisite.eq("") & status.eq("not_listed")
    )
    add("official_prerequisite_status", "courses", ~official | consistent_status)
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
