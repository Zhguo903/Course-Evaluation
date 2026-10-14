"""Historical evaluations retain source facts without inventing ratings or identity."""

from copy import deepcopy
import csv
import io
import json
from pathlib import Path

import pytest

from src.evaluations import (
    SOURCES,
    import_evaluation_sources,
    load_evaluation_snapshot,
    normalize_evaluations,
    validate_evaluation_snapshot,
    write_evaluation_snapshot,
)


CATALOGUE = [
    {"campus": "St. George", "course_code": "CSC108H1"},
    {"campus": "Mississauga", "course_code": "CSC108H5"},
    {"campus": "Scarborough", "course_code": "CSCA08H3"},
]


def _csv(source, changes=None, additional=None):
    campus_codes = {"St. George": "CSC108H1", "Mississauga": "CSC108H5", "Scarborough": "CSCA08H3"}
    code = campus_codes[source["campus"]]
    record = {
        "Course Code": code, "Course": f"Computer Programming {code}-F-LEC0101", "Year": "2024", "Term": "Fall",
        "Number Invited": "100", source["responses_field"]: "40", source["overall_field"]: "4.1",
        source["workload_field"]: "3.5", source["recommendation_field"]: "4.3", "Last Name": "ExampleTeacher",
    }
    record.update(changes or {})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(record))
    writer.writeheader()
    writer.writerow(record)
    for change in additional or []:
        writer.writerow({**record, **change})
    return output.getvalue().encode("utf-8")


def test_numeric_facts_and_correct_official_question_mapping_for_each_campus():
    for source in SOURCES:
        records, metadata = normalize_evaluations(_csv(source), source, CATALOGUE, "2026-10-13T23:00:00-04:00")
        row = records[0]
        assert row["overall_score"] == 4.1
        assert row["workload_score"] == 3.5
        assert row["recommendation_score"] == 4.3
        assert row["response_count"] == 40 and row["invited_count"] == 100
        assert row["match_status"] == "matched"
        assert row["source_row_number"] == 2
        assert metadata["record_count"] == 1
        assert "ExampleTeacher" not in json.dumps(records)
        assert "Computer Programming" not in json.dumps(records)


def test_missing_score_and_invitation_are_unknown_not_zero():
    source = SOURCES[0]
    records, _ = normalize_evaluations(_csv(source, {"ARTSC2": "", "ARTSC3": "", "Number Invited": ""}), source, CATALOGUE, "now")
    assert records[0]["workload_score"] is None
    assert records[0]["recommendation_score"] is None
    assert records[0]["invited_count"] is None
    assert records[0]["quality_flags"] == ["invited_count_not_listed"]


@pytest.mark.parametrize("score", ["0", "5.1", "-1", "nan", "inf"])
def test_scores_outside_verified_scale_are_rejected(score):
    source = SOURCES[0]
    with pytest.raises(ValueError, match="1–5"):
        normalize_evaluations(_csv(source, {"ARTSC2": score}), source, CATALOGUE, "now")


@pytest.mark.parametrize("score", ["1", "5"])
def test_valid_scale_endpoints_are_retained(score):
    source = SOURCES[0]
    rows, _ = normalize_evaluations(_csv(source, {"ARTSC2": score}), source, CATALOGUE, "now")
    assert rows[0]["workload_score"] == float(score)


def test_exact_campus_full_code_matching_never_uses_another_campuss_course():
    source = SOURCES[1]
    records, _ = normalize_evaluations(_csv(source, {"Course Code": "CSC108H1"}), source, CATALOGUE, "now")
    assert records[0]["course_code"] == ""
    assert records[0]["source_course_code"] == "CSC108H1"
    assert records[0]["match_status"] == "unmatched"


def test_removed_or_abbreviated_courses_are_not_matched_by_title():
    source = SOURCES[0]
    for code in ["CSC108", "ZZZ999H1"]:
        changes = {"Course Code": code, "Course": "Computer Programming"}
        records, _ = normalize_evaluations(_csv(source, changes), source, CATALOGUE, "now")
        assert records[0]["course_code"] == ""
        assert records[0]["source_course_code"] == code


def test_single_unambiguous_full_code_in_source_label_can_be_matched():
    source = SOURCES[0]
    records, _ = normalize_evaluations(_csv(source, {"Course Code": "Computer Programming"}), source, CATALOGUE, "now")
    assert records[0]["course_code"] == "CSC108H1"
    assert records[0]["match_basis"] == "unique_full_code_in_source_label"


def test_multiple_full_codes_in_label_are_not_guessed():
    source = SOURCES[0]
    changes = {"Course Code": "Crosslisted", "Course": "CSC108H1 and CSC148H1"}
    rows, _ = normalize_evaluations(_csv(source, changes), source, CATALOGUE, "now")
    assert rows[0]["match_status"] == "unmatched"


