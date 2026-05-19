"""ETL cleaning pipeline for CourseInsight raw CSV data."""

from __future__ import annotations

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
    data = {}
    for key, filename in RAW_FILES.items():
        path = RAW_DATA_DIR / filename
        data[key] = read_csv(path)
    return data


def clean_text_value(value: object) -> str:
    """Normalize review text while preserving basic English characters."""
    if pd.isna(value):
        return ""
    text = str(value).lower()
    text = re.sub(r"[^a-z0-9\s.,;:!?'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_courses(courses: pd.DataFrame) -> pd.DataFrame:
    """Clean course fields and remove duplicate course IDs."""
    df = courses.copy()
    df["course_id"] = pd.to_numeric(df["course_id"], errors="coerce").astype("Int64")
    df["course_code"] = df["course_code"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    df["course_name"] = df["course_name"].astype(str).str.strip()
    df["department"] = df["department"].astype(str).str.strip()
    df["course_level"] = pd.to_numeric(df["course_level"], errors="coerce").fillna(0).astype(int)
    df["credit"] = pd.to_numeric(df["credit"], errors="coerce")
    df["prerequisite"] = df["prerequisite"].fillna("").astype(str).str.strip()
    df["campus"] = df["campus"].astype(str).str.strip()
    df = df.dropna(subset=["course_id"]).drop_duplicates(subset=["course_id"])
    return df


def clean_instructors(instructors: pd.DataFrame) -> pd.DataFrame:
    """Clean instructor fields and remove duplicate instructor IDs."""
    df = instructors.copy()
    df["instructor_id"] = pd.to_numeric(df["instructor_id"], errors="coerce").astype("Int64")
    df["instructor_name"] = df["instructor_name"].astype(str).str.strip()
    df["department"] = df["department"].astype(str).str.strip()
    df = df.dropna(subset=["instructor_id"]).drop_duplicates(subset=["instructor_id"])
    return df


def clean_semesters(semesters: pd.DataFrame) -> pd.DataFrame:
    """Clean semester fields and normalize date columns."""
    df = semesters.copy()
    df["semester_id"] = pd.to_numeric(df["semester_id"], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["term"] = df["term"].astype(str).str.strip().str.title()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.date.astype(str)
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce").dt.date.astype(str)
    df = df.dropna(subset=["semester_id"]).drop_duplicates(subset=["semester_id"])
    return df


def clean_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """Clean review ratings, review text, and duplicate review IDs."""
    df = reviews.copy()
    for col in ["review_id", "course_id", "instructor_id", "semester_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["rating", "difficulty", "workload", "usefulness"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=1, upper=5)
    df["review_text"] = df["review_text"].apply(clean_text_value)
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce").dt.date.astype(str)
    df = df.dropna(subset=["review_id", "course_id"]).drop_duplicates(subset=["review_id"])
    return df


def clean_offerings(offerings: pd.DataFrame) -> pd.DataFrame:
    """Clean offering capacity, enrollment, delivery mode, and duplicates."""
    df = offerings.copy()
    for col in ["offering_id", "course_id", "instructor_id", "semester_id", "capacity", "enrolled_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    mode_map = {
        "in person": "In-person",
        "in-person": "In-person",
        "inperson": "In-person",
        "online": "Online",
        "hybrid": "Hybrid",
    }
    normalized = df["delivery_mode"].astype(str).str.strip().str.lower().str.replace("_", " ")
    df["delivery_mode"] = normalized.map(mode_map).fillna("In-person")
    df = df.drop_duplicates(subset=["offering_id"])
    return df


def save_processed_data(data: Dict[str, pd.DataFrame]) -> None:
    """Save cleaned DataFrames to the processed data directory."""
    ensure_directories()
    mapping = {
        "courses": PROCESSED_FILES["courses"],
        "instructors": PROCESSED_FILES["instructors"],
        "semesters": PROCESSED_FILES["semesters"],
        "offerings": PROCESSED_FILES["offerings"],
        "reviews": PROCESSED_FILES["reviews"],
    }
    for key, filename in mapping.items():
        write_csv(data[key], PROCESSED_DATA_DIR / filename)


def run_etl() -> Dict[str, pd.DataFrame]:
    """Run the full raw-to-processed ETL pipeline."""
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
