"""Exercise the official-only finder with a small, isolated real catalog sample."""

import json
import io
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage

from src import config, finder
from src.catalog import load_catalog
from src.evaluations import load_evaluation_snapshot
from src.timetable import annotate_offerings, load_timetable_snapshot

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
REFERENCE_DIR = APP.parents[1] / "data" / "reference"


@pytest.fixture(scope="module")
def feedback_snapshot():
    evaluations, _ = load_evaluation_snapshot()
    return {
        "reviews": pd.DataFrame(json.loads((REFERENCE_DIR / "student_reviews.json").read_text())),
        "resources": pd.DataFrame(json.loads((REFERENCE_DIR / "course_resources.json").read_text())),
        "feedback_sources": pd.DataFrame(json.loads((REFERENCE_DIR / "feedback_sources.json").read_text())),
        "evaluations": pd.DataFrame(evaluations),
    }


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
def finder_data(tmp_path_factory, feedback_snapshot):
    records = pd.DataFrame(load_catalog())
    # These are real official records. Coverage is intentionally unavailable in this
    # fixture, so every offering annotation must remain unknown rather than invented.
    sample = records.groupby("campus", sort=False).head(8)
    multi = records.loc[records["breadth_categories"].map(lambda value: len(json.loads(value)) > 1)]
    missing_score = (
        feedback_snapshot["evaluations"]
        .loc[
            feedback_snapshot["evaluations"]["workload_score"].isna()
            & feedback_snapshot["evaluations"]["course_code"].ne("")
        ]
        .iloc[0]["course_code"]
    )
    resource_counts = (
        feedback_snapshot["resources"]
        .loc[feedback_snapshot["resources"]["course_code"].fillna("").ne("")]
        .groupby("course_code")
        .size()
    )
    most_resources_code = resource_counts.idxmax()
    extra_codes = [
        "CSC110Y1",
        "CSC165H1",
        "MAT223H1",
        "CSCA08H3",
        "RSM430H1",
        missing_score,
        most_resources_code,
    ]
    extras = records.loc[records["course_code"].isin(extra_codes)]
    sample = pd.concat([sample, multi.head(1), extras], ignore_index=True).drop_duplicates("course_code")
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


@pytest.fixture
def feedback_data(monkeypatch, finder_data, feedback_snapshot):
    original = finder.load_finder_data
    injected = {key: value.copy() for key, value in feedback_snapshot.items()}

    def load_with_feedback(db_path=None):
        loaded = original(db_path=db_path)
        loaded.update(injected)
        loaded["courses"] = loaded["courses"].copy()
        for table, column in [
            ("reviews", "student_review_count"),
            ("evaluations", "historical_evaluation_count"),
            ("resources", "resource_count"),
        ]:
            counts = injected[table].groupby("course_code").size()
            loaded["courses"][column] = loaded["courses"]["course_code"].map(counts).fillna(0).astype(int)
        return loaded

    monkeypatch.setattr(finder, "load_finder_data", load_with_feedback)
    st.cache_data.clear()
    yield injected
    st.cache_data.clear()


def dashboard():
    app = AppTest.from_file(str(APP)).run(timeout=45)
    assert not app.exception, [exception.message for exception in app.exception]
    assert not any(item.value == "None" for item in app.markdown)
    return app


def course_table(app):
    return next(frame.value for frame in app.dataframe if "课程代码 / Code" in frame.value)


def result_count_is(app, count):
    return any(f"找到 {count:,} 门课程" in item.value for item in app.markdown)


def test_defaults_show_all_official_courses_without_review_controls(finder_data):
    app = dashboard()
    assert len(app.tabs) == 3
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


def test_feedback_tab_missing_records_is_unknown_not_a_low_score(finder_data):
    app = dashboard()
    assert any("尚无已导入的公开学生评价" in item.value for item in app.info)
    assert any("尚无已导入且能准确关联" in item.value for item in app.info)
    assert app.selectbox(key="feedback_course").value == app.selectbox(key="detail_course").value
    assert not app.metric


