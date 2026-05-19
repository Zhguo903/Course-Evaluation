"""Centralized project paths and constants."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
SQL_DIR = PROJECT_ROOT / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"
APP_DIR = PROJECT_ROOT / "app"

DUCKDB_PATH = WAREHOUSE_DIR / "course_insight.duckdb"

DEPARTMENTS = [
    "Statistics",
    "Computer Science",
    "Data Science",
    "Economics",
    "Mathematics",
    "Biology",
    "Psychology",
    "Business",
]

RAW_FILES = {
    "courses": "courses_raw.csv",
    "instructors": "instructors_raw.csv",
    "semesters": "semesters_raw.csv",
    "offerings": "course_offerings_raw.csv",
    "reviews": "reviews_raw.csv",
}

PROCESSED_FILES = {
    "courses": "courses_clean.csv",
    "instructors": "instructors_clean.csv",
    "semesters": "semesters_clean.csv",
    "offerings": "course_offerings_clean.csv",
    "reviews": "reviews_clean.csv",
    "course_tags": "course_tags.csv",
    "data_quality": "data_quality_report.csv",
}


def ensure_directories() -> None:
    """Create required project data directories if they do not exist."""
    for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, WAREHOUSE_DIR]:
        path.mkdir(parents=True, exist_ok=True)
