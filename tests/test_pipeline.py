"""Publication gate regressions: failed validation must never publish a warehouse."""

import pandas as pd
import pytest

import run_pipeline
from src.data_quality import DataQualityError


def _fake_steps(monkeypatch, report):
    events = []
    for name in ["generate_all", "run_etl", "generate_course_tags", "build_warehouse"]:
        monkeypatch.setattr(run_pipeline, name, lambda step=name: events.append(step))

    def quality():
        events.append("save_quality_report")
        return report

    monkeypatch.setattr(run_pipeline, "run_data_quality", quality)
    return events


def test_quality_failure_stops_before_tags_and_warehouse(monkeypatch):
    report = pd.DataFrame(
        [{"check_name": "rating_range", "status": "FAIL", "failed_count": 1, "total_count": 4}]
    )
    events = _fake_steps(monkeypatch, report)
    with pytest.raises(DataQualityError):
        run_pipeline.main()
    assert events == ["generate_all", "run_etl", "save_quality_report"]


def test_skip_generate_reuses_inputs_after_passing_quality(monkeypatch):
    report = pd.DataFrame(
        [{"check_name": "rating_range", "status": "PASS", "failed_count": 0, "total_count": 4}]
    )
    events = _fake_steps(monkeypatch, report)
    run_pipeline.main(generate=False)
    assert events == ["run_etl", "save_quality_report", "generate_course_tags", "build_warehouse"]