def test_student_review_keeps_actual_scale_source_and_author(feedback_data):
    review = feedback_data["reviews"].iloc[0]
    app = dashboard()
    app.text_input(key="course_query").set_value(review["course_code"]).run()
    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    captions = "\n".join(item.value for item in app.caption)
    assert review["summary"] in markdown
    assert review["reviewer_label"] in markdown
    assert "作者个人推荐程度" in markdown and "原始尺度 1–10" in markdown
    assert review["academic_period"] in captions
    assert "公开自述；未核验作者选课身份" in captions
    assert review["source_url"] in [item.proto.url for item in app.get("link_button")]
    assert not app.metric


def test_history_shows_recent_fifty_reports_and_its_own_export(feedback_data):
    app = dashboard()
    app.text_input(key="course_query").set_value("MAT223H1").run()
    assert not app.exception
    history = next(frame.value for frame in app.dataframe if "总体学习体验（1–5）" in frame.value)
    expected = feedback_data["evaluations"].loc[feedback_data["evaluations"]["course_code"].eq("MAT223H1")]
    assert len(expected) > 50 and len(history) == 50
    assert history["历史年份"].is_monotonic_decreasing
    assert any(f"已导入 {len(expected):,} 条历史报告" in item.value for item in app.markdown)
    assert any("不能相加当作独立学生人数" in item.value for item in app.caption)
    assert any("第三方公开整理的历史官方评价结果副本" in item.value for item in app.caption)
    assert any(item.proto.label == "下载本课完整历史评价 CSV" for item in app.get("download_button"))


def test_history_preserves_missing_scores_and_source_anomaly(feedback_data):
    evaluations = feedback_data["evaluations"]
    missing = evaluations.loc[evaluations["workload_score"].isna() & evaluations["course_code"].ne("")].head(
        1
    )
    feedback_data["evaluations"] = missing
    st.cache_data.clear()
    app = dashboard()
    app.text_input(key="course_query").set_value(missing.iloc[0]["course_code"]).run()
    assert not app.exception
    history = next(frame.value for frame in app.dataframe if "总体学习体验（1–5）" in frame.value)
    assert history["工作量（1–5，非难度）"].isna().all()
    feedback_data["evaluations"] = evaluations
    st.cache_data.clear()
    app = dashboard()
    app.text_input(key="course_query").set_value("RSM430H1").run()
    assert not app.exception
    assert any("回答数高于受邀数" in item.value for item in app.warning)


def test_resources_show_login_history_and_campus_scope(feedback_data):
    app = dashboard()
    app.text_input(key="course_query").set_value("CSCA08H3").run()
    assert not app.exception
    assert any("需 UTORid 登录" in item.value for item in app.caption)
    urls = [item.proto.url for item in app.get("link_button")]
    other_campus = feedback_data["resources"].loc[feedback_data["resources"]["course_code"].eq("CSC110Y1")]
    assert not set(other_campus["url"]).intersection(urls)
    app.text_input(key="course_query").set_value("CSC165H1").run()
    assert not app.exception
    assert any("历史资料 · 资料对应学期/年份：Fall 2019" in item.value for item in app.caption)
    sources = next(frame.value for frame in app.dataframe if "接入状态" in frame.value)
    assert "需登录的外部入口，未导入记录" in set(sources["接入状态"])
    assert "需授权，未导入记录" in set(sources["接入状态"])


def test_feedback_selection_follows_details_then_can_be_independent(feedback_data):
    app = dashboard()
    codes = app.selectbox(key="detail_course").options
    first_code = app.selectbox(key="detail_course").value
    next_code = next(
        code for code in app.selectbox(key="feedback_course").options if not code.startswith(first_code)
    )
    # Selectbox values are raw course codes even though displayed options contain names.
    raw_next = next_code.split(" · ")[0]
    app.selectbox(key="detail_course").set_value(raw_next).run()
    assert not app.exception
    assert app.selectbox(key="feedback_course").value == raw_next
    independent = next(code.split(" · ")[0] for code in codes if not code.startswith(raw_next))
    app.selectbox(key="feedback_course").set_value(independent).run()
    assert not app.exception
    assert app.selectbox(key="feedback_course").value == independent
    assert app.selectbox(key="detail_course").value == raw_next


