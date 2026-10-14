"""Exercise user-visible dashboard states against an isolated published dataset."""

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import config, data_quality, etl, generate_mock_data, nlp_tags, recommender, warehouse

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


@pytest.fixture(scope="module")
def dashboard_data(tmp_path_factory):
    root = tmp_path_factory.mktemp("dashboard")
    paths = {
        "DATA_DIR": root,
        "RAW_DATA_DIR": root / "raw",
        "PROCESSED_DATA_DIR": root / "processed",
        "WAREHOUSE_DIR": root / "warehouse",
        "DUCKDB_PATH": root / "warehouse" / "course_insight.duckdb",
    }
    with pytest.MonkeyPatch.context() as patch:
        for module in [config, data_quality, etl, generate_mock_data, nlp_tags, recommender, warehouse]:
            for name, value in paths.items():
                if hasattr(module, name):
                    patch.setattr(module, name, value)
        import run_pipeline

        run_pipeline.main()
        st.cache_data.clear()
        yield paths
        st.cache_data.clear()


def dashboard():
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception, [exception.message for exception in app.exception]
    return app


def published_courses(paths):
    with duckdb.connect(str(paths["DUCKDB_PATH"]), read_only=True) as conn:
        return conn.execute("SELECT * FROM ads_course_profile").df()


def catalog_frame(app):
    return next(
        frame.value
        for frame in app.dataframe
        if "课程代码 / Code" in frame.value and "实用性 / Usefulness" in frame.value
    )


def test_all_pages_render_with_published_data(dashboard_data):
    app = dashboard()
    assert len(app.tabs) == 6
    assert app.metric[0].value == "200"
    assert app.metric[1].value == "12,000"
    assert len(app.get("download_button")) >= 4


def test_empty_search_has_helpful_state(dashboard_data):
    app = dashboard()
    app.text_input[0].set_value("definitely-no-course-903").run()
    assert not app.exception
    assert any("没有匹配课程" in item.value for item in app.info)


def test_department_filter_limits_catalog(dashboard_data):
    app = dashboard()
    department = app.multiselect(key="department_filter").options[0]
    app.multiselect(key="department_filter").set_value([department]).run()
    assert not app.exception
    expected = published_courses(dashboard_data)["department"].eq(department).sum()
    assert app.metric[0].value == str(expected)
    assert catalog_frame(app)["院系 / Department"].eq(department).all()


def test_campus_filter_preserves_official_course_codes(dashboard_data):
    app = dashboard()
    app.multiselect(key="campus_filter").set_value(["Mississauga"]).run()
    assert not app.exception
    assert app.metric[0].value == "60"
    catalog = catalog_frame(app)
    assert catalog["校区 / Campus"].eq("Mississauga").all()
    assert catalog["课程代码 / Code"].str.endswith("5").all()
    assert catalog["官方目录 / Official calendar"].str.startswith("https://utm.calendar.utoronto.ca/").all()


def test_breadth_filter_matches_each_category_of_multi_category_courses(dashboard_data):
    courses = published_courses(dashboard_data)
    parsed = courses["breadth_categories"].map(json.loads)
    multi = courses.loc[parsed.map(len).gt(1)].iloc[0]
    for category in json.loads(multi["breadth_categories"]):
        app = dashboard()
        option = next(
            label
            for label in app.multiselect(key="classification_filter").options
            if label.startswith(f"St. George · BR {category} ·")
        )
        app.multiselect(key="classification_filter").set_value([option]).run()
        assert not app.exception
        catalog = catalog_frame(app)
        expected = courses.loc[parsed.map(lambda values: category in values)]
        assert set(catalog["课程代码 / Code"]) == set(expected["course_code"])
        assert multi["course_code"] in set(catalog["课程代码 / Code"])
        assert catalog["校区 / Campus"].eq("St. George").all()


@pytest.mark.parametrize(
    "system,prefix,campus",
    [
        ("utm_distribution", "UTM · Distribution ·", "Mississauga"),
        ("utsc_breadth", "UTSC · Breadth ·", "Scarborough"),
    ],
)
def test_campus_categories_keep_their_own_system(dashboard_data, system, prefix, campus):
    app = dashboard()
    option = next(
        label for label in app.multiselect(key="classification_filter").options if label.startswith(prefix)
    )
    app.multiselect(key="classification_filter").set_value([option]).run()
    assert not app.exception
    category = option.removeprefix(prefix).strip()
    courses = published_courses(dashboard_data)
    expected = courses.loc[
        courses["requirement_system"].eq(system)
        & courses["requirement_categories"].map(lambda value: category in json.loads(value))
    ]
    catalog = catalog_frame(app)
    assert set(catalog["课程代码 / Code"]) == set(expected["course_code"])
    assert catalog["校区 / Campus"].eq(campus).all()


def test_profile_preserves_official_requirements_and_sources(dashboard_data):
    courses = published_courses(dashboard_data)
    course = courses.loc[courses["prerequisite"].fillna("").str.len().gt(0)].iloc[0]
    app = dashboard()
    app.selectbox(key="profile_course").set_value(course["course_code"]).run()
    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    captions = "\n".join(item.value for item in app.caption)
    assert course["prerequisite"] in markdown
    for field in [
        "corequisite",
        "exclusion",
        "recommended_preparation",
        "enrolment_requirements",
        "requirement_notes",
    ]:
        if pd.notna(course.get(field)) and course.get(field):
            assert course[field] in markdown
    assert f"[查看该课程的官方目录]({course['source_url']})" in markdown
    assert str(course["source_retrieved_at"]) in captions
    assert "不自动判断先修资格" in captions
    assert any("不是群聊原文或真实评论摘录" in item.value for item in app.info)
    assert any("模拟学习体验" in item.value for item in app.subheader)


def test_preferences_rerank_and_explain(dashboard_data):
    app = dashboard()
    app.checkbox[2].set_value(True).run()
    assert not app.exception
    matching = [frame.value for frame in app.dataframe if "推荐理由 / Why this course" in frame.value]
    assert matching
    recommendations = matching[0]
    assert recommendations["偏好匹配分 / Preference score"].is_monotonic_decreasing
    assert recommendations["推荐理由 / Why this course"].str.len().gt(0).all()


def test_latest_failed_report_keeps_last_published_snapshot(dashboard_data):
    quality_path = dashboard_data["PROCESSED_DATA_DIR"] / config.PROCESSED_FILES["data_quality"]
    original = quality_path.read_bytes()
    try:
        report = pd.read_csv(quality_path)
        report.loc[0, "status"] = "FAIL"
        report.to_csv(quality_path, index=False)
        # An invalid intermediate CSV must not change the dashboard's published review count.
        reviews_path = dashboard_data["PROCESSED_DATA_DIR"] / config.PROCESSED_FILES["reviews"]
        reviews_original = reviews_path.read_bytes()
        try:
            pd.read_csv(reviews_path).head(1).to_csv(reviews_path, index=False)
            app = dashboard()
            assert app.metric[1].value == "12,000"
            assert any("上一次成功发布" in item.value for item in app.warning)
        finally:
            reviews_path.write_bytes(reviews_original)
    finally:
        quality_path.write_bytes(original)


def test_missing_database_shows_explicit_setup(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp_path / "missing.duckdb")
    st.cache_data.clear()
    app = dashboard()
    assert any("生成演示数据" in button.label for button in app.button)
    assert not (tmp_path / "missing.duckdb").exists()
