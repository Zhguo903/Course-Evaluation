"""Validate curated public student feedback and links, without generating content."""

from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
import json
import math
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from src.catalog import load_catalog
from src.config import REFERENCE_DIR

SUPPORT_FILES = {
    "reviews": "student_reviews.json",
    "resources": "course_resources.json",
    "feedback_sources": "feedback_sources.json",
}
REVIEW_COLUMNS = [
    "review_id",
    "course_code",
    "campus",
    "source_id",
    "source_url",
    "source_title",
    "source_kind",
    "reviewer_label",
    "academic_period",
    "published_at",
    "retrieved_at",
    "rating",
    "rating_scale_min",
    "rating_scale_max",
    "rating_dimension",
    "summary",
    "verification_level",
    "limitations",
    "code_mapping",
    "source_course_code",
]
RESOURCE_COLUMNS = [
    "resource_id",
    "course_code",
    "campus",
    "title",
    "resource_type",
    "url",
    "provider",
    "source_kind",
    "academic_period",
    "access_requirement",
    "rights_note",
    "verified_at",
    "source_url",
    "limitations",
]
SOURCE_COLUMNS = [
    "source_id",
    "title",
    "source_type",
    "status",
    "access",
    "covered_period",
    "source_url",
    "limitations",
]


def safe_public_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def _date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid support retrieval date: {value!r}") from error


def validate_support(records: dict, catalogue: list[dict] | None = None) -> None:
    catalogue = load_catalog() if catalogue is None else catalogue
    course_campuses = {row["course_code"]: row["campus"] for row in catalogue}
    campuses = set(course_campuses.values())
    sources = records.get("feedback_sources", [])
    source_ids = set()
    source_index = {}
    for source in sources:
        if not set(SOURCE_COLUMNS).issubset(source):
            raise ValueError("Feedback source fields are incomplete")
        identity = source["source_id"]
        if not identity or identity in source_ids or not safe_public_url(source["source_url"]):
            raise ValueError("Invalid or duplicate feedback source")
        if source["status"] not in {"imported", "external_link", "login_required", "licence_required"}:
            raise ValueError("Unknown feedback source status")
        if source["access"] not in {"public", "utorid_required", "mixed", "restricted"}:
            raise ValueError("Unknown feedback source access")
        source_ids.add(identity)
        source_index[identity] = source
    for key, columns, identity_field in [
        ("reviews", REVIEW_COLUMNS, "review_id"),
        ("resources", RESOURCE_COLUMNS, "resource_id"),
    ]:
        identities = set()
        for row in records.get(key, []):
            if not set(columns).issubset(row):
                raise ValueError(f"{key} fields are incomplete")
            identity = row[identity_field]
            if not identity or identity in identities:
                raise ValueError(f"Duplicate or missing {key} identity")
            identities.add(identity)
            code, campus = row["course_code"], row["campus"]
            if code:
                if course_campuses.get(code) != campus:
                    raise ValueError(f"Support course/campus mismatch: {code}")
            elif key == "reviews" or campus not in campuses | {"All"}:
                raise ValueError("A review must link to a verified catalogue course")
            if not safe_public_url(row["source_url"]):
                raise ValueError("Support source requires a public HTTPS URL")
            if key == "reviews":
                _date(row["retrieved_at"])
                if row["source_id"] not in source_ids:
                    raise ValueError("Review source is not registered")
                if (
                    source_index[row["source_id"]]["status"] != "imported"
                    or source_index[row["source_id"]]["source_type"] != "student_review_collection"
                ):
                    raise ValueError("A link-only source cannot be represented as imported student reviews")
                if row["published_at"]:
                    _date(row["published_at"])
                if (
                    row["source_kind"] != "student_review"
                    or row["verification_level"] != "public_self_report"
                ):
                    raise ValueError(
                        "Unverified source kind cannot be presented as a verified student identity"
                    )
                if not row["summary"] or not row["limitations"] or not row["code_mapping"]:
                    raise ValueError("Review requires attribution, limitations and course mapping")
                rating_values = [row[name] for name in ["rating", "rating_scale_min", "rating_scale_max"]]
                if all(value is None for value in rating_values):
                    continue
                if any(
                    type(value) not in {int, float} or not math.isfinite(value) for value in rating_values
                ):
                    raise ValueError("Review rating must be numeric or explicitly missing")
                rating, lower, upper = rating_values
                if not lower < upper or not lower <= rating <= upper or not row["rating_dimension"]:
                    raise ValueError("Review rating scale or dimension is invalid")
            else:
                _date(row["verified_at"])
                if not safe_public_url(row["url"]):
                    raise ValueError("Resource requires a public HTTPS URL")
                if row["access_requirement"] not in {"public", "utorid_required", "mixed"}:
                    raise ValueError("Resource access must be explicit")
                if row["source_kind"] not in {
                    "official",
                    "student_organization",
                    "open_textbook",
                    "third_party",
                }:
                    raise ValueError("Resource provenance must be explicit")
                if not row["rights_note"] or not row["title"]:
                    raise ValueError("Resource title and link-only rights note are required")


def write_support_manifest(directory: str | Path = REFERENCE_DIR) -> dict:
    """Record checksums only after the deliberately curated metadata validates."""
    directory = Path(directory)
    records = {key: json.loads((directory / name).read_text()) for key, name in SUPPORT_FILES.items()}
    validate_support(records)
    manifest = {
        "schema_version": 1,
        "verified_at": datetime.now(ZoneInfo("America/Toronto")).date().isoformat(),
        "files": {
            key: {
                "file": name,
                "count": len(records[key]),
                "sha256": sha256((directory / name).read_bytes()).hexdigest(),
            }
            for key, name in SUPPORT_FILES.items()
        },
        "review_policy": "Public self-reported individual opinions. Student identity is not verified. No averaging or quality ranking.",
        "resource_policy": "Verified metadata and original links only; no redistributed course materials or exam contents.",
    }
    (directory / "support_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest


def load_support_snapshot(directory: str | Path = REFERENCE_DIR) -> tuple[dict, dict]:
    directory = Path(directory)
    paths = [directory / name for name in SUPPORT_FILES.values()] + [directory / "support_manifest.json"]
    if not any(path.exists() for path in paths):
        return {key: [] for key in SUPPORT_FILES}, {}
    if not all(path.exists() for path in paths):
        raise ValueError("Support records and manifest must all be present")
    manifest = json.loads(paths[-1].read_text())
    records = {}
    for key, name in SUPPORT_FILES.items():
        payload = (directory / name).read_bytes()
        values = json.loads(payload)
        expected = manifest.get("files", {}).get(key, {})
        if (
            not isinstance(values, list)
            or expected.get("file") != name
            or expected.get("count") != len(values)
        ):
            raise ValueError("Support manifest counts or file names do not match")
        if expected.get("sha256") != sha256(payload).hexdigest():
            raise ValueError("Support snapshot hash mismatch")
        records[key] = values
    validate_support(records)
    return records, manifest
