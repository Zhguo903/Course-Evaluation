"""Publish verified course facts, attributed feedback and resource links atomically."""

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
from src.support import (
    REVIEW_COLUMNS,
    RESOURCE_COLUMNS,
    SOURCE_COLUMNS,
    load_support_snapshot,
    validate_support,
)
from src.evaluations import load_evaluation_snapshot


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
    support_snapshot: dict | None = None,
    support_manifest: dict | None = None,
    evaluations: list[dict] | None = None,
    evaluation_manifest: dict | None = None,
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
    if support_snapshot is None:
        support_snapshot, support_manifest = load_support_snapshot()
    else:
        validate_support(support_snapshot, catalogue=courses)
    if evaluations is None or evaluation_manifest is None:
        evaluations, evaluation_manifest = load_evaluation_snapshot()
    catalogue_keys = {(row["campus"], row["course_code"]) for row in courses}
    if default_catalog and any(
        row["course_code"] and (row["campus"], row["course_code"]) not in catalogue_keys
        for row in evaluations
    ):
        raise ValueError("Historical evaluation mapping is stale; re-import against the current catalogue")
    reviews = support_snapshot.get("reviews", [])
    resources = support_snapshot.get("resources", [])
    feedback_sources = support_snapshot.get("feedback_sources", [])
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
    counts = {
        row["course_code"]: {
            "student_review_count": 0,
            "historical_evaluation_count": 0,
            "resource_count": 0,
            "evaluation_year_min": None,
            "evaluation_year_max": None,
        }
        for row in courses
    }
    for records, field in [
        (reviews, "student_review_count"),
        (resources, "resource_count"),
        (evaluations, "historical_evaluation_count"),
    ]:
        for record in records:
            code = record.get("course_code")
            if code not in counts or (record.get("campus"), code) not in catalogue_keys:
                continue
            counts[code][field] += 1
            if field == "historical_evaluation_count":
                year = int(record["year"])
                prior_min, prior_max = (
                    counts[code]["evaluation_year_min"],
                    counts[code]["evaluation_year_max"],
                )
                counts[code]["evaluation_year_min"] = year if prior_min is None else min(year, prior_min)
                counts[code]["evaluation_year_max"] = year if prior_max is None else max(year, prior_max)
    for row in enriched:
        row.update(counts[row["course_code"]])
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
                ("dwd_student_reviews", _frame(reviews, REVIEW_COLUMNS)),
                ("dwd_course_resources", _frame(resources, RESOURCE_COLUMNS)),
                ("ads_feedback_sources", _frame(feedback_sources, SOURCE_COLUMNS)),
                (
                    "dwd_course_evaluations",
                    _frame(evaluations, ["evaluation_id", "campus", "course_code", "year", "term"]),
                ),
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
                            {"source": "support", "manifest": support_manifest or {}},
                            {"source": "historical_evaluations", "manifest": evaluation_manifest},
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
