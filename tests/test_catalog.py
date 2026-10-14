"""Official metadata must remain literal, campus-specific and reproducible."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.update_catalog import refresh_catalog
from src.catalog import (
    CATALOG_PATH,
    REFERENCE_DIR,
    catalog_sources,
    load_catalog,
    parse_calendar_section,
    validate_catalog,
)


def _course_html(code, title, fields, description=""):
    body = f'<div class="views-field views-field-body"><div class="field-content">{description}</div></div>'
    for name, value in fields.items():
        body += (
            f'<span class="views-field views-field-{name}"><strong>Label: </strong>'
            f'<span class="field-content">{value}</span></span>'
        )
    return (
        f'<div><h3 class="js-views-accordion-group-header"><div>{code} - {title}</div></h3>'
        f"<div>{body}</div></div>"
    )


def test_st_george_preserves_compound_requirements_and_multiple_breadths():
    html = _course_html(
        "HIS100Y1",
        "History &amp; the Environment",
        {
            "field-prerequisite": '(A minimum of 60% in <a href="/course/ABC100H1">ABC100H1</a>) or permission',
            "field-corequisite": "DEF100H1 or equivalent",
            "field-exclusion": "HIS101Y1; may not be taken concurrently",
            "field-recommended": "Grade 12 English",
            "field-breadth-requirements": "Society and its Institutions (3) + Living Things and Their Environment (4)",
        },
        "<p>Restricted to first-year students. Not eligible for CR/NCR.</p>",
    )
    record = parse_calendar_section(
        html, campus="St. George", department="History", retrieved_at="2026-10-13"
    )[0]
    assert record["course_name"] == "History & the Environment"
    assert record["prerequisite"] == "(A minimum of 60% in ABC100H1) or permission"
    assert record["corequisite"] == "DEF100H1 or equivalent"
    assert record["exclusion"] == "HIS101Y1; may not be taken concurrently"
    assert record["recommended_preparation"] == "Grade 12 English"
    assert json.loads(record["breadth_categories"]) == [3, 4]
    assert "Restricted to first-year students" in record["requirement_notes"]
    assert record["credit"] == 1.0
    validate_catalog([record])


def test_missing_prerequisite_does_not_become_no_prerequisite():
    html = _course_html(
        "CSC108H1",
        "Introduction to Computer Programming",
        {
            "field-breadth-requirements": "The Physical and Mathematical Universes (5)",
        },
    )
    record = parse_calendar_section(
        html, campus="St. George", department="Computer Science", retrieved_at="2026-10-13"
    )[0]
    assert record["prerequisite"] == ""
    assert record["prerequisite_status"] == "not_listed"
    assert record["corequisite"] == ""


def test_utm_distribution_is_not_mapped_to_st_george_br():
    html = _course_html(
        "CSC110Y5",
        "Foundations of Computer Science 1",
        {
            "field-prerequisite": "Minimum 70% in Grade 12 Advanced Functions (MHF4U)",
            "field-enrolment-limits": "Restricted to students in year of study 1 in Computer Science",
            "field-distribution-requirements": "Science, Humanities",
            "field-note": "Only offered in the Fall term.",
        },
    )
    record = parse_calendar_section(
        html, campus="Mississauga", department="Computer Science", retrieved_at="2026-10-13"
    )[0]
    assert record["requirement_system"] == "utm_distribution"
    assert record["breadth_categories"] == "[]"
    assert record["breadth_requirements"] == ""
    assert json.loads(record["requirement_categories"]) == ["Science", "Humanities"]
    assert record["enrolment_requirements"].startswith("Restricted to")
    assert record["requirement_notes"] == "Only offered in the Fall term."
    validate_catalog([record])


def test_utm_social_science_does_not_invent_a_science_distribution():
    html = _course_html(
        "ECO101H5",
        "Principles of Microeconomics",
        {
            "field-distribution-requirements": "Social Science",
        },
    )
    record = parse_calendar_section(
        html, campus="Mississauga", department="Economics", retrieved_at="2026-10-13"
    )[0]
    assert json.loads(record["requirement_categories"]) == ["Social Science"]


def test_utm_body_enrolment_and_term_restriction_are_preserved():
    restriction = "Note: This course is not open to Commerce or Management Specialist/Major students during Fall/Winter."
    html = _course_html(
        "ECO200Y5",
        "Microeconomic Theory",
        {
            "field-prerequisite": "ECO101H5 and ECO102H5",
            "field-distribution-requirements": "Social Science",
        },
        f"<p>Study of microeconomic theory.</p><p>{restriction}</p>",
    )
    record = parse_calendar_section(
        html, campus="Mississauga", department="Economics", retrieved_at="2026-10-13"
    )[0]
    assert record["requirement_notes"] == restriction


@pytest.mark.parametrize(
    "campus,code,field",
    [
        ("St. George", "CSC108H1", "field-breadth-requirements"),
        ("Mississauga", "CSC108H5", "field-distribution-requirements"),
        ("Scarborough", "CSCA08H3", "field-breadth-requirements"),
    ],
)
def test_unknown_requirement_taxonomy_fails_instead_of_becoming_empty(campus, code, field):
    html = _course_html(code, "Programming", {field: "New category introduced upstream"})
    with pytest.raises(ValueError, match="Unrecognized official"):
        parse_calendar_section(html, campus=campus, department="Computer Science", retrieved_at="2026-10-13")


def test_utsc_comma_in_category_name_is_not_a_separator():
    html = _course_html(
        "ENGA01H3",
        "What Is Literature?",
        {
            "field-breadth-requirements": "Arts, Literature and Language",
            "field-recommended-preparation": "High school English",
        },
    )
    record = parse_calendar_section(
        html, campus="Scarborough", department="English", retrieved_at="2026-10-13"
    )[0]
    assert json.loads(record["requirement_categories"]) == ["Arts, Literature and Language"]
    assert record["breadth_categories"] == "[]"
    assert record["course_level"] == 100
    assert record["recommended_preparation"] == "High school English"
    validate_catalog([record])


def test_program_admission_requirements_never_become_course_prerequisites():
    html = (
        '<h3 class="js-views-accordion-group-header">Computer Science Major - ASMAJ1689</h3>'
        '<div class="views-field-field-prerequisite">PROGRAM ADMISSION TEXT</div>'
    )
    html += _course_html(
        "CSC108H1",
        "Programming",
        {"field-breadth-requirements": "The Physical and Mathematical Universes (5)"},
    )
    record = parse_calendar_section(
        html, campus="St. George", department="Computer Science", retrieved_at="2026-10-13"
    )[0]
    assert record["prerequisite"] == ""


def test_changed_calendar_markup_fails_explicitly():
    with pytest.raises(ValueError, match="No recognized courses"):
        parse_calendar_section(
            "<h1>Maintenance</h1>", campus="St. George", department="Statistics", retrieved_at="2026-10-13"
        )


def test_checked_in_catalog_has_verified_coverage_and_manifest():
    records = load_catalog()
    assert len(records) == 200
    assert Counter(row["campus"] for row in records) == {
        "St. George": 80,
        "Mississauga": 60,
        "Scarborough": 60,
    }
    assert len({row["department"] for row in records}) == 8
    codes = {row["course_code"] for row in records}
    assert {"STA303H1", "CSC108H1", "CSC148H1", "CSC108H5", "CSCA08H3"} <= codes
    manifest = json.loads((REFERENCE_DIR / "catalog_manifest.json").read_text())
    assert manifest["catalog_sha256"] == hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    assert len(manifest["sources"]) == 24
    assert all(row["metadata_source"] == "official_calendar" for row in records)


@pytest.mark.parametrize(
    "change",
    [
        {"campus": "Scarborough"},
        {"breadth_categories": "[8]"},
        {"source_url": "https://example.com/course/csc108h1"},
        {"prerequisite_status": "none"},
        {"metadata_source": "synthetic"},
    ],
)
def test_validation_rejects_inconsistent_official_metadata(change):
    row = deepcopy(load_catalog()[0])
    row.update(change)
    with pytest.raises(ValueError):
        validate_catalog([row])


def test_validation_rejects_duplicates_and_cross_campus_br():
    records = load_catalog()
    with pytest.raises(ValueError, match="duplicate"):
        validate_catalog([records[0], records[0]])
    utm = deepcopy(next(row for row in records if row["campus"] == "Mississauga"))
    utm["breadth_categories"] = "[5]"
    with pytest.raises(ValueError, match="cannot be assigned"):
        validate_catalog([utm])


def test_failed_refresh_preserves_both_existing_snapshot_files(tmp_path):
    output = tmp_path / "output"
    html_dir = tmp_path / "html"
    output.mkdir()
    html_dir.mkdir()
    (output / "uoft_courses.json").write_text("existing catalogue")
    (output / "catalog_manifest.json").write_text("existing provenance")
    first = catalog_sources()[0]
    (html_dir / f"{first['key']}.html").write_text("<h1>University calendar is unavailable</h1>")
    with pytest.raises(ValueError, match="No recognized courses"):
        refresh_catalog(html_dir=html_dir, output_dir=output, retrieved_at="2026-10-13")
    assert (output / "uoft_courses.json").read_text() == "existing catalogue"
    assert (output / "catalog_manifest.json").read_text() == "existing provenance"


def test_snapshot_round_trip_loader(tmp_path):
    record = load_catalog()[0]
    path = tmp_path / "small_catalog.json"
    path.write_text(json.dumps([record]))
    assert load_catalog(Path(path)) == [record]
