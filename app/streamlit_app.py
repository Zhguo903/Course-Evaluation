"""Streamlit dashboard for CourseInsight."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES
from src.recommender import build_recommendation_table, recommend_courses, similar_courses


st.set_page_config(page_title="CourseInsight", page_icon="CI", layout="wide")


@st.cache_data
def load_tables() -> dict[str, pd.DataFrame]:
    """Load dashboard tables from DuckDB and processed CSV files."""
    if not DUCKDB_PATH.exists():
        st.error("DuckDB warehouse not found. Run `python run_pipeline.py` first.")
        st.stop()
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
        profile = conn.execute("SELECT * FROM ads_course_profile").df()
        course_summary = conn.execute("SELECT * FROM dws_course_summary").df()
        dept_summary = conn.execute("SELECT * FROM dws_department_summary").df()
        instructor_summary = conn.execute("SELECT * FROM dws_instructor_summary").df()
    tags = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["course_tags"])
    reviews = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["reviews"])
    quality = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"])
    recommendation_table = build_recommendation_table()
    return {
        "profile": profile,
        "course_summary": course_summary,
        "dept_summary": dept_summary,
        "instructor_summary": instructor_summary,
        "tags": tags,
        "reviews": reviews,
        "quality": quality,
        "recommendation_table": recommendation_table,
    }


tables = load_tables()

st.title("CourseInsight: Campus Course Review & Recommendation System")

overview_tab, profile_tab, rec_tab, similar_tab, quality_tab = st.tabs(
    ["Overview", "Course Profile", "Recommendation", "Similar Courses", "Data Quality"]
)

with overview_tab:
    profile = tables["profile"]
    dept_summary = tables["dept_summary"]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Courses", f"{len(profile):,}")
    col2.metric("Reviews", f"{int(dept_summary['review_count'].sum()):,}")
    col3.metric("Instructors", f"{len(tables['instructor_summary']):,}")
    col4.metric("Avg Rating", f"{profile['avg_rating'].mean():.2f}")
    col5.metric("Avg Difficulty", f"{profile['avg_difficulty'].mean():.2f}")
    col6.metric("Avg Workload", f"{profile['avg_workload'].mean():.2f}")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(
            px.bar(dept_summary, x="department", y="course_count", title="Course Count by Department"),
            use_container_width=True,
        )
    with chart_col2:
        st.plotly_chart(
            px.bar(dept_summary, x="department", y="avg_rating", title="Average Rating by Department"),
            use_container_width=True,
        )

with profile_tab:
    recommendation_table = tables["recommendation_table"]
    selected_code = st.selectbox("Course", sorted(recommendation_table["course_code"].astype(str).tolist()))
    selected = recommendation_table[recommendation_table["course_code"] == selected_code].iloc[0]
    st.subheader(f"{selected['course_code']} - {selected['course_name']}")
    st.caption(f"{selected['department']}")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Rating", f"{selected['avg_rating']:.2f}")
    metric_cols[1].metric("Difficulty", f"{selected['avg_difficulty']:.2f}")
    metric_cols[2].metric("Workload", f"{selected['avg_workload']:.2f}")
    metric_cols[3].metric("Usefulness", f"{selected['avg_usefulness']:.2f}")

    st.write("Tags")
    tags = [tag.strip() for tag in str(selected.get("tags", "")).split(",") if tag.strip()]
    st.write(" | ".join(tags) if tags else "No tags generated")
    st.write("Keywords")
    st.write(selected.get("keywords", ""))

    course_id = selected["course_id"]
    sample_reviews = tables["reviews"][tables["reviews"]["course_id"] == course_id].head(8)
    st.write("Representative Reviews")
    st.dataframe(sample_reviews[["rating", "difficulty", "workload", "usefulness", "review_text"]], use_container_width=True)

with rec_tab:
    pref_col1, pref_col2, pref_col3 = st.columns(3)
    preferences = {
        "prefer_low_workload": pref_col1.checkbox("Low workload", value=True),
        "prefer_high_rating": pref_col1.checkbox("High rating", value=True),
        "prefer_project_based": pref_col2.checkbox("Project based", value=True),
        "prefer_data_science": pref_col2.checkbox("Data science friendly", value=True),
        "prefer_gpa_friendly": pref_col3.checkbox("GPA friendly", value=False),
        "avoid_exam_heavy": pref_col3.checkbox("Avoid exam heavy", value=True),
    }
    if st.button("Recommend Top 10 Courses", type="primary"):
        results = recommend_courses(preferences, top_n=10, recommendation_table=tables["recommendation_table"])
        st.dataframe(results, use_container_width=True)

with similar_tab:
    recommendation_table = tables["recommendation_table"]
    selected_similar_code = st.selectbox(
        "Select a course", sorted(recommendation_table["course_code"].astype(str).tolist()), key="similar_course"
    )
    similar = similar_courses(selected_similar_code, top_n=5, recommendation_table=recommendation_table)
    st.dataframe(similar, use_container_width=True)

with quality_tab:
    quality = tables["quality"]
    pass_count = int((quality["status"] == "PASS").sum())
    fail_count = int((quality["status"] == "FAIL").sum())
    q1, q2 = st.columns(2)
    q1.metric("Passed Checks", pass_count)
    q2.metric("Failed Checks", fail_count)
    st.plotly_chart(px.bar(quality, x="check_name", y="failure_rate", color="status"), use_container_width=True)
    st.dataframe(quality, use_container_width=True)
    failed = quality[quality["status"] == "FAIL"]
    if not failed.empty:
        st.write("Failed Checks")
        st.dataframe(failed, use_container_width=True)
