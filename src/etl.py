"""Normalize raw CSVs without disguising invalid records as valid data.

Invalid values remain missing or out of range for the data-quality gate. Duplicate
primary keys keep their first occurrence in file order; missing keys are retained
so the quality report can account for every invalid record.
"""

from __future__ import annotations

import json
import re
from typing import Dict

import pandas as pd

try:
    from src.config import PROCESSED_DATA_DIR, PROCESSED_FILES, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from src.utils import log_step, read_csv, write_csv
except ImportError:  # pragma: no cover
    from config import PROCESSED_DATA_DIR, PROCESSED_FILES, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from utils import log_step, read_csv, write_csv


def load_raw_data() -> Dict[str, pd.DataFrame]:
    """Load all raw CSV files from the raw data directory."""
    ensure_directories()
    return {key: read_csv(RAW_DATA_DIR / filename) for key, filename in RAW_FILES.items()}


def _strings(values: pd.Series) -> pd.Series:
    """Preserve missing values, including common serialized null markers."""
    result = values.astype("string").str.strip()
    return result.mask(result.str.lower().isin(["", "nan", "nat", "none", "null", "<na>"]))


def _integers(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.where(numeric.mod(1).eq(0) & numeric.ge(-(2**63)) & numeric.lt(2**63)).astype("Int64")


def _dates(values: pd.Series) -> pd.Series:
    # Vectorized mixed-format parsing preserves valid ISO variants without a
    # costly per-record parser or a format inferred only from the first row.
    parsed = pd.to_datetime(values, format="mixed", errors="coerce", utc=True)
    return parsed.dt.strftime("%Y-%m-%d").astype("string")


def _deduplicate(df: pd.DataFrame, key: str) -> pd.DataFrame:
    return df.loc[df[key].isna() | ~df[key].duplicated(keep="first")].reset_index(drop=True)


def clean_text_value(value: object) -> str:
    """Normalize English review text; missing values become empty text."""
    if pd.isna(value) or str(value).strip().lower() in {"nan", "nat", "none", "null", "<na>"}:
        return ""
    text = re.sub(r"[^a-z0-9\s.,;:!?'-]", " ", str(value).lower())
    return re.sub(r"\s+", " ", text).strip()


def _breadth_json(value: object) -> str:
    """Serialize native lists; preserve malformed metadata for quality reporting."""
    if isinstance(value, list):
        return json.dumps(value, separators=(",", ":"))
    if pd.isna(value) or str(value).strip().lower() in {"", "nan", "nat", "none", "null", "<na>"}:
        return "[]"
    return str(value).strip()


def clean_courses(courses: pd.DataFrame) -> pd.DataFrame:
    df = courses.copy()
    df["course_id"] = _integers(df["course_id"])
    df["course_code"] = _strings(df["course_code"]).str.upper().str.replace(r"\s+", "", regex=True)
    for column in ["course_name", "department", "campus"]:
        df[column] = _strings(df[column])
    # Official requirement wording carries AND/OR, minimum grades, credits, and
    # permission clauses. Preserve it verbatim apart from surrounding whitespace.
    for column in [
        "prerequisite",
        "corequisite",
        "exclusion",
        "recommended_preparation",
        "enrolment_requirements",
        "breadth_requirements",
        "distribution_requirements",
        "requirement_system",
        "source_url",
        "source_retrieved_at",
        "metadata_source",
        "requirement_notes",
        "prerequisite_status",
    ]:
        source = df[column] if column in df else pd.Series("", index=df.index, dtype="string")
        df[column] = source.astype("string").str.strip().fillna("")
    for column in ["breadth_categories", "requirement_categories"]:
        source = df[column] if column in df else pd.Series("[]", index=df.index)
        df[column] = source.map(_breadth_json)
    df["course_level"] = _integers(df["course_level"])
    df["credit"] = pd.to_numeric(df["credit"], errors="coerce")
    return _deduplicate(df, "course_id")


def clean_instructors(instructors: pd.DataFrame) -> pd.DataFrame:
    df = instructors.copy()
    df["instructor_id"] = _integers(df["instructor_id"])
    for column in ["instructor_name", "department"]:
        df[column] = _strings(df[column])
    return _deduplicate(df, "instructor_id")


def clean_semesters(semesters: pd.DataFrame) -> pd.DataFrame:
    df = semesters.copy()
    for column in ["semester_id", "year"]:
        df[column] = _integers(df[column])
    df["term"] = _strings(df["term"]).str.title()
    for column in ["start_date", "end_date"]:
        df[column] = _dates(df[column])
    return _deduplicate(df, "semester_id")


def clean_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    df = reviews.copy()
    for column in ["review_id", "course_id", "instructor_id", "semester_id"]:
        df[column] = _integers(df[column])
    for column in ["rating", "difficulty", "workload", "usefulness"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["review_text"] = df["review_text"].apply(clean_text_value)
    df["review_date"] = _dates(df["review_date"])
    return _deduplicate(df, "review_id")


def clean_offerings(offerings: pd.DataFrame) -> pd.DataFrame:
    df = offerings.copy()
    for column in ["offering_id", "course_id", "instructor_id", "semester_id", "capacity", "enrolled_count"]:
        df[column] = _integers(df[column])
    mode_map = {
        "in person": "In-person",
        "in-person": "In-person",
        "inperson": "In-person",
        "online": "Online",
        "hybrid": "Hybrid",
    }
    normalized = _strings(df["delivery_mode"]).str.lower().str.replace("_", " ", regex=False)
    df["delivery_mode"] = normalized.map(mode_map).astype("string")
    return _deduplicate(df, "offering_id")


def save_processed_data(data: Dict[str, pd.DataFrame]) -> None:
    ensure_directories()
    for key in RAW_FILES:
        write_csv(data[key], PROCESSED_DATA_DIR / PROCESSED_FILES[key])


def run_etl() -> Dict[str, pd.DataFrame]:
    """Normalize all input tables and persist them for quality validation."""
    log_step("Loading raw CSV files")
    raw = load_raw_data()
    log_step("Cleaning raw tables")
    processed = {
        "courses": clean_courses(raw["courses"]),
        "instructors": clean_instructors(raw["instructors"]),
        "semesters": clean_semesters(raw["semesters"]),
        "offerings": clean_offerings(raw["offerings"]),
        "reviews": clean_reviews(raw["reviews"]),
    }
    save_processed_data(processed)
    log_step(f"Processed data saved to {PROCESSED_DATA_DIR}")
    return processed


if __name__ == "__main__":
    run_etl()
