"""Fast, explainable filtering of official course data; no quality prediction."""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import pandas as pd

from src.config import DUCKDB_PATH

BR_NAMES = {
    1: "Creative and Cultural Representations",
    2: "Thought, Belief and Behaviour",
    3: "Society and its Institutions",
    4: "Living Things and Their Environment",
    5: "The Physical and Mathematical Universes",
}
STATUS_LABELS = {
    "offered": "已发布开课",
    "cancelled": "已取消",
    "not_found": "已发布课表中未找到",
    "unknown": "尚未核实",
}


def _text(value: object) -> str:
    return "" if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)) else str(value)


def _json(value: object, default):
    if isinstance(value, type(default)):
        return value
    try:
        decoded = json.loads(_text(value))
    except (TypeError, ValueError):
        return default
    return decoded if isinstance(decoded, type(default)) else default


def course_categories(row: pd.Series | dict) -> list[str]:
    """Classification labels are explicitly scoped to their campus system."""
    system = row.get("requirement_system", "")
    if system == "artsci_breadth":
        return [
            f"St. George · BR {number} · {BR_NAMES[number]}"
            for number in _json(row.get("breadth_categories"), [])
            if type(number) is int and number in BR_NAMES
        ]
    prefix = {"utm_distribution": "UTM · Distribution", "utsc_breadth": "UTSC · Breadth"}.get(system)
    return [f"{prefix} · {label}" for label in _json(row.get("requirement_categories"), [])] if prefix else []


def course_departments(row: pd.Series | dict) -> list[str]:
    """All official academic-area memberships, or the explicit prefix fallback."""
    areas = _json(row.get("subject_areas"), [])
    return areas or ([_text(row.get("department"))] if _text(row.get("department")) else [])


def available_sessions(coverage: pd.DataFrame) -> list[tuple[str, str]]:
    """Read published session choices from the source, never from guessed dates."""
    if coverage.empty or "session_code" not in coverage:
        return []
    options = {}
    for row in coverage.to_dict("records"):
        code = _text(row.get("session_code"))
        if code:
            options[code] = _text(row.get("label")) or code
    return sorted(options.items(), reverse=True)


def load_finder_data(db_path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Read every table from a single successfully published database snapshot."""
    with duckdb.connect(str(db_path or DUCKDB_PATH), read_only=True) as conn:
        conn.execute("BEGIN TRANSACTION")
        result = {
            "courses": conn.execute("SELECT * FROM ads_course_finder ORDER BY course_code").df(),
            "coverage": conn.execute("SELECT * FROM ads_timetable_coverage").df(),
            "quality": conn.execute("SELECT * FROM ads_data_quality_report").df(),
        }
        conn.execute("COMMIT")
    return result


def _timetable_link(row: pd.Series, session: str | None) -> str:
    """Link to evidence for the displayed state and selected session."""
    state = row.get("offering_status")
    if state not in {"offered", "cancelled"}:
        return "https://ttb.utoronto.ca/"
    for offering in _json(row.get("offering_sessions"), []):
        code = str(offering.get("session", ""))
        matches = session is None or code == session or ("-" not in session and session in code.split("-"))
        if matches and offering.get("status") == state:
            return offering.get("source_url") or "https://ttb.utoronto.ca/"
    return "https://ttb.utoronto.ca/"


def filter_courses(
    courses: pd.DataFrame,
    *,
    campuses=None,
    levels=None,
    departments=None,
    categories=None,
    query: str = "",
    offering_status: str | None = None,
    session: str | None = None,
) -> pd.DataFrame:
    """AND across filters, OR within each; keyword order is relevance, not course quality."""
    table = courses.copy()
    table["selected_session"] = session or "all_published"
    if table.empty:
        table["match_reason"] = pd.Series(dtype="str")
        return table
    for field, choices in [("campus", campuses), ("course_level", levels)]:
        if choices:
            table = table[table[field].isin(choices)].copy()
    if departments and not table.empty:
        table = table[
            table.apply(lambda row: bool(set(departments).intersection(course_departments(row))), axis=1)
        ].copy()
    if table.empty:
        table["match_reason"] = pd.Series(index=table.index, dtype="str")
        return table.reset_index(drop=True)
    labels = table.apply(course_categories, axis=1)
    if categories:
        wanted = set(categories)
        table = table[labels.map(lambda values: bool(wanted.intersection(values)))].copy()
        labels = labels.loc[table.index]
    if session:
        table["offering_status"] = table.get(
            "offering_status_by_session", pd.Series("{}", index=table.index)
        ).map(lambda value: _json(value, {}).get(str(session), "unknown"))
    if "offering_status" not in table:
        table["offering_status"] = "unknown"
    table["offering_status"] = table["offering_status"].fillna("unknown")
    if offering_status:
        table = table[table["offering_status"].eq(offering_status)].copy()
        labels = labels.loc[table.index]
    if not table.empty:
        table["timetable_source_url"] = table.apply(lambda row: _timetable_link(row, session), axis=1)
    terms = re.findall(r"\S+", query.strip().casefold())
    text_fields = [
        name
        for name in [
            "course_code",
            "course_name",
            "description",
            "department",
            "subject_areas",
            "prerequisite",
            "corequisite",
            "exclusion",
            "recommended_preparation",
            "enrolment_requirements",
            "requirement_notes",
        ]
        if name in table
    ]
    if terms and not table.empty:
        documents = table[text_fields].fillna("").astype(str).agg(" ".join, axis=1).str.casefold()
        for term in terms:
            table = table[documents.loc[table.index].str.contains(term, regex=False)].copy()
        labels = labels.loc[table.index]
    reasons = []
    for _, row in table.iterrows():
        matches = []
        if campuses:
            matches.append(f"校区：{row['campus']}")
        if levels:
            matches.append(f"级别：{int(row['course_level'])}")
        if departments:
            matches.append(
                "学科：" + "、".join(area for area in course_departments(row) if area in departments)
            )
        if categories:
            matches.extend(label for label in labels.loc[row.name] if label in set(categories))
        if terms:
            matches.append("关键词：" + "、".join(terms))
        if offering_status or session:
            matches.append(STATUS_LABELS.get(row["offering_status"], "尚未核实"))
        reasons.append(
            "；".join(matches) if matches else "官方目录课程；可通过校区、级别、学科和分类缩小范围"
        )
    table["match_reason"] = reasons
    # Exact course-code hits precede title hits, then other metadata matches.
    table["_exact"] = table["course_code"].astype(str).str.casefold().eq(query.strip().casefold()).astype(int)
    table["_title"] = (
        table["course_name"]
        .fillna("")
        .astype(str)
        .str.casefold()
        .map(lambda value: sum(term in value for term in terms))
    )
    return (
        table.sort_values(["_exact", "_title", "course_code"], ascending=[False, False, True], kind="stable")
        .drop(columns=["_exact", "_title"])
        .reset_index(drop=True)
    )
