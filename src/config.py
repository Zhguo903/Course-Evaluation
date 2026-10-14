"""Paths for the official catalogue and published timetable snapshots."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_DIR = DATA_DIR / "reference"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
DUCKDB_PATH = WAREHOUSE_DIR / "course_insight.duckdb"
CATALOG_PATH = REFERENCE_DIR / "uoft_courses.json"
CATALOG_MANIFEST_PATH = REFERENCE_DIR / "catalog_manifest.json"
TIMETABLE_PATH = REFERENCE_DIR / "timetable_offerings.json"
TIMETABLE_MANIFEST_PATH = REFERENCE_DIR / "timetable_manifest.json"


def ensure_directories() -> None:
    for path in [REFERENCE_DIR, WAREHOUSE_DIR]:
        path.mkdir(parents=True, exist_ok=True)
