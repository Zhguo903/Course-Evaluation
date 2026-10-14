"""Timetable completeness, cancellations and honest unknown/absence semantics."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from src.timetable import (
    DIVISION_CAMPUSES,
    API_BASE,
    OFFERINGS_PATH,
    annotate_offerings,
    fetch_timetable_snapshot,
    load_timetable_snapshot,
    normalize_offering,
    validate_timetable_snapshot,
    write_timetable_snapshot,
)


def _manifest():
    sessions = [
        {"session_code": "20269", "label": "Fall 2026 (F)"},
        {"session_code": "20271", "label": "Winter 2027 (S)"},
        {"session_code": "20269-20271", "label": "Fall-Winter 2026-2027 (Y)"},
    ]
    return {"complete": True, "sessions": sessions, "coverage": [
        {**session, "campus": "St. George", "complete": True, "retrieved_at": "2026-10-13"}
        for session in sessions
    ]}


def _raw_course(**changes):
    value = {
        "id": "official-course-id", "code": "CSC108H1", "name": "Computer Programming",
        "faculty": {"code": "ARTSC"}, "sessions": ["20269"], "sectionCode": "F",
        "primaryTeachMethod": "LEC", "cancelInd": "N", "created": "2026-10-14@02:43:07.180",
        "sections": [{"name": "LEC0101", "type": "Lecture", "teachMethod": "LEC",
                      "cancelInd": "N", "openLimitInd": "C"}],
    }
    value.update(changes)
    return value


def test_closed_enrolment_is_offered_not_cancelled():
    row = normalize_offering(_raw_course(), "ARTSC", "2026-10-13")
    assert row["status"] == "offered"
    assert row["sections"][0]["enrolment_closed"] is True
    assert "currentEnrolment" not in row["sections"][0]
    assert row["source_url"].startswith("https://api.easi.utoronto.ca/ttb/findById?id=")
    assert row["source_created_at"] == "2026-10-14@02:43:07.180"


@pytest.mark.parametrize("course_cancelled,lecture_cancelled", [(True, False), (False, True)])
def test_course_or_all_primary_sections_cancelled(course_cancelled, lecture_cancelled):
    raw = _raw_course(cancelInd="Y" if course_cancelled else "N")
    raw["sections"][0]["cancelInd"] = "Y" if lecture_cancelled else "N"
    assert normalize_offering(raw, "ARTSC", "2026-10-13")["status"] == "cancelled"


def test_one_cancelled_tutorial_does_not_cancel_active_course():
    raw = _raw_course()
    raw["sections"].append({"name": "TUT0101", "teachMethod": "TUT", "cancelInd": "Y"})
    assert normalize_offering(raw, "ARTSC", "2026-10-13")["status"] == "offered"


def test_course_identifier_or_faculty_mismatch_rejected():
    with pytest.raises(ValueError, match="faculty"):
        normalize_offering(_raw_course(), "ERIN", "2026-10-13")
    with pytest.raises(ValueError, match="identifier"):
        normalize_offering(_raw_course(code=""), "ARTSC", "2026-10-13")
    with pytest.raises(ValueError, match="session"):
        normalize_offering(_raw_course(sessions=[]), "ARTSC", "2026-10-13")


def test_absent_course_requires_complete_campus_and_all_selected_term_coverage():
    course = [{"campus": "St. George", "course_code": "CSC999H1"}]
    manifest = _manifest()
    assert annotate_offerings(course, [], manifest)[0]["offering_status"] == "not_found"
    assert annotate_offerings(course, [], manifest, "20269")[0]["offering_status"] == "not_found"
    manifest["coverage"][-1]["complete"] = False
    assert annotate_offerings(course, [], manifest, "20269")[0]["offering_status"] == "unknown"
    manifest["coverage"] = manifest["coverage"][:1]
    assert annotate_offerings(course, [], manifest, "20269")[0]["offering_status"] == "unknown"
    course[0]["campus"] = "Mississauga"
    assert annotate_offerings(course, [], _manifest())[0]["offering_status"] == "unknown"


def test_unpublished_session_is_unknown_and_missing_manifest_is_unknown():
    course = [{"campus": "St. George", "course_code": "CSC999H1"}]
    assert annotate_offerings(course, [], _manifest(), "20285")[0]["offering_status"] == "unknown"
    assert annotate_offerings(course, [], {"coverage": [], "sessions": []})[0]["offering_status"] == "unknown"


def test_full_year_offering_is_available_in_both_constituent_terms():
    raw = _raw_course(code="MAT137Y1", sessions=["20269", "20271"], sectionCode="Y")
    offering = normalize_offering(raw, "ARTSC", "2026-10-13")
    course = [{"campus": "St. George", "course_code": "MAT137Y1"}]
    for session in [None, "20269", "20271", "20269-20271"]:
        row = annotate_offerings(course, [offering], _manifest(), session)[0]
        assert row["offering_status"] == "offered"
        assert json.loads(row["offered_sessions"]) == ["20269", "20269-20271", "20271"]
        assert json.loads(row["offering_sessions"])[0]["term_code"] == "Y"


def test_term_filter_does_not_show_fall_course_as_winter_offering():
    offering = normalize_offering(_raw_course(), "ARTSC", "2026-10-13")
    course = [{"campus": "St. George", "course_code": "CSC108H1"}]
    assert annotate_offerings(course, [offering], _manifest(), "20269")[0]["offering_status"] == "offered"
    assert annotate_offerings(course, [offering], _manifest(), "20271")[0]["offering_status"] == "not_found"


def test_active_offering_takes_precedence_over_cancelled_offering():
    fall = normalize_offering(_raw_course(id="fall", cancelInd="Y"), "ARTSC", "2026-10-13")
    winter = normalize_offering(_raw_course(id="winter", sessions=["20271"], sectionCode="S"), "ARTSC", "2026-10-13")
    course = [{"campus": "St. George", "course_code": "CSC108H1"}]
    assert annotate_offerings(course, [fall, winter], _manifest())[0]["offering_status"] == "offered"
    assert annotate_offerings(course, [fall, winter], _manifest())[0]["timetable_source_url"] == winter["source_url"]
    assert annotate_offerings(course, [fall, winter], _manifest(), "20269")[0]["offering_status"] == "cancelled"
    assert annotate_offerings(course, [fall, winter], _manifest(), "20269")[0]["timetable_source_url"] == fall["source_url"]


def test_campus_identity_does_not_leak_another_campuss_offering():
    offering = normalize_offering(_raw_course(), "ARTSC", "2026-10-13")
    course = [{"campus": "Mississauga", "course_code": "CSC108H1"}]
    assert annotate_offerings(course, [offering], _manifest())[0]["offering_status"] == "unknown"


def test_fetch_rejects_incomplete_response_before_any_replacement(monkeypatch):
    reference = {"payload": {"currentSessions": [{"value": "20269", "label": "Fall", "header": False}],
                             "divisions": [{"value": key} for key in DIVISION_CAMPUSES]}}

    def request(endpoint, payload=None, timeout=60):
        if endpoint == "/reference-data":
            return reference
        if endpoint == "/getCourses":
            return {"payload": [_raw_course()]}
        return {"payload": {"pageableCourse": {"total": 2}}}

    monkeypatch.setattr("src.timetable._request_json", request)
    with pytest.raises(ValueError, match="Incomplete"):
        fetch_timetable_snapshot(throttle=0)


def test_incomplete_refresh_preserves_previous_files(tmp_path):
    original = "previous verified data\n"
    for name in ["timetable_offerings.json", "timetable_manifest.json"]:
        (tmp_path / name).write_text(original)
    manifest = _manifest()
    manifest["coverage"][0]["complete"] = False
    with pytest.raises(ValueError, match="incomplete"):
        write_timetable_snapshot([], manifest, tmp_path)
    assert all(path.read_text() == original for path in tmp_path.iterdir())


def test_actual_snapshot_covers_all_published_campus_sessions_and_matches_official_counts():
    offerings, manifest = load_timetable_snapshot()
    assert len(offerings) == manifest["offering_count"]
    assert manifest["complete"] is True
    assert set(DIVISION_CAMPUSES.values()) == {row["campus"] for row in manifest["coverage"]}
    assert len(manifest["coverage"]) == 3 * len(manifest["sessions"])
    assert all(row["complete"] is True for row in manifest["coverage"])
    assert {row["status"] for row in offerings}.issubset({"offered", "cancelled"})
    assert len({(row["campus"], row["course_code"]) for row in offerings}) == manifest["unique_course_count"]
    for coverage in manifest["coverage"]:
        count = sum(row["division"] == coverage["division"] and row["session_code"] == coverage["session_code"]
                    for row in offerings)
        assert count == coverage["offering_count"] == coverage["official_total"]
    for coverage in manifest["division_totals"]:
        assert sum(row["division"] == coverage["division"] for row in offerings) == coverage["official_total"]
    assert manifest["offerings_sha256"] == sha256(OFFERINGS_PATH.read_bytes()).hexdigest()


def test_annotation_never_mutates_catalogue_record():
    courses = [{"campus": "St. George", "course_code": "CSC108H1"}]
    original = deepcopy(courses)
    annotate_offerings(courses, [], _manifest())
    assert courses == original


@pytest.fixture
def verified_pair(tmp_path, monkeypatch):
    """Small complete three-campus fixture, used only to test storage failures."""
    retrieved_at = "2026-10-13T22:46:06-04:00"
    offerings = [normalize_offering(_raw_course(), "ARTSC", retrieved_at)]
    manifest = {
        "api_base": API_BASE, "reference_url": API_BASE + "/reference-data",
        "retrieved_at": retrieved_at, "complete": True,
        "sessions": [{"session_code": "20269", "label": "Fall 2026 (F)"}],
        "coverage": [{
            "division": division, "campus": campus, "session_code": "20269", "complete": True,
            "retrieved_at": retrieved_at, "offering_count": int(division == "ARTSC"),
            "official_total": int(division == "ARTSC"), "source_url": API_BASE + "/getCourses",
            "count_source_url": API_BASE + "/getPageableCourses",
        } for division, campus in DIVISION_CAMPUSES.items()],
        "offering_count": 1, "unique_course_count": 1, "status_counts": {"offered": 1},
        "division_totals": [{"division": division, "campus": campus, "official_total": int(division == "ARTSC")}
                            for division, campus in DIVISION_CAMPUSES.items()],
    }
    write_timetable_snapshot(offerings, manifest, tmp_path)
    monkeypatch.setattr("src.timetable.OFFERINGS_PATH", tmp_path / "timetable_offerings.json")
    monkeypatch.setattr("src.timetable.MANIFEST_PATH", tmp_path / "timetable_manifest.json")
    return tmp_path, offerings, manifest


def test_both_snapshot_files_missing_is_unknown(verified_pair):
    directory, _, _ = verified_pair
    for path in directory.iterdir():
        path.unlink()
    offerings, manifest = load_timetable_snapshot()
    assert offerings == [] and manifest["coverage"] == []
    assert annotate_offerings([{"campus": "St. George", "course_code": "CSC108H1"}])[0]["offering_status"] == "unknown"


@pytest.mark.parametrize("missing", ["timetable_offerings.json", "timetable_manifest.json"])
def test_one_missing_file_cannot_make_complete_absence_claim(verified_pair, missing):
    directory, _, _ = verified_pair
    (directory / missing).unlink()
    with pytest.raises(ValueError, match="must both be present"):
        load_timetable_snapshot()
    with pytest.raises(ValueError, match="must both be present"):
        annotate_offerings([{"campus": "St. George", "course_code": "CSC108H1"}])


def test_modified_snapshot_is_rejected_by_hash(verified_pair):
    directory, _, _ = verified_pair
    (directory / "timetable_offerings.json").write_text("[]\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_timetable_snapshot()


def test_manifest_count_tampering_cannot_prove_absence(verified_pair):
    directory, _, _ = verified_pair
    path = directory / "timetable_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["coverage"][0]["official_total"] = 2
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="session counts"):
        load_timetable_snapshot()


@pytest.mark.parametrize("change,message", [
    ({"source_url": "https://example.org/fake-data"}, "source provenance"),
    ({"status": "not_found"}, "offering status"),
    ({"campus": "Mississauga"}, "campus/division"),
    ({"source_retrieved_at": "2025-01-01"}, "retrieval times"),
])
def test_invalid_row_provenance_or_status_is_rejected(verified_pair, change, message):
    _, offerings, manifest = verified_pair
    offerings[0].update(change)
    with pytest.raises(ValueError, match=message):
        validate_timetable_snapshot(offerings, manifest)


def test_duplicate_offering_identifier_is_rejected(verified_pair):
    _, offerings, manifest = verified_pair
    offerings.append(deepcopy(offerings[0]))
    with pytest.raises(ValueError, match="duplicate timetable offering"):
        validate_timetable_snapshot(offerings, manifest)


def test_complete_manifest_must_cover_each_published_campus_session(verified_pair):
    _, offerings, manifest = verified_pair
    manifest["coverage"].pop()
    with pytest.raises(ValueError, match="every published campus/session"):
        validate_timetable_snapshot(offerings, manifest)
