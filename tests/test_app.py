"""Exercise the official-only finder with a small, isolated real catalog sample."""

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import config
from src.catalog import load_catalog
from src.timetable import annotate_offerings, load_timetable_snapshot

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def write_index(db_path, courses, coverage):
    quality = pd.DataFrame([{"check_name": "official_course_code_unique", "status": "PASS"}])
    with duckdb.connect(str(db_path)) as conn:
        for table, frame in [
            ("ads_course_finder", courses),
            ("ads_timetable_coverage", coverage),
            ("ads_data_quality_report", quality),
        ]:
            conn.register("input_frame", frame)
            conn.execute(f"CREATE TABLE {table} AS SELECT * FROM input_frame")
            conn.unregister("input_frame")


@pytest.fixture(scope="module")
def finder_data(tmp_path_factory):
    records = pd.DataFrame(load_catalog())
    # These are real official records. Coverage is intentionally unavailable in this
    # fixture, so every offering annotation must remain unknown rather than invented.
    sample = records.groupby("campus", sort=False).head(8)
    multi = records.loc[records["breadth_categories"].map(lambda value: len(json.loads(value)) > 1)]
    sample = pd.concat([sample, multi.head(1)], ignore_index=True).drop_duplicates("course_code")
    sample["offering_status"] = "unknown"
    sample["offering_status_by_session"] = json.dumps({"20269": "unknown", "20271": "unknown"})
    sample["offered_sessions"] = "[]"
    sample["checked_sessions"] = "[]"
    sample["timetable_source_url"] = ""
    sample["timetable_retrieved_at"] = ""
    coverage = pd.DataFrame(
        [
            {
                "campus": campus,
                "session_code": session,
                "label": label,
                "complete": False,
                "retrieved_at": "",
                "source_url": "https://ttb.utoronto.ca/",
            }
            for campus in sample["campus"].unique()
            for session, label in [("20269", "Fall 2026"), ("20271", "Winter 2027")]
        ]
    )
    db_path = tmp_path_factory.mktemp("finder-ui") / "finder.duckdb"
    write_index(db_path, sample, coverage)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(config, "DUCKDB_PATH", db_path)
        st.cache_data.clear()
        yield {"courses": sample, "DUCKDB_PATH": db_path}
        st.cache_data.clear()


def dashboard():
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception, [exception.message for exception in app.exception]
    return app


def course_table(app):
    return next(frame.value for frame in app.dataframe if "课程代码 / Code" in frame.value)


def result_count_is(app, count):
    return any(f"找到 {count:,} 门课程" in item.value for item in app.markdown)


def test_defaults_show_all_official_courses_without_review_controls(finder_data):
    app = dashboard()
    assert len(app.tabs) == 2
    assert result_count_is(app, len(finder_data["courses"]))
    assert app.selectbox(key="session_filter").value is None
    assert not app.checkbox(key="only_offered").value
    assert not app.slider
    catalog = course_table(app)
    assert "匹配原因 / Why it matches" in catalog
    assert "官方课程目录" in catalog
    assert not any("评分" in column or "评论" in column for column in catalog.columns)


def test_empty_search_has_helpful_state(finder_data):
    app = dashboard()
    app.text_input(key="course_query").set_value("no-such-official-course-903").run()
    assert not app.exception
    assert result_count_is(app, 0)
    assert any("没有匹配课程" in item.value for item in app.info)


def test_department_and_level_filters_combine(finder_data):
    sample = finder_data["courses"]
    course = sample.iloc[0]
    app = dashboard()
    app.multiselect(key="department_filter").set_value([course["department"]])
    app.multiselect(key="level_filter").set_value([course["course_level"]]).run()
    assert not app.exception
    expected = sample.loc[
        sample["department"].eq(course["department"]) & sample["course_level"].eq(course["course_level"])
    ]
    assert result_count_is(app, len(expected))
    assert set(course_table(app)["课程代码 / Code"]) == set(expected["course_code"])


def test_campus_filter_preserves_official_codes_and_source(finder_data):
    app = dashboard()
    app.multiselect(key="campus_filter").set_value(["Mississauga"]).run()
    assert not app.exception
    catalog = course_table(app)
    assert catalog["校区 / Campus"].eq("Mississauga").all()
    assert catalog["课程代码 / Code"].str.endswith("5").all()
    assert catalog["官方课程目录"].str.startswith("https://utm.calendar.utoronto.ca/").all()


