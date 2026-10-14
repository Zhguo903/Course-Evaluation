"""Atomic pure official-data publication preserves requirements and removes old tables."""

import duckdb
import pandas as pd
import pytest

from src.data_quality import DataQualityError
from src.finder import load_finder_data
from src.warehouse import build_warehouse


def test_only_official_tables_are_published(tmp_path, official_sample, sample_manifest):
    path = tmp_path / "finder.duckdb"
    with duckdb.connect(str(path)) as conn:
        conn.execute("CREATE TABLE dwd_reviews_clean AS SELECT 'old simulated text' AS review_text")
    build_warehouse(
        support_snapshot={"reviews": [], "resources": [], "feedback_sources": []},
        support_manifest={},
        evaluations=[],
        evaluation_manifest={},
        courses=official_sample,
        catalog_manifest=sample_manifest,
        offerings=[],
        timetable_manifest={"coverage": [], "sessions": []},
        db_path=path,
    )
    data = load_finder_data(path)
    assert len(data["courses"]) == 3
    assert data["courses"].offering_status.eq("unknown").all()
    assert data["quality"].status.eq("PASS").all()
    with duckdb.connect(str(path)) as conn:
        tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    assert "dwd_reviews_clean" not in tables
    assert "ads_course_finder" in tables
    actual = data["courses"].set_index("course_code")
    for row in official_sample:
        assert actual.loc[row["course_code"], "prerequisite"] == row["prerequisite"]


def test_failed_validation_keeps_previous_database(tmp_path, official_sample, sample_manifest):
    path = tmp_path / "finder.duckdb"
    with duckdb.connect(str(path)) as conn:
        conn.execute("CREATE TABLE original AS SELECT 42 AS value")
    sample_manifest["complete"] = False
    with pytest.raises(DataQualityError):
        build_warehouse(
            support_snapshot={"reviews": [], "resources": [], "feedback_sources": []},
            support_manifest={},
            evaluations=[],
            evaluation_manifest={},
            courses=official_sample,
            catalog_manifest=sample_manifest,
            offerings=[],
            timetable_manifest={"coverage": []},
            db_path=path,
        )
    with duckdb.connect(str(path)) as conn:
        assert conn.execute("SELECT value FROM original").fetchone()[0] == 42


def test_build_error_keeps_previous_database(tmp_path, official_sample, sample_manifest, monkeypatch):
    path = tmp_path / "finder.duckdb"
    with duckdb.connect(str(path)) as conn:
        conn.execute("CREATE TABLE original AS SELECT 42 AS value")
    monkeypatch.setattr(pd.DataFrame, "to_csv", lambda *args, **kwargs: None)
    from src import warehouse

    monkeypatch.setattr(warehouse, "_frame", lambda *args: (_ for _ in ()).throw(RuntimeError("frame error")))
    with pytest.raises(RuntimeError, match="frame error"):
        build_warehouse(
            support_snapshot={"reviews": [], "resources": [], "feedback_sources": []},
            support_manifest={},
            evaluations=[],
            evaluation_manifest={},
            courses=official_sample,
            catalog_manifest=sample_manifest,
            offerings=[],
            timetable_manifest={"coverage": []},
            db_path=path,
        )
    with duckdb.connect(str(path)) as conn:
        assert conn.execute("SELECT value FROM original").fetchone()[0] == 42
    assert not list(tmp_path.glob(".course-finder-*"))


def test_full_real_feedback_and_link_metadata_publish_without_quality_ranking(tmp_path):
    from src.evaluations import load_evaluation_snapshot
    from src.support import load_support_snapshot

    support, _ = load_support_snapshot()
    evaluations, manifest = load_evaluation_snapshot()
    path = tmp_path / "real-feedback.duckdb"
    build_warehouse(db_path=path)
    data = load_finder_data(path)
    assert len(data["reviews"]) == len(support["reviews"])
    assert len(data["resources"]) == len(support["resources"])
    assert len(data["evaluations"]) == manifest["record_count"]
    assert data["courses"].historical_evaluation_count.sum() == manifest["matched_record_count"]
    assert data["evaluations"].course_code.eq("").sum() == manifest["unmatched_record_count"]
    assert data["courses"].student_review_count.sum() == len(support["reviews"])
    assert data["courses"].resource_count.sum() == sum(
        bool(row["course_code"]) for row in support["resources"]
    )
    assert not any("average_rating" in column or "quality_rank" in column for column in data["courses"])
    assert any("multiple_reports_same_cohort" in flags for flags in data["evaluations"].quality_flags)
    assert len(evaluations) > data["courses"].historical_evaluation_count.sum()
