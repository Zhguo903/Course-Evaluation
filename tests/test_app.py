"""Exercise user-visible dashboard states against an isolated published dataset."""

from pathlib import Path

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
    department = app.sidebar.multiselect[0].options[0]
    app.sidebar.multiselect[0].set_value([department]).run()
    assert not app.exception
    assert app.metric[0].value == "25"


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