def test_breadth_matches_each_category_of_multi_category_courses(finder_data):
    sample = finder_data["courses"]
    parsed = sample["breadth_categories"].map(json.loads)
    multi = sample.loc[parsed.map(len).gt(1)].iloc[0]
    for category in json.loads(multi["breadth_categories"]):
        app = dashboard()
        option = next(
            label
            for label in app.multiselect(key="classification_filter").options
            if label.startswith(f"St. George · BR {category} ·")
        )
        app.multiselect(key="classification_filter").set_value([option]).run()
        assert not app.exception
        expected = sample.loc[parsed.map(lambda values: category in values)]
        assert set(course_table(app)["课程代码 / Code"]) == set(expected["course_code"])
        assert multi["course_code"] in set(course_table(app)["课程代码 / Code"])


@pytest.mark.parametrize(
    "prefix,campus",
    [
        ("UTM · Distribution ·", "Mississauga"),
        ("UTSC · Breadth ·", "Scarborough"),
    ],
)
def test_other_campus_categories_do_not_map_to_st_george_br(finder_data, prefix, campus):
    app = dashboard()
    option = next(
        label for label in app.multiselect(key="classification_filter").options if label.startswith(prefix)
    )
    app.multiselect(key="classification_filter").set_value([option]).run()
    assert not app.exception
    assert course_table(app)["校区 / Campus"].eq(campus).all()


def test_unknown_offerings_are_visible_and_never_treated_as_not_found(finder_data):
    app = dashboard()
    assert course_table(app)["所选学期开课记录"].eq("未核验 / Unknown").all()
    app.selectbox(key="session_filter").set_value("20269").run()
    assert not app.exception
    assert course_table(app)["所选学期开课记录"].eq("未核验 / Unknown").all()
    app.checkbox(key="only_offered").set_value(True).run()
    assert not app.exception
    assert result_count_is(app, 0)


def test_exact_course_lookup_shows_official_requirements_and_sources(finder_data):
    sample = finder_data["courses"]
    course = sample.loc[sample["prerequisite"].fillna("").str.len().gt(0)].iloc[0]
    app = dashboard()
    app.text_input(key="course_query").set_value(course["course_code"]).run()
    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    captions = "\n".join(item.value for item in app.caption)
    assert course["prerequisite"] in markdown
    assert f"[查看该课程的官方目录]({course['source_url']})" in markdown
    assert str(course["source_retrieved_at"]) in captions
    assert "不自动判断先修资格" in captions
    assert any("不能据此判断是否开课" in item.value for item in app.info)


def test_actual_published_offering_has_source_and_selectable_session(monkeypatch, tmp_path):
    catalog = {row["course_code"]: row for row in load_catalog()}
    offerings, manifest = load_timetable_snapshot()
    actual = next(row for row in offerings if row["status"] == "offered" and row["course_code"] in catalog)
    course = catalog[actual["course_code"]]
    annotated = annotate_offerings([course], offerings, manifest)[0]
    annotated["offering_status_by_session"] = json.dumps(
        {
            row["session_code"]: annotate_offerings([course], offerings, manifest, row["session_code"])[0][
                "offering_status"
            ]
            for row in manifest["sessions"]
        }
    )
    db_path = tmp_path / "actual-offering.duckdb"
    write_index(db_path, pd.DataFrame([annotated]), pd.DataFrame(manifest["coverage"]))
    monkeypatch.setattr(config, "DUCKDB_PATH", db_path)
    st.cache_data.clear()
    app = dashboard()
    app.selectbox(key="session_filter").set_value(actual["session_code"])
    app.checkbox(key="only_offered").set_value(True).run()
    assert not app.exception
    assert result_count_is(app, 1)
    assert course_table(app)["所选学期开课记录"].eq("课表已列出").all()
    assert any(annotated["timetable_source_url"] in item.value for item in app.markdown)
    assert any(annotated["timetable_checked_at"] in item.value for item in app.caption)


def test_pagination_and_comparison_use_current_official_results(finder_data):
    app = dashboard()
    assert len(course_table(app)) <= 20
    codes = finder_data["courses"]["course_code"].head(2).tolist()
    app.multiselect(key="compare_courses").set_value(codes).run()
    assert not app.exception
    comparison = next(frame.value for frame in app.dataframe if "先修要求 / Prerequisite" in frame.value)
    assert set(comparison["课程代码 / Code"]) == set(codes)
    assert len(app.get("download_button")) == 2
    first_page_codes = set(course_table(app)["课程代码 / Code"])
    app.number_input(key="results_page").set_value(2).run()
    assert not app.exception
    assert not first_page_codes.intersection(course_table(app)["课程代码 / Code"])
    app.text_input(key="course_query").set_value(codes[0]).run()
    assert not app.exception
    assert app.number_input(key="results_page").value == 1
    assert result_count_is(app, 1)


def test_missing_index_has_explicit_offline_build(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp_path / "missing.duckdb")
    st.cache_data.clear()
    app = dashboard()
    assert any("构建官方课程索引" in button.label for button in app.button)
    assert not (tmp_path / "missing.duckdb").exists()
