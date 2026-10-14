"""Historical numeric evaluation facts from an openly shared community dataset.

These are third-party copies of past official survey aggregates, not live
university data or individual student reviews. Only numeric facts and identifiers
are retained; instructor names and the source course-title text are excluded.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


REFERENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "reference"
EVALUATIONS_PATH = REFERENCE_DIR / "course_evaluations.json"
MANIFEST_PATH = REFERENCE_DIR / "evaluation_manifest.json"
SOURCE_KIND = "third_party_historical_official_evaluations"
ORIGIN_POST = "https://www.reddit.com/r/UofT/comments/1ihe5tu/"
ORIGIN_FOLDER = "https://drive.google.com/drive/folders/1Pg7qk7N2PvKaqMsGjw09El9jsWVmHPEB"
ITEMS_SOURCE = "https://teaching.utoronto.ca/course-evaluations/ce-items/"
COURSE_CODE = re.compile(r"(?<![A-Z0-9])(?:[A-Z]{3}\d{3}[HY][015]|[A-Z]{3}[A-D]\d{2}[HY]3)(?![A-Z0-9])")
SOURCES = (
    {"source_id": "artsci2012_2024", "filename": "artsci.csv", "campus": "St. George",
     "file_id": "1A2yh-XeIeUTrudYHfAHvclj39S_kdlzJ", "responses_field": "Number Responses",
     "overall_field": "INS6", "workload_field": "ARTSC2", "recommendation_field": "ARTSC3"},
    {"source_id": "utm2013_2024", "filename": "mississaugua.csv", "campus": "Mississauga",
     "file_id": "1jnrCY8UjQpvqeswR3xXB-9tE4JIcwSp_", "responses_field": "Number of Survey Responses",
     "overall_field": "Item 6", "workload_field": "Course Workload",
     "recommendation_field": "I would recommend this course"},
    {"source_id": "utsc2014_2024", "filename": "scarborough.csv", "campus": "Scarborough",
     "file_id": "1pGV_LFagFQikou8n0xkumVQ_VyyRTIo7", "responses_field": "Number of Responses",
     "overall_field": "INS6", "workload_field": "UTSC2", "recommendation_field": "UTSC3"},
    {"source_id": "apsc2013_2024", "filename": "fas.csv", "campus": "St. George",
     "origin_faculty": "APSC / Engineering", "course_label_field": "Course Name",
     "file_id": "1wMut9mPuEKMDdS_PXhVvN-94061w2sTe", "responses_field": "Number Responses",
     "overall_field": "INS6", "workload_field": "APSC003", "recommendation_field": None},
)
LIMITATIONS = [
    "Third-party public copy of historical university survey aggregates; not individually revalidated behind UTORid.",
    "2012–2024 historical coverage differs by campus; not a complete current course-evaluation database.",
    "No explicit open redistribution license was found; retained data are numeric facts and provenance only.",
    "Multiple instructor reports may represent the same respondent cohort. Response counts must not be added as unique students.",
    "Response counts describe the source survey report; item-specific respondent counts are not supplied.",
    "Overall learning experience, workload and recommendation are different five-level survey items, not a universal star rating.",
    "Workload is reported historical workload, not course difficulty; missing values are unknown, not zero.",
    "Some historical courses no longer appear in the current catalogue; unmatched records must not be assigned by course name.",
    "Source CSVs contain instructor surnames but no individual student responses or free-text student comments; surnames are excluded here.",
    "Source-derived department and lecture aggregation files are not imported; their zero-filled and response-ratio calculations are not reused.",
    "The Engineering source overlaps the selected undergraduate catalogue for only a small subset of courses; most Engineering records remain unmatched.",
    "Engineering has no matching course-recommendation survey item in this source; recommendation scores remain unknown.",
]


def _source_url(source: dict) -> str:
    return f"https://drive.google.com/file/d/{source['file_id']}/view"


def _score(value: str) -> float | None:
    if not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number) or not 1 <= number <= 5:
        raise ValueError(f"Evaluation score is outside the verified 1–5 scale: {value!r}")
    return number


def _count(value: str) -> int | None:
    if not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError("Evaluation response/invitation counts must be nonnegative integers")
    return int(number)


def _resolve_code(raw_code: str, course_label: str, campus: str, catalogue_keys: set) -> tuple[str, str]:
    raw_code = raw_code.strip()
    if COURSE_CODE.fullmatch(raw_code):
        return (raw_code, "exact_source_code") if (campus, raw_code) in catalogue_keys else ("", "unmatched")
    # Some source rows place a title in Course Code. Require a single full code;
    # never infer by title, prefix, another campus or compressed cross-listings.
    candidates = set(COURSE_CODE.findall(course_label)) | set(COURSE_CODE.findall(raw_code))
    if len(candidates) == 1:
        candidate = next(iter(candidates))
        if (campus, candidate) in catalogue_keys:
            return candidate, "unique_full_code_in_source_label"
    return "", "unmatched"


def normalize_evaluations(
    content: bytes, source: dict, catalogue: list[dict], retrieved_at: str,
) -> tuple[list[dict], dict]:
    """Read a public source CSV without copying names or narrative review text."""
    digest = hashlib.sha256(content).hexdigest()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    label_field = source.get("course_label_field", "Course")
    required = {
        "Course Code", label_field, "Year", "Term", "Number Invited", source["responses_field"],
        source["overall_field"], source["workload_field"], source["recommendation_field"],
    } - {None}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError(f"Evaluation CSV schema changed for {source['source_id']}")
    catalogue_keys = {(row["campus"], row["course_code"]) for row in catalogue}
    records = []
    for source_row_number, raw in enumerate(reader, start=2):
        year, term = int(raw["Year"]), raw["Term"].strip()
        if not 2000 <= year <= 2100 or term not in {"Fall", "Winter", "Summer"}:
            raise ValueError("Invalid historical evaluation year/term")
        code, basis = _resolve_code(raw["Course Code"], raw[label_field], source["campus"], catalogue_keys)
        section_match = re.search(r"\b((?:LEC|TUT|PRA|LAB|SEM)\s*\d+)\s*$", raw[label_field])
        section = re.sub(r"\s+", "", section_match.group(1)) if section_match else ""
        cohort_identity = f"{source['campus']}|{year}|{term}|{raw[label_field].strip()}"
        response_count, invited_count = _count(raw[source["responses_field"]]), _count(raw["Number Invited"])
        quality_flags = []
        if invited_count is None:
            quality_flags.append("invited_count_not_listed")
        if response_count is not None and invited_count is not None and response_count > invited_count:
            quality_flags.append("responses_exceed_invited_in_source")
        if not section:
            quality_flags.append("teaching_section_not_identified")
        records.append({
            "evaluation_id": hashlib.sha256(f"{digest}:{source_row_number}".encode()).hexdigest()[:24],
            "course_code": code, "source_course_code": raw["Course Code"].strip(), "campus": source["campus"],
            "match_status": "matched" if code else "unmatched", "match_basis": basis,
            "year": year, "term": term, "teaching_section": section,
            "cohort_id": hashlib.sha256(cohort_identity.encode()).hexdigest()[:20],
            "overall_score": _score(raw[source["overall_field"]]),
            "workload_score": _score(raw[source["workload_field"]]),
            "recommendation_score": _score(raw[source["recommendation_field"]]) if source["recommendation_field"] else None,
            "response_count": response_count, "invited_count": invited_count,
            "source_id": source["source_id"], "source_row_number": source_row_number,
            "source_url": _source_url(source), "source_retrieved_at": retrieved_at,
            "source_kind": SOURCE_KIND, "quality_flags": quality_flags,
        })
    if not records:
        raise ValueError("Refusing an empty evaluation source")
    cohort_counts = Counter(row["cohort_id"] for row in records)
    for row in records:
        if cohort_counts[row["cohort_id"]] > 1:
            row["quality_flags"].append("multiple_reports_same_cohort")
    metadata = {
        **source, "source_url": _source_url(source),
        "download_url": f"https://drive.google.com/uc?export=download&id={source['file_id']}",
        "sha256": digest, "source_retrieved_at": retrieved_at, "record_count": len(records),
        "year_min": min(row["year"] for row in records), "year_max": max(row["year"] for row in records),
        "year_term_counts": dict(sorted(Counter(f"{row['year']}-{row['term']}" for row in records).items())),
        "matched_record_count": sum(row["match_status"] == "matched" for row in records),
        "matched_current_course_count": len({row["course_code"] for row in records if row["course_code"]}),
        "multiple_report_cohort_count": sum(count > 1 for count in cohort_counts.values()),
        "source_fieldnames": reader.fieldnames,
    }
    return records, metadata


def import_evaluation_sources(directory: Path | str, catalogue: list[dict]) -> tuple[list[dict], dict]:
    directory = Path(directory)
    retrieved_at = datetime.now(ZoneInfo("America/Toronto")).isoformat(timespec="seconds")
    records, sources = [], []
    for source in SOURCES:
        path = directory / source["filename"]
        if not path.exists():
            path = directory / ("evals_" + source["filename"])
        rows, metadata = normalize_evaluations(path.read_bytes(), source, catalogue, retrieved_at)
        records.extend(rows)
        sources.append(metadata)
    manifest = {
        "schema_version": 1, "complete": True, "source_kind": SOURCE_KIND,
        "retrieved_at": retrieved_at, "origin_post_url": ORIGIN_POST, "origin_folder_url": ORIGIN_FOLDER,
        "data_contributor": "Public CSV files shared by Reddit contributor _O-o-f in a student journalist dataset thread",
        "license_status": "No explicit open redistribution license found; only numeric facts and provenance retained",
        "source_verification": "Public files downloaded without login; historical values not independently checked against private official reports",
        "official_items_source_url": ITEMS_SOURCE, "record_count": len(records), "sources": sources,
        "matched_record_count": sum(row["match_status"] == "matched" for row in records),
        "unmatched_record_count": sum(row["match_status"] == "unmatched" for row in records),
        "matched_current_course_count": len({(row["campus"], row["course_code"]) for row in records if row["course_code"]}),
        "metrics": {
            "overall_score": {"scale_min": 1, "scale_max": 5, "meaning": "Historical overall quality of learning experience", "higher_means": "better reported learning experience"},
            "workload_score": {"scale_min": 1, "scale_max": 5, "meaning": "Historical workload compared with other courses", "higher_means": "heavier reported workload, not course difficulty"},
            "recommendation_score": {"scale_min": 1, "scale_max": 5, "meaning": "Historical willingness to recommend the course", "higher_means": "stronger recommendation"},
        },
        "missing_scores": {key: sum(row[key] is None for row in records)
                           for key in ("overall_score", "workload_score", "recommendation_score")},
        "quality_flag_counts": dict(Counter(flag for row in records for flag in row["quality_flags"])),
        "limitations": LIMITATIONS,
    }
    validate_evaluation_snapshot(records, manifest)
    return records, manifest


def fetch_evaluation_sources(directory: Path | str, timeout: float = 60, throttle: float = 0.35) -> None:
    """Explicit public download, used only by the import CLI's --fetch option."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        request = Request(f"https://drive.google.com/uc?export=download&id={source['file_id']}",
                          headers={"User-Agent": "CourseInsight historical evaluation research"})
        with urlopen(request, timeout=timeout) as response:
            content = response.read()
        if content.lstrip().startswith(b"<"):
            raise ValueError("Evaluation download returned HTML instead of a public CSV")
        (directory / source["filename"]).write_bytes(content)
        time.sleep(throttle)


