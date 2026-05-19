"""Shared utility helpers for CourseInsight."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


def log_step(message: str) -> None:
    """Print a compact timestamped pipeline log message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV file with a consistent log-friendly wrapper."""
    return pd.read_csv(path, **kwargs)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV and ensure the parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def join_non_empty(values: Iterable[str], sep: str = ", ") -> str:
    """Join non-empty string values into a display-ready string."""
    return sep.join(str(value) for value in values if str(value).strip())
