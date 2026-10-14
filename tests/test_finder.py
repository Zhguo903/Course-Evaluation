"""Filtering must be fast, literal, campus-aware and honest about unknown offerings."""

import json

import pandas as pd

from src.catalog import load_catalog
from src.finder import available_sessions, course_categories, filter_courses


def _courses(official_sample):
    table = pd.DataFrame(official_sample)
    table["offering_status"] = ["offered", "not_found", "unknown"]
    table["offering_status_by_session"] = [json.dumps({"20269": state}) for state in table.offering_status]
    return table


def test_empty_filters_return_all_real_records(official_sample):
    table = _courses(official_sample)
    result = filter_courses(table, campuses=[], departments=[], levels=[])
    assert len(result) == 3
    assert result.match_reason.str.len().gt(0).all()
    assert "preference_score" not in result


def test_combined_filters_and_multiple_categories(official_sample):
    table = _courses(official_sample)
    source = table.iloc[0]
    labels = course_categories(source)
    result = filter_courses(
        table,
        campuses=[source.campus],
        levels=[source.course_level],
        departments=[source.department],
        categories=labels,
    )
    assert result.course_code.tolist() == [source.course_code]
    assert source.campus in result.match_reason.iloc[0]


def test_literal_search_handles_brackets_and_empty_results(official_sample):
    table = _courses(official_sample)
    assert filter_courses(table, query="[nothing+(").empty
    assert filter_courses(table, campuses=["not a campus"]).empty
    assert filter_courses(table.iloc[:0]).empty


def test_known_code_search_and_no_false_offered_state(official_sample):
    table = _courses(official_sample)
    code = table.course_code.iloc[0]
    assert filter_courses(table, query=code).course_code.tolist() == [code]
    assert filter_courses(table, offering_status="offered", session="20269").course_code.tolist() == [code]
    assert filter_courses(table, offering_status="offered", session="unpublished").empty
    unknown = filter_courses(table, session="unpublished")
    assert unknown.offering_status.eq("unknown").all()


def test_session_choices_only_come_from_verified_reference():
    frame = pd.DataFrame(
        [{"session_code": "20269", "label": "Fall 2026"}, {"session_code": "20269", "label": "Fall 2026"}]
    )
    assert available_sessions(frame) == [("20269", "Fall 2026")]
    assert available_sessions(pd.DataFrame()) == []


def test_source_link_tracks_selected_session_and_status(official_sample):
    table = _courses(official_sample).iloc[:1].copy()
    table["offering_status_by_session"] = json.dumps(
        {"20269": "offered", "20271": "offered", "20269-20271": "not_found"}
    )
    table["offering_sessions"] = json.dumps(
        [
            {
                "session": "20269",
                "status": "offered",
                "source_url": "https://api.easi.utoronto.ca/ttb/findById?id=fall",
            },
            {
                "session": "20271",
                "status": "offered",
                "source_url": "https://api.easi.utoronto.ca/ttb/findById?id=winter",
            },
        ]
    )
    winter = filter_courses(table, session="20271").iloc[0]
    assert winter.timetable_source_url.endswith("id=winter")
    assert winter.selected_session == "20271"
    year = filter_courses(table, session="20269-20271").iloc[0]
    assert year.offering_status == "not_found"
    assert year.timetable_source_url == "https://ttb.utoronto.ca/"
    assert (
        filter_courses(table, session="unpublished").iloc[0].timetable_source_url
        == "https://ttb.utoronto.ca/"
    )


def test_full_year_source_is_valid_for_both_constituent_terms(official_sample):
    table = _courses(official_sample).iloc[:1].copy()
    table["offering_status_by_session"] = json.dumps({"20269": "offered", "20271": "offered"})
    table["offering_sessions"] = json.dumps(
        [
            {
                "session": "20269-20271",
                "status": "offered",
                "source_url": "https://api.easi.utoronto.ca/ttb/findById?id=year",
            }
        ]
    )
    for session in ["20269", "20271"]:
        assert filter_courses(table, session=session).iloc[0].timetable_source_url.endswith("id=year")
    assert filter_courses(table).iloc[0].selected_session == "all_published"


def test_secondary_official_academic_area_is_filterable():
    course = next(row for row in load_catalog() if row["course_code"] == "CSC108H1")
    assert course["department"] == "Computer Science"
    assert "Data Science" in json.loads(course["subject_areas"])
    result = filter_courses(pd.DataFrame([course]), departments=["Data Science"])
    assert result.course_code.tolist() == ["CSC108H1"]
    assert "学科：Data Science" in result.match_reason.iloc[0]