def validate_evaluation_snapshot(records: list[dict], manifest: dict) -> None:
    if not manifest.get("complete") or manifest.get("source_kind") != SOURCE_KIND:
        raise ValueError("Invalid historical evaluation manifest")
    source_index = {row["source_id"]: row for row in manifest.get("sources", [])}
    if set(source_index) != {row["source_id"] for row in SOURCES} or len(manifest["sources"]) != len(SOURCES):
        raise ValueError("Missing or duplicate evaluation sources")
    for expected in SOURCES:
        source = source_index[expected["source_id"]]
        if source.get("file_id") != expected["file_id"] or source.get("campus") != expected["campus"]:
            raise ValueError("Invalid public historical evaluation source identity")
        if source.get("source_url") != _source_url(expected) or not re.fullmatch(r"[a-f0-9]{64}", source.get("sha256", "")):
            raise ValueError("Invalid public historical evaluation source provenance")
        if source.get("source_retrieved_at") != manifest.get("retrieved_at"):
            raise ValueError("Historical evaluation retrieval times do not match")
    counts, seen_ids = Counter(), set()
    for row in records:
        source = source_index.get(row.get("source_id"))
        if source is None or row.get("campus") != source["campus"] or row.get("source_url") != _source_url(source):
            raise ValueError("Invalid evaluation campus or source provenance")
        identity = row.get("evaluation_id")
        expected_id = hashlib.sha256(f"{source['sha256']}:{row.get('source_row_number')}".encode()).hexdigest()[:24]
        if identity != expected_id or identity in seen_ids:
            raise ValueError("Invalid or duplicate historical evaluation identifier")
        seen_ids.add(identity)
        if row.get("source_kind") != SOURCE_KIND or row.get("source_retrieved_at") != source["source_retrieved_at"]:
            raise ValueError("Invalid historical evaluation source metadata")
        if row.get("term") not in {"Fall", "Winter", "Summer"} or type(row.get("year")) is not int or not 2000 <= row["year"] <= 2100:
            raise ValueError("Invalid historical evaluation term")
        if row.get("match_status") not in {"matched", "unmatched"}:
            raise ValueError("Invalid historical evaluation match status")
        if bool(row.get("course_code")) != (row["match_status"] == "matched"):
            raise ValueError("Unmatched evaluations must not be assigned to a current course")
        if row["course_code"] and not COURSE_CODE.fullmatch(row["course_code"]):
            raise ValueError("Historical evaluation match requires a full course code")
        if row["course_code"] and row["course_code"][-1] not in {"St. George": "01", "Mississauga": "5", "Scarborough": "3"}[row["campus"]]:
            raise ValueError("Historical evaluation course code belongs to another campus")
        for key in ("overall_score", "workload_score", "recommendation_score"):
            value = row.get(key)
            if value is not None and (type(value) not in (float, int) or not math.isfinite(value) or not 1 <= value <= 5):
                raise ValueError("Invalid historical evaluation score")
        for key in ("response_count", "invited_count"):
            value = row.get(key)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Invalid historical evaluation response count")
        if any(key in row for key in ("Last Name", "instructor", "instructor_last_name", "Course", "comment", "review_text")):
            raise ValueError("Identifying names and narrative text are excluded from this evaluation snapshot")
        counts[row["source_id"]] += 1
    if len(records) != manifest.get("record_count") or any(counts[key] != source["record_count"] for key, source in source_index.items()):
        raise ValueError("Historical evaluation snapshot/source count mismatch")
    matched = sum(row["match_status"] == "matched" for row in records)
    if matched != manifest.get("matched_record_count") or len(records) - matched != manifest.get("unmatched_record_count"):
        raise ValueError("Historical evaluation match count mismatch")
    current_courses = {(row["campus"], row["course_code"]) for row in records if row["course_code"]}
    if len(current_courses) != manifest.get("matched_current_course_count"):
        raise ValueError("Historical evaluation matched course count mismatch")


