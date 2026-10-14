"""Public, verifiable U of T Timetable Builder offerings.

The calendars describe courses; this snapshot describes published offerings.
``not_found`` means absent from a completely retrieved published timetable, not
that the course will never run. Closed enrolment still counts as an offering.
Full-year courses are included when looking up either of their constituent terms.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


API_BASE = "https://api.easi.utoronto.ca/ttb"
TTB_URL = "https://ttb.utoronto.ca/"
REFERENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "reference"
OFFERINGS_PATH = REFERENCE_DIR / "timetable_offerings.json"
MANIFEST_PATH = REFERENCE_DIR / "timetable_manifest.json"
DIVISION_CAMPUSES = {"ARTSC": "St. George", "ERIN": "Mississauga", "SCAR": "Scarborough"}
STATUSES = {"offered", "cancelled", "not_found", "unknown"}


def load_timetable(path: Path | str | None = None) -> list[dict]:
    """Load the checked-in offering snapshot, without making network calls."""
    target = Path(path) if path is not None else OFFERINGS_PATH
    if not target.exists():
        return []
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Timetable snapshot must be a list")
    return value


def load_timetable_manifest(path: Path | str | None = None) -> dict:
    target = Path(path) if path is not None else MANIFEST_PATH
    if not target.exists():
        return {"coverage": [], "sessions": []}
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Timetable manifest must be an object")
    return value


def load_timetable_snapshot() -> tuple[list[dict], dict]:
    """Load a verified pair; incomplete/tampered files cannot prove absence."""
    present = (OFFERINGS_PATH.exists(), MANIFEST_PATH.exists())
    if not any(present):
        return [], {"coverage": [], "sessions": [], "complete": False}
    if not all(present):
        raise ValueError("Incomplete timetable snapshot: offering and manifest files must both be present")
    offerings, manifest = load_timetable(), load_timetable_manifest()
    actual_hash = sha256(OFFERINGS_PATH.read_bytes()).hexdigest()
    if not manifest.get("offerings_sha256") or manifest["offerings_sha256"] != actual_hash:
        raise ValueError("Timetable snapshot SHA-256 mismatch; refresh the verified file pair")
    validate_timetable_snapshot(offerings, manifest)
    return offerings, manifest


def validate_timetable_snapshot(offerings: list[dict], manifest: dict) -> None:
    """Verify identity, provenance and all counts before trusting completeness."""
    if manifest.get("api_base") != API_BASE or manifest.get("reference_url") != API_BASE + "/reference-data":
        raise ValueError("Invalid official timetable manifest provenance")
    try:
        retrieved_at = datetime.fromisoformat(manifest.get("retrieved_at", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid timetable retrieval time") from exc
    if retrieved_at.tzinfo is None:
        raise ValueError("Timetable retrieval time must include its timezone")
    sessions = manifest.get("sessions", [])
    session_codes = [row.get("session_code") for row in sessions]
    if not sessions or any(not code for code in session_codes) or len(set(session_codes)) != len(session_codes):
        raise ValueError("Invalid or duplicate published timetable sessions")
    seen_ids = set()
    seen_courses = set()
    counts = Counter()
    for row in offerings:
        division = row.get("division")
        if division not in DIVISION_CAMPUSES or row.get("campus") != DIVISION_CAMPUSES[division]:
            raise ValueError("Invalid timetable campus/division identity")
        identity = row.get("timetable_id")
        key = (row.get("campus"), row.get("course_code"), row.get("session_code"))
        if not identity or not row.get("course_code") or identity in seen_ids or key in seen_courses:
            raise ValueError("Missing or duplicate timetable offering identifier")
        seen_ids.add(identity)
        seen_courses.add(key)
        if row.get("status") not in {"offered", "cancelled"}:
            raise ValueError("Invalid timetable offering status")
        if row.get("session_code") not in session_codes:
            raise ValueError("Offering references an unpublished timetable session")
        if "-".join(sorted(set(row.get("sessions") or []))) != row["session_code"]:
            raise ValueError("Offering session components do not match its published session")
        source = urlparse(row.get("source_url", ""))
        if (
            source.scheme != "https" or source.hostname != "api.easi.utoronto.ca"
            or source.path != "/ttb/findById" or parse_qs(source.query).get("id") != [identity]
        ):
            raise ValueError("Invalid official timetable source provenance")
        if not row.get("source_retrieved_at") or row["source_retrieved_at"] != manifest.get("retrieved_at"):
            raise ValueError("Timetable offering and manifest retrieval times do not match")
        counts[(division, row["session_code"])] += 1
    coverage = manifest.get("coverage", [])
    coverage_keys = []
    for row in coverage:
        division, session_code = row.get("division"), row.get("session_code")
        key = (division, session_code)
        if division not in DIVISION_CAMPUSES or row.get("campus") != DIVISION_CAMPUSES[division]:
            raise ValueError("Invalid timetable coverage campus/division identity")
        if session_code not in session_codes or key in coverage_keys:
            raise ValueError("Invalid or duplicate timetable session coverage")
        coverage_keys.append(key)
        if not isinstance(row.get("complete"), bool):
            raise ValueError("Timetable completeness must be explicit")
        if row.get("retrieved_at") != manifest.get("retrieved_at"):
            raise ValueError("Timetable coverage and manifest retrieval times do not match")
        if row.get("source_url") != API_BASE + "/getCourses" or row.get("count_source_url") != API_BASE + "/getPageableCourses":
            raise ValueError("Invalid official timetable count provenance")
        if row.get("offering_count") != counts[key] or row.get("official_total") != counts[key]:
            raise ValueError("Timetable session counts do not match the verified snapshot")
    expected_keys = {(division, code) for division in DIVISION_CAMPUSES for code in session_codes}
    if manifest.get("complete") is True and (
        set(coverage_keys) != expected_keys or not all(row["complete"] for row in coverage)
    ):
        raise ValueError("A complete timetable manifest must cover every published campus/session pair")
    if manifest.get("offering_count") != len(offerings):
        raise ValueError("Timetable overall offering count mismatch")
    if manifest.get("unique_course_count") != len({(row["campus"], row["course_code"]) for row in offerings}):
        raise ValueError("Timetable unique course count mismatch")
    if manifest.get("status_counts") != dict(Counter(row["status"] for row in offerings)):
        raise ValueError("Timetable status counts do not match the snapshot")
    totals = manifest.get("division_totals", [])
    if {row.get("division") for row in totals} != set(DIVISION_CAMPUSES) or len(totals) != len(DIVISION_CAMPUSES):
        raise ValueError("Timetable division totals are missing or duplicated")
    for row in totals:
        if row.get("campus") != DIVISION_CAMPUSES[row["division"]] or row.get("official_total") != sum(
            value for (division, _), value in counts.items() if division == row["division"]
        ):
            raise ValueError("Timetable division counts do not match the snapshot")


def _session_code(course: dict) -> str:
    sessions = sorted(set(course.get("sessions") or []))
    if not sessions:
        raise ValueError(f"Course {course.get('code')} has no published session")
    return "-".join(sessions)


def normalize_offering(course: dict, division: str, retrieved_at: str) -> dict:
    """Keep public course/section provenance, excluding volatile seat counts."""
    if division not in DIVISION_CAMPUSES or course.get("faculty", {}).get("code") != division:
        raise ValueError("Unexpected timetable faculty")
    course_code = str(course.get("code") or "")
    if not course_code or not course.get("id"):
        raise ValueError("Timetable course is missing its identifier")
    sections = course.get("sections") or []
    primary_method = course.get("primaryTeachMethod")
    primary_sections = [item for item in sections if item.get("teachMethod") == primary_method]
    relevant_sections = primary_sections or sections
    cancelled = course.get("cancelInd") == "Y" or (
        bool(relevant_sections) and all(item.get("cancelInd") == "Y" for item in relevant_sections)
    )
    status = "cancelled" if cancelled else "offered"
    normalized_sections = []
    for section in sections:
        normalized_sections.append(
            {
                "name": section.get("name") or "",
                "type": section.get("type") or "",
                "status": "cancelled" if section.get("cancelInd") == "Y" else "offered",
                "enrolment_closed": section.get("openLimitInd") == "C",
                "delivery_modes": section.get("deliveryModes") or [],
            }
        )
    return {
        "course_code": course_code,
        "timetable_id": course["id"],
        "title": course.get("name") or "",
        "campus": DIVISION_CAMPUSES[division],
        "division": division,
        "session_code": _session_code(course),
        "sessions": sorted(set(course["sessions"])),
        "term_code": course.get("sectionCode") or "",
        "status": status,
        "sections": normalized_sections,
        "source_url": f"{API_BASE}/findById?id={course['id']}",
        "timetable_url": TTB_URL,
        "source_retrieved_at": retrieved_at,
        "source_created_at": course.get("created"),
        "source_modified_at": course.get("modified"),
    }


def _matches_session(offering: dict, session: str | None) -> bool:
    if session is None:
        return True
    return offering["session_code"] == session or (
        "-" not in session and session in offering.get("sessions", [])
    )


def _relevant_coverage(manifest: dict, campus: str, session: str | None) -> list[dict]:
    coverage = [row for row in manifest.get("coverage", []) if row.get("campus") == campus]
    if session is None:
        return coverage
    return [
        row for row in coverage
        if row.get("session_code") == session
        or ("-" not in session and session in str(row.get("session_code", "")).split("-"))
    ]


def annotate_offerings(
    courses: list[dict],
    offerings: list[dict] | None = None,
    manifest: dict | None = None,
    session: str | None = None,
) -> list[dict]:
    """Add honest offering labels; no absence inference after incomplete fetches.

    A selected Fall/Winter term includes any full-year offering that spans it.
    ``offered_sessions`` is a JSON array of usable session selectors. A full-year
    offering therefore includes both term codes and its exact full-year code.
    """
    if offerings is None or manifest is None:
        default_offerings, default_manifest = load_timetable_snapshot()
        offerings = default_offerings if offerings is None else offerings
        manifest = default_manifest if manifest is None else manifest
    index: dict[tuple[str, str], list[dict]] = {}
    for row in offerings:
        index.setdefault((row["campus"], row["course_code"]), []).append(row)
    published = {
        row.get("session_code", row.get("value")): row.get("label", "")
        for row in manifest.get("sessions", [])
    }
    # Support manifests with coverage records but no separate session metadata.
    for row in manifest.get("coverage", []):
        published.setdefault(row["session_code"], row.get("label", row["session_code"]))
    result = []
    for course in courses:
        campus = course.get("campus", "")
        code = course.get("course_code", course.get("code", ""))
        matches = index.get((campus, code), [])
        selected = [row for row in matches if _matches_session(row, session)]
        coverage = _relevant_coverage(manifest, campus, session)
        expected = [
            code for code in published
            if session is None or code == session
            or ("-" not in session and session in str(code).split("-"))
        ]
        complete = bool(expected) and all(
            any(row.get("session_code") == code and row.get("complete") is True for row in coverage)
            for code in expected
        )
        if any(row["status"] == "offered" for row in selected):
            status = "offered"
        elif selected and all(row["status"] == "cancelled" for row in selected):
            status = "cancelled"
        else:
            status = "not_found" if complete else "unknown"
        offered_sessions = sorted(
            code for code in published
            if any(row["status"] == "offered" and _matches_session(row, code) for row in matches)
        )
        details = [
            {
                "session": row["session_code"],
                "label": published.get(row["session_code"], row["session_code"]),
                "term_code": row.get("term_code", ""),
                "status": row["status"],
                "source_url": row["source_url"],
            }
            for row in matches
        ]
        checked_at = max(
            [row.get("retrieved_at", "") for row in coverage]
            + [row.get("source_retrieved_at", "") for row in selected],
            default="",
        )
        result.append(
            {
                **course,
                "offering_status": status,
                "offered_sessions": json.dumps(offered_sessions, ensure_ascii=False),
                "offering_sessions": json.dumps(details, ensure_ascii=False),
                "timetable_source_url": next(
                    (row["source_url"] for row in selected if row["status"] == status), TTB_URL
                ),
                "timetable_checked_at": checked_at,
            }
        )
    return result


def _query(division: str, sessions: list[str]) -> dict:
    # Request shape verified against the official Timetable Builder client.
    return {
        "courseCodeAndTitleProps": {
            "courseCode": "", "courseTitle": "", "courseSectionCode": "", "searchCourseDescription": False,
        },
        "departmentProps": [], "campuses": [], "sessions": sessions, "requirementProps": [],
        "instructor": "", "courseLevels": [], "deliveryModes": [], "dayPreferences": [],
        "timePreferences": [], "divisions": [division], "creditWeights": [],
        "availableSpace": False, "waitListable": False, "page": 1, "pageSize": 20, "direction": "asc",
    }


def _request_json(endpoint: str, payload: dict | None = None, timeout: float = 60) -> dict:
    request = Request(
        API_BASE + endpoint,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json", "Content-Type": "application/json",
            "User-Agent": "CourseInsight/3.0 (public academic timetable research)",
        },
    )
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.load(response)
            statuses = data.get("status", [])
            if not statuses or any(str(item.get("code")) != "0" for item in statuses):
                raise ValueError(f"Timetable returned an unsuccessful status: {statuses}")
            return data
        except (OSError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Could not retrieve {endpoint}; existing snapshots are unchanged") from last_error


def fetch_timetable_snapshot(timeout: float = 60, throttle: float = 0.35) -> tuple[list[dict], dict]:
    """Fetch every currently published session for the three campus divisions.

    getCourses is unpaginated. Each division's combined count and every session's
    count are independently cross-checked against getPageableCourses.total. Any
    mismatch aborts the refresh; callers must retain their previous snapshot.
    """
    retrieved_at = datetime.now(ZoneInfo("America/Toronto")).isoformat(timespec="seconds")
    reference = _request_json("/reference-data", timeout=timeout)["payload"]
    sessions = [row for row in reference["currentSessions"] if not row.get("header")]
    if not sessions or any(not row.get("value") for row in sessions):
        raise ValueError("Official timetable has no published sessions")
    available = {row["value"] for row in reference["divisions"]}
    if not set(DIVISION_CAMPUSES).issubset(available):
        raise ValueError("One or more campus divisions are missing from official reference data")
    normalized = []
    coverage = []
    division_totals = []
    session_values = [row["value"] for row in sessions]
    for division, campus in DIVISION_CAMPUSES.items():
        time.sleep(throttle)
        query = _query(division, session_values)
        raw = _request_json("/getCourses", query, timeout=timeout)["payload"]
        if not isinstance(raw, list):
            raise ValueError("Unexpected getCourses response")
        keys = [(row.get("id"), row.get("code"), row.get("sectionCode")) for row in raw]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate offering identifiers returned for {division}")
        time.sleep(throttle)
        page = _request_json("/getPageableCourses", query, timeout=timeout)["payload"]["pageableCourse"]
        if page["total"] != len(raw):
            raise ValueError(f"Incomplete {division} offering download: {len(raw)} / {page['total']}")
        rows = [normalize_offering(row, division, retrieved_at) for row in raw]
        counts = Counter(row["session_code"] for row in rows)
        if set(counts) - set(session_values):
            raise ValueError(f"Unrecognized offering session for {division}")
        for session in sessions:
            time.sleep(throttle)
            one_query = _query(division, [session["value"]])
            one_page = _request_json("/getPageableCourses", one_query, timeout=timeout)["payload"]["pageableCourse"]
            total = one_page["total"]
            if counts[session["value"]] != total:
                raise ValueError(f"Session completeness mismatch: {division} {session['value']}")
            coverage.append({
                "campus": campus, "division": division, "session_code": session["value"],
                "label": session["label"].strip(), "group": session.get("group"), "complete": True,
                "retrieved_at": retrieved_at, "offering_count": total, "official_total": total,
                "source_url": API_BASE + "/getCourses", "count_source_url": API_BASE + "/getPageableCourses",
                "query_sessions": [session["value"]],
            })
        normalized.extend(rows)
        division_totals.append({"division": division, "campus": campus, "official_total": page["total"]})
    normalized.sort(key=lambda row: (row["campus"], row["course_code"], row["session_code"]))
    manifest = {
        "schema_version": 1, "source_name": "University of Toronto official Timetable Builder",
        "source_url": TTB_URL, "api_base": API_BASE, "reference_url": API_BASE + "/reference-data",
        "retrieved_at": retrieved_at, "timezone": "America/Toronto", "complete": True,
        "scope": "Faculty of Arts and Science (St. George), UTM, UTSC; currently published sessions",
        "sessions": [{"session_code": row["value"], "label": row["label"].strip(),
                      "group": row.get("group")} for row in sessions],
        "coverage": coverage, "division_totals": division_totals, "offering_count": len(normalized),
        "unique_course_count": len({(row["campus"], row["course_code"]) for row in normalized}),
        "status_counts": dict(Counter(row["status"] for row in normalized)),
        "verification": "Unpaginated getCourses response counts equal combined and per-session getPageableCourses totals",
        "limitations": [
            "Published timetable snapshot, not a guarantee of future delivery or registration eligibility.",
            "Closed or full enrolment is still offered; section cancellations are preserved separately.",
            "not_found means absent from a fully retrieved published session; incomplete coverage means unknown.",
            "Y offerings count for both constituent terms when filtering. No private ACORN data or credentials used.",
            "Source created/modified timestamps are preserved verbatim; their timezone is not inferred.",
        ],
    }
    return normalized, manifest


def write_timetable_snapshot(offerings: list[dict], manifest: dict, directory: Path | str = REFERENCE_DIR) -> None:
    """Write only validated complete refreshes; failure before this preserves both files."""
    if not manifest.get("complete") or not manifest.get("coverage") or not all(
        row.get("complete") is True for row in manifest["coverage"]
    ):
        raise ValueError("Refusing to replace a snapshot with incomplete offering coverage")
    validate_timetable_snapshot(offerings, manifest)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(offerings, ensure_ascii=False, indent=2) + "\n"
    manifest = {**manifest, "offerings_sha256": sha256(serialized.encode("utf-8")).hexdigest()}
    outputs = [
        ("timetable_offerings.json", serialized),
        ("timetable_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"),
    ]
    previous = {}
    for name, content in outputs:
        target = directory / name
        previous[name] = target.read_bytes() if target.exists() else None
        temporary = directory / f".{name}.tmp"
        temporary.write_text(content, encoding="utf-8")
    try:
        for name, _ in outputs:
            (directory / f".{name}.tmp").replace(directory / name)
    except OSError:
        # Also retain the previous pair if a filesystem error interrupts renames.
        for name, original in previous.items():
            target = directory / name
            if original is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(original)
        raise
    finally:
        for name, _ in outputs:
            (directory / f".{name}.tmp").unlink(missing_ok=True)
