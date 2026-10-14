"""The default runner only publishes verified snapshots; no generator path exists."""

import pandas as pd

import run_pipeline


def test_runner_calls_only_official_warehouse(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        run_pipeline,
        "build_warehouse",
        lambda: calls.append("official") or pd.DataFrame({"status": ["PASS"]}),
    )
    run_pipeline.main()
    assert calls == ["official"]
    assert "Published official" in capsys.readouterr().out