def load_evaluation_snapshot() -> tuple[list[dict], dict]:
    present = (EVALUATIONS_PATH.exists(), MANIFEST_PATH.exists())
    if not any(present):
        return [], {"complete": False, "record_count": 0, "sources": []}
    if not all(present):
        raise ValueError("Historical evaluation snapshot and manifest must both be present")
    content = EVALUATIONS_PATH.read_bytes()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("evaluations_sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError("Historical evaluation SHA-256 mismatch")
    records = json.loads(content)
    if not isinstance(records, list):
        raise ValueError("Historical evaluation snapshot must be a JSON array")
    validate_evaluation_snapshot(records, manifest)
    return records, manifest


def write_evaluation_snapshot(records: list[dict], manifest: dict, directory: Path | str = REFERENCE_DIR) -> None:
    validate_evaluation_snapshot(records, manifest)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    content = "[\n" + ",\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in records) + "\n]\n"
    manifest = {**manifest, "evaluations_sha256": hashlib.sha256(content.encode()).hexdigest()}
    outputs = [("course_evaluations.json", content),
               ("evaluation_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")]
    previous = {}
    for name, text in outputs:
        path = directory / name
        previous[name] = path.read_bytes() if path.exists() else None
        (directory / f".{name}.tmp").write_text(text, encoding="utf-8")
    try:
        for name, _ in outputs:
            (directory / f".{name}.tmp").replace(directory / name)
    except OSError:
        for name, original in previous.items():
            path = directory / name
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        raise
    finally:
        for name, _ in outputs:
            (directory / f".{name}.tmp").unlink(missing_ok=True)
