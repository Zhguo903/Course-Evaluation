"""Integrity checks for official course metadata and offering annotations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pandas as pd

from src.catalog import validate_catalog

SYNTHETIC_FIELDS = {
    "rating",
    "avg_rating",
    "difficulty",
    "avg_difficulty",
    "workload",
    "avg_workload",
    "usefulness",
    "review_text",
    "review_count",
    "gpa_friendly_score",
    "recommend_score",
    "preference_score",
    "confidence",
    "data_career_relevance_score",
}


class DataQualityError(ValueError):
    """An invalid source snapshot must never replace the published database."""


def assert_quality(report: pd.DataFrame) -> None:
    if report.empty or "status" not in report or report.status.ne("PASS").any():
        failures = report.loc[report.status.ne("PASS"), "check_name"].tolist() if "status" in report else []
        raise DataQualityError("Official data validation failed: " + ", ".join(failures))


def run_data_quality_checks(
    courses: list[dict], manifest: dict, catalog_payload: bytes | None = None
) -> pd.DataFrame:
    records = []

    def check(name: str, valid: bool, detail: str = "") -> None:
        records.append(
            {
                "check_name": name,
                "status": "PASS" if valid else "FAIL",
                "detail": detail,
                "check_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    check("catalogue_nonempty", bool(courses), f"{len(courses)} official catalogue records")
    try:
        validate_catalog(courses)
    except (KeyError, TypeError, ValueError) as error:
        check("official_metadata_consistent", False, str(error))
    else:
        check("official_metadata_consistent", True)
    check("no_simulated_rating_fields", not any(SYNTHETIC_FIELDS.intersection(row) for row in courses))
    check(
        "official_provenance",
        bool(courses) and all(row.get("metadata_source") == "official_calendar" for row in courses),
    )
    check("catalogue_manifest_count", manifest.get("course_count") == len(courses))
    declared = manifest.get("campus_coverage", {})
    actual = {
        campus: sum(row.get("campus") == campus for row in courses)
        for campus in ["St. George", "Mississauga", "Scarborough"]
    }
    check("three_campus_counts_match", declared == actual and all(actual.values()), json.dumps(actual))
    check("complete_catalogue_source", manifest.get("complete") is True)
    if catalog_payload is not None:
        check(
            "catalogue_hash_matches",
            manifest.get("catalog_sha256") == hashlib.sha256(catalog_payload).hexdigest(),
        )
    return pd.DataFrame(records)