def test_feedback_links_reject_non_https_urls(feedback_data):
    course_code = feedback_data["reviews"].iloc[0]["course_code"]
    feedback_data["reviews"].loc[:, "source_url"] = "javascript:alert(1)"
    feedback_data["resources"].loc[:, "url"] = "http://example.invalid/"
    feedback_data["resources"].loc[:, "source_url"] = "https://user:password@example.invalid/"
    feedback_data["feedback_sources"].loc[:, "source_url"] = "data:text/html,unsafe"
    st.cache_data.clear()
    app = dashboard()
    app.text_input(key="course_query").set_value(course_code).run()
    assert not app.exception
    assert not app.get("link_button")
    sources = next(frame.value for frame in app.dataframe if "接入状态" in frame.value)
    assert sources["来源入口"].eq("").all()


def test_optional_feedback_and_resource_filters_use_associated_records(feedback_data):
    app = dashboard()
    app.checkbox(key="only_resources").set_value(True).run()
    assert not app.exception
    codes = set(course_table(app)["课程代码 / Code"])
    assert codes
    assert codes.issubset(set(feedback_data["resources"]["course_code"]) - {""})
    app.checkbox(key="only_resources").set_value(False)
    app.checkbox(key="only_feedback").set_value(True).run()
    assert not app.exception
    reviews = set(feedback_data["reviews"]["course_code"])
    historical = set(feedback_data["evaluations"]["course_code"]) - {""}
    assert set(course_table(app)["课程代码 / Code"]).issubset(reviews | historical)


def most_resources_course(feedback_data):
    resources = feedback_data["resources"]
    specific = resources.loc[resources["course_code"].fillna("").ne("")]
    return specific.groupby("course_code").size().idxmax()


def displayed_resource_urls(app):
    return [item.proto.url for item in app.get("link_button") if item.proto.label == "打开学习资料入口 ↗"]


def test_resource_type_and_literal_title_filters_use_real_course_links(feedback_data):
    code = most_resources_course(feedback_data)
    resources = feedback_data["resources"]
    actual = resources.loc[resources["course_code"].eq(code)]
    resource = actual.iloc[0]
    app = dashboard()
    app.text_input(key="course_query").set_value(code).run()
    assert not app.exception
    assert app.multiselect(key="resource_type_filter").value == []
    app.multiselect(key="resource_type_filter").set_value([resource["resource_type"]]).run()
    app.text_input(key="resource_title_query").set_value(resource["title"]).run()
    assert not app.exception
    expected = actual.loc[
        actual["resource_type"].eq(resource["resource_type"])
        & actual["title"].str.contains(resource["title"], case=False, regex=False)
    ]
    # Generic portals do not match the full title of this real course resource.
    assert set(displayed_resource_urls(app)) == set(expected["url"])
    assert resource["url"] in displayed_resource_urls(app)
    assert any("顺序不代表质量评分" in item.value for item in app.caption)


def test_empty_resource_search_has_clear_action_and_retains_full_export(feedback_data):
    code = most_resources_course(feedback_data)
    app = dashboard()
    app.text_input(key="course_query").set_value(code).run()
    app.text_input(key="resource_title_query").set_value("no-such-public-resource-903").run()
    assert not app.exception
    assert displayed_resource_urls(app) == []
    assert any("没有符合资料筛选的本课条目" in item.value for item in app.info)
    assert any(button.proto.label == "下载本课完整学习资料 CSV" for button in app.get("download_button"))
    app.button(key="clear_resource_filters").click().run()
    assert not app.exception
    assert app.text_input(key="resource_title_query").value == ""
    assert app.multiselect(key="resource_type_filter").value == []
    assert displayed_resource_urls(app)


def capture_resource_downloads(monkeypatch):
    captured = {}
    original = MemoryMediaFileStorage.load_and_get_id

    def capture(self, path_or_data, mimetype, kind, filename=None):
        if filename and filename.endswith("_learning_resources.csv"):
            captured[filename] = path_or_data
        return original(self, path_or_data, mimetype, kind, filename)

    monkeypatch.setattr(MemoryMediaFileStorage, "load_and_get_id", capture)
    return captured


