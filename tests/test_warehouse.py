"""Warehouse score definitions, snapshot consistency, and empty-course regressions."""

import duckdb
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import recommender, warehouse


@pytest.fixture
def warehouse_input():
    courses = pd.DataFrame(
        {
            "course_id": [1, 2, 3],
            "course_code": ["A", "B", "C"],
            "course_name": ["Alpha", "Beta", "Gamma"],
            "department": ["Statistics"] * 3,
            "course_level": [100, 200, 300],
        }
    )
    reviews = pd.DataFrame(
        {
            "review_id": [1, 2, 3],
            "course_id": [1, 2, 2],
            "instructor_id": [1, 1, 1],
            "rating": [5.0, 3.0, 3.0],
            "difficulty": [2.0] * 3,
            "workload": [2.0] * 3,
            "usefulness": [4.0] * 3,
            "review_text": ["not heavy workload; Python project", "workload is manageable", "useful"],
        }
    )
    return courses, reviews


def _dws(conn, courses, reviews):
    conn.register("dwd_courses_clean", courses)
    conn.register("dwd_reviews_clean", reviews)
    conn.register(
        "dwd_instructors_clean",
        pd.DataFrame({"instructor_id": [1], "instructor_name": ["Teacher"], "department": ["Statistics"]}),
    )
    warehouse.build_dws_layer(conn)
    return conn.execute("SELECT * FROM dws_course_summary ORDER BY course_code").df()


def test_scores_are_bounded_smoothed_and_unreviewed_are_null(warehouse_input):
    courses, reviews = warehouse_input
    with duckdb.connect(":memory:") as conn:
        summary = _dws(conn, courses, reviews)
    profile = warehouse.build_course_profile(summary, reviews)
    assert profile.loc[0, "smoothed_rating"] == pytest.approx((5 + 10 * 11 / 3) / 11)
    assert profile.loc[0, "confidence"] == pytest.approx(1 / 11)
    assert profile.loc[2, "review_count"] == 0
    assert pd.isna(profile.loc[2, "avg_rating"])
    assert pd.isna(profile.loc[2, "recommend_score"])
    assert pd.isna(profile.loc[2, "gpa_friendly_score"])
    assert pd.isna(profile.loc[2, "positive_review_ratio"])
    assert profile.loc[0, "workload_negative_ratio"] == 0
    for name in ["gpa_friendly_score", "course_value_score", "workload_risk_score", "recommend_score"]:
        assert profile.loc[:1, name].between(1, 5).all()
    assert recommender.recommend_courses(recommendation_table=profile)["course_code"].tolist() == ["A", "B"]


def test_csv_fallback_and_warehouse_use_identical_formulas(warehouse_input, tmp_path, monkeypatch):
    courses, reviews = warehouse_input
    courses.to_csv(tmp_path / warehouse.PROCESSED_FILES["courses"], index=False)
    reviews.to_csv(tmp_path / warehouse.PROCESSED_FILES["reviews"], index=False)
    monkeypatch.setattr(recommender, "DUCKDB_PATH", tmp_path / "absent.duckdb")
    monkeypatch.setattr(recommender, "PROCESSED_DATA_DIR", tmp_path)
    fallback = recommender._load_course_profile()
    with duckdb.connect(":memory:") as conn:
        summary = _dws(conn, courses, reviews)
    expected = warehouse.build_course_profile(summary, reviews)
    assert_frame_equal(fallback[expected.columns], expected, check_dtype=False)


def test_all_courses_unreviewed_is_safe(warehouse_input):
    courses, reviews = warehouse_input
    reviews = reviews.iloc[:0]
    with duckdb.connect(":memory:") as conn:
        summary = _dws(conn, courses, reviews)
    profile = warehouse.build_course_profile(summary, reviews)
    assert profile["smoothed_rating"].eq(3).all()
    assert profile["confidence"].eq(0).all()
    assert recommender.recommend_courses(recommendation_table=profile).empty


def test_warehouse_failure_rolls_back_published_tables(tmp_path, monkeypatch):
    path = tmp_path / "published.duckdb"
    with duckdb.connect(str(path)) as conn:
        conn.execute("CREATE TABLE stable AS SELECT 1 AS version")
    monkeypatch.setattr(warehouse, "run_quality_report", lambda: pd.DataFrame())
    monkeypatch.setattr(warehouse, "assert_quality", lambda report: None)
    monkeypatch.setattr(warehouse, "init_duckdb", lambda: duckdb.connect(str(path)))
    monkeypatch.setattr(
        warehouse, "build_ods_layer", lambda conn: conn.execute("UPDATE stable SET version=2")
    )
    monkeypatch.setattr(
        warehouse, "build_dwd_layer", lambda conn: (_ for _ in ()).throw(RuntimeError("bad CSV"))
    )
    with pytest.raises(RuntimeError, match="bad CSV"):
        warehouse.build_warehouse()
    with duckdb.connect(str(path)) as conn:
        assert conn.execute("SELECT version FROM stable").fetchone()[0] == 1


def test_failed_gate_never_opens_the_warehouse(monkeypatch):
    monkeypatch.setattr(warehouse, "run_quality_report", lambda: pd.DataFrame())
    monkeypatch.setattr(
        warehouse, "assert_quality", lambda report: (_ for _ in ()).throw(ValueError("quality failed"))
    )
    monkeypatch.setattr(warehouse, "init_duckdb", lambda: pytest.fail("warehouse opened before gate"))
    with pytest.raises(ValueError, match="quality failed"):
        warehouse.build_warehouse()


def test_recommendation_tags_are_read_from_committed_database(warehouse_input, tmp_path, monkeypatch):
    courses, reviews = warehouse_input
    db_path = tmp_path / "snapshot.duckdb"
    tag_path = tmp_path / warehouse.PROCESSED_FILES["course_tags"]
    pd.DataFrame(
        {"course_id": [1, 2, 3], "tags": ["Project Based", "", ""], "keywords": ["python", "useful", ""]}
    ).to_csv(tag_path, index=False)
    pd.DataFrame({"status": ["PASS"]}).to_csv(
        tmp_path / warehouse.PROCESSED_FILES["data_quality"], index=False
    )
    monkeypatch.setattr(warehouse, "PROCESSED_DATA_DIR", tmp_path)
    with duckdb.connect(str(db_path)) as conn:
        _dws(conn, courses, reviews)
        warehouse.build_ads_layer(conn)
    # A later failed run may already have replaced CSV artifacts; published tags stay consistent.
    tag_path.unlink()
    monkeypatch.setattr(recommender, "DUCKDB_PATH", db_path)
    monkeypatch.setattr(recommender, "PROCESSED_DATA_DIR", tmp_path)
    table = recommender.build_recommendation_table()
    assert table.loc[table["course_id"] == 1, "tags"].item() == "Project Based"
    assert table["course_level"].tolist() == [100, 200, 300]
