"""Publish a pure official-data course finder database atomically."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

from src.catalog import CATALOG_PATH, load_catalog
from src.config import CATALOG_MANIFEST_PATH, DUCKDB_PATH
from src.data_quality import assert_quality, run_data_quality_checks
from src.timetable import annotate_offerings, load_timetable_snapshot


def _frame(records: list[dict], columns: list[str] | None = None) -> pd.DataFrame:
    normalized = [
        {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            for key, value in row.items()
        }
        for row in records
    ]
    return pd.DataFrame(normalized) if normalized else pd.DataFrame(columns=columns or ["empty"])


def build_warehouse(
    *,
    courses: list[dict] | None = None,
    catalog_manifest: dict | None = None,
    offerings: list[dict] | None = None,
    timetable_manifest: dict | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Validate first; failed builds preserve the previous published file."""
    default_catalog = courses is None
    courses = load_catalog() if courses is None else courses
    catalog_manifest = (
        json.loads(CATALOG_MANIFEST_PATH.read_text()) if catalog_manifest is None else catalog_manifest
    )
    quality = run_data_quality_checks(
        courses, catalog_manifest, CATALOG_PATH.read_bytes() if default_catalog else None
    )
    assert_quality(quality)
    if offerings is None or timetable_manifest is None:
        offerings, timetable_manifest = load_timetable_snapshot()
    enriched = annotate_offerings(courses, offerings=offerings, manifest=timetable_manifest)
    coverage = timetable_manifest.get("coverage", [])
    sessions = sorted({str(row["session_code"]) for row in coverage if row.get("session_code")})
    status_maps = {row["course_code"]: {} for row in courses}
    for session in sessions:
        annotated = annotate_offerings(
            courses, offerings=offerings, manifest=timetable_manifest, session=session
        )
        for row in annotated:
            status_maps[row["course_code"]][session] = row["offering_status"]
    for row in enriched:
        row["offering_status_by_session"] = json.dumps(status_maps[row["course_code"]], ensure_ascii=False)
        row["checked_sessions"] = json.dumps(sessions)
        row["timetable_retrieved_at"] = row.get("timetable_checked_at", "")
    destination = Path(db_path or DUCKDB_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".course-finder-", suffix=".duckdb", dir=destination.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        with duckdb.connect(str(temporary)) as conn:
            for name, frame in [
                ("dwd_catalog_courses", _frame(courses)),
                (
                    "dwd_timetable_offerings",
                    _frame(offerings, ["course_code", "session_code", "campus", "status"]),
                ),
                ("ads_course_finder", _frame(enriched)),
                (
                    "ads_timetable_coverage",
                    _frame(coverage, ["campus", "session_code", "label", "complete", "retrieved_at"]),
                ),
                ("ads_data_quality_report", quality),
                (
                    "ads_source_manifests",
                    _frame(
                        [
                            {"source": "catalogue", "manifest": catalog_manifest},
                            {"source": "timetable", "manifest": timetable_manifest},
                        ]
                    ),
                ),
            ]:
                conn.register("source_frame", frame)
                conn.execute(f"CREATE TABLE {name} AS SELECT * FROM source_frame")
                conn.unregister("source_frame")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
        temporary.with_suffix(temporary.suffix + ".wal").unlink(missing_ok=True)
    return quality