def test_full_resource_csv_contains_all_actual_course_metadata_even_when_display_is_filtered(
    feedback_data, monkeypatch
):
    captured = capture_resource_downloads(monkeypatch)
    code = most_resources_course(feedback_data)
    actual = feedback_data["resources"].loc[feedback_data["resources"]["course_code"].eq(code)]
    app = dashboard()
    app.text_input(key="course_query").set_value(code).run()
    app.text_input(key="resource_title_query").set_value("no-such-public-resource-903").run()
    assert not app.exception
    exported = pd.read_csv(io.BytesIO(captured[f"{code}_learning_resources.csv"]))
    assert len(exported) == len(actual)
    assert set(exported["resource_id"]) == set(actual["resource_id"])
    assert set(exported["url"]) == set(actual["url"])
    assert exported["course_code"].eq(code).all()
    assert set(exported["campus"]) == set(actual["campus"])
    assert not any(column.startswith("_resource_") for column in exported)


def test_resource_display_limit_preserves_all_rows_in_download(feedback_data):
    code = most_resources_course(feedback_data)
    resources = feedback_data["resources"]
    actual = resources.loc[resources["course_code"].eq(code)]
    campus = actual.iloc[0]["campus"]
    generic = resources.loc[
        resources["course_code"].fillna("").eq("") & resources["campus"].isin([campus, "All"])
    ]
    app = dashboard()
    app.text_input(key="course_query").set_value(code).run()
    assert not app.exception
    assert len(displayed_resource_urls(app)) == min(20, len(actual)) + min(20, len(generic))
    assert any(f"本课共 {len(actual):,} 条专属资料" in item.value for item in app.caption)
    assert any("最多展示 20 条" in item.value for item in app.caption)
    assert any(button.proto.label == "下载本课完整学习资料 CSV" for button in app.get("download_button"))


def test_resource_filters_reset_for_a_different_course(feedback_data):
    app = dashboard()
    app.text_input(key="resource_title_query").set_value("selected-resource-keyword").run()
    first = app.selectbox(key="feedback_course").value
    other = next(
        option.split(" · ")[0]
        for option in app.selectbox(key="feedback_course").options
        if not option.startswith(first)
    )
    app.selectbox(key="feedback_course").set_value(other).run()
    assert not app.exception
    assert app.text_input(key="resource_title_query").value == ""
    assert app.multiselect(key="resource_type_filter").value == []


def test_twenty_card_limit_with_repeated_verified_rows_only_in_an_isolated_ui_fixture(
    feedback_data, monkeypatch
):
    code = most_resources_course(feedback_data)
    actual = feedback_data["resources"].loc[feedback_data["resources"]["course_code"].eq(code)]
    # Repeat already verified metadata solely to stress the card limit. No new
    # URLs, periods or course associations are invented; no fixture is published.
    stress = pd.concat([actual] * 25, ignore_index=True).head(25)
    feedback_data["resources"] = stress
    captured = capture_resource_downloads(monkeypatch)
    st.cache_data.clear()
    app = dashboard()
    app.text_input(key="course_query").set_value(code).run()
    assert not app.exception
    assert len(displayed_resource_urls(app)) == 20
    exported = pd.read_csv(io.BytesIO(captured[f"{code}_learning_resources.csv"]))
    assert len(exported) == 25
    assert exported["course_code"].eq(code).all()
    assert set(exported["url"]).issubset(set(actual["url"]))


def test_coverage_expander_counts_courses_per_campus_not_reports_or_resources(feedback_data, finder_data):
    app = dashboard()
    coverage = next(frame.value for frame in app.dataframe if "目录课程数" in frame.value)
    catalogue = finder_data["courses"]
    assert coverage["目录课程数"].sum() == len(catalogue.drop_duplicates(["campus", "course_code"]))
    for _, row in coverage.iterrows():
        campus_codes = set(catalogue.loc[catalogue["campus"].eq(row["校区"]), "course_code"])
        evaluations = feedback_data["evaluations"]
        expected = evaluations.loc[evaluations["campus"].eq(row["校区"]), "course_code"]
        assert row["有历史评价的课程"] == len(campus_codes.intersection(expected))
        resources = feedback_data["resources"]
        expected_resources = resources.loc[resources["campus"].eq(row["校区"]), "course_code"]
        assert row["有专属资料的课程"] == len(campus_codes.intersection(expected_resources))
    app.multiselect(key="campus_filter").set_value(["Mississauga"]).run()
    unchanged = next(frame.value for frame in app.dataframe if "目录课程数" in frame.value)
    pd.testing.assert_frame_equal(coverage, unchanged)