def test_same_cohort_reports_are_preserved_without_summing_respondents():
    source = SOURCES[0]
    data = _csv(source, additional=[{"Last Name": "AnotherTeacher"}])
    rows, metadata = normalize_evaluations(data, source, CATALOGUE, "now")
    assert len(rows) == 2
    assert rows[0]["cohort_id"] == rows[1]["cohort_id"]
    assert rows[0]["evaluation_id"] != rows[1]["evaluation_id"]
    assert [row["response_count"] for row in rows] == [40, 40]
    assert all("multiple_reports_same_cohort" in row["quality_flags"] for row in rows)
    assert metadata["multiple_report_cohort_count"] == 1
    assert "unique_student_count" not in metadata


def test_source_count_anomaly_is_retained_and_flagged():
    source = SOURCES[0]
    rows, _ = normalize_evaluations(_csv(source, {"Number Invited": "30"}), source, CATALOGUE, "now")
    assert rows[0]["response_count"] == 40 and rows[0]["invited_count"] == 30
    assert "responses_exceed_invited_in_source" in rows[0]["quality_flags"]


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    for source in SOURCES:
        (tmp_path / source["filename"]).write_bytes(_csv(source))
    records, manifest = import_evaluation_sources(tmp_path, CATALOGUE)
    write_evaluation_snapshot(records, manifest, tmp_path)
    monkeypatch.setattr("src.evaluations.EVALUATIONS_PATH", tmp_path / "course_evaluations.json")
    monkeypatch.setattr("src.evaluations.MANIFEST_PATH", tmp_path / "evaluation_manifest.json")
    return tmp_path, records, manifest


def test_round_trip_integrity_with_three_sources(snapshot):
    _, original, _ = snapshot
    rows, manifest = load_evaluation_snapshot()
    assert rows == original
    assert manifest["record_count"] == 3
    assert manifest["matched_current_course_count"] == 3
    assert manifest["metrics"]["workload_score"]["higher_means"] == "heavier reported workload, not course difficulty"


def test_both_missing_files_return_explicitly_unavailable(snapshot):
    directory, _, _ = snapshot
    (directory / "course_evaluations.json").unlink()
    (directory / "evaluation_manifest.json").unlink()
    rows, manifest = load_evaluation_snapshot()
    assert rows == [] and manifest["complete"] is False


@pytest.mark.parametrize("filename", ["course_evaluations.json", "evaluation_manifest.json"])
def test_single_missing_file_is_rejected(snapshot, filename):
    directory, _, _ = snapshot
    (directory / filename).unlink()
    with pytest.raises(ValueError, match="both be present"):
        load_evaluation_snapshot()


def test_hash_tampering_is_rejected(snapshot):
    directory, _, _ = snapshot
    (directory / "course_evaluations.json").write_text("[]")
    with pytest.raises(ValueError, match="SHA-256"):
        load_evaluation_snapshot()


def test_manifest_source_count_tampering_is_rejected(snapshot):
    directory, _, _ = snapshot
    path = directory / "evaluation_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["sources"][0]["record_count"] += 1
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="count mismatch"):
        load_evaluation_snapshot()


def test_duplicate_report_id_invalid_source_or_identifying_text_rejected(snapshot):
    _, records, manifest = snapshot
    repeated = deepcopy(records)
    repeated.append(deepcopy(records[0]))
    with pytest.raises(ValueError, match="duplicate"):
        validate_evaluation_snapshot(repeated, manifest)
    modified = deepcopy(records)
    modified[0]["source_url"] = "https://example.org/fake"
    with pytest.raises(ValueError, match="source provenance"):
        validate_evaluation_snapshot(modified, manifest)
    modified = deepcopy(records)
    modified[0]["instructor_last_name"] = "Excluded"
    with pytest.raises(ValueError, match="Identifying names"):
        validate_evaluation_snapshot(modified, manifest)


def test_failed_import_cannot_overwrite_verified_pair(snapshot):
    directory, _, manifest = snapshot
    before = {name: (directory / name).read_bytes() for name in ["course_evaluations.json", "evaluation_manifest.json"]}
    (directory / SOURCES[1]["filename"]).unlink()
    with pytest.raises(FileNotFoundError):
        import_evaluation_sources(directory, CATALOGUE)
    bad_manifest = deepcopy(manifest)
    bad_manifest["complete"] = False
    with pytest.raises(ValueError):
        write_evaluation_snapshot([], bad_manifest, directory)
    assert all((directory / name).read_bytes() == content for name, content in before.items())


def test_checked_in_real_snapshot_has_consistent_counts_scores_and_no_student_comment_fields():
    rows, manifest = load_evaluation_snapshot()
    assert len(rows) == manifest["record_count"] == sum(source["record_count"] for source in manifest["sources"])
    assert manifest["matched_record_count"] + manifest["unmatched_record_count"] == len(rows)
    assert {source["campus"] for source in manifest["sources"]} == {"St. George", "Mississauga", "Scarborough"}
    assert all(row["source_kind"] == "third_party_historical_official_evaluations" for row in rows)
    for key in ["overall_score", "workload_score", "recommendation_score"]:
        assert sum(row[key] is None for row in rows) == manifest["missing_scores"][key]
        assert all(row[key] is None or 1 <= row[key] <= 5 for row in rows)
    assert Path(__file__).resolve().parents[1].joinpath("data/reference/course_evaluations.json").stat().st_size < 100_000_000
