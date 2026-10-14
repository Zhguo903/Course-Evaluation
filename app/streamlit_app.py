"""Fast, source-linked University of Toronto course finder using official data only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DUCKDB_PATH  # noqa: E402
from src.finder import (  # noqa: E402
    available_sessions,
    course_categories,
    course_departments,
    filter_courses,
    load_finder_data,
)

st.set_page_config(page_title="CourseInsight · UofT 找课", page_icon="🎓", layout="wide")

LABELS = {
    "course_code": "课程代码 / Code",
    "course_name": "课程名称 / Course",
    "campus": "校区 / Campus",
    "department": "院系 / Department",
    "course_level": "级别 / Level",
    "credit": "学分 / Credit",
    "breadth_requirements": "官方广度要求 / Breadth",
    "distribution_requirements": "官方分布要求 / Distribution",
    "prerequisite": "先修要求 / Prerequisite",
    "corequisite": "共修要求 / Corequisite",
    "exclusion": "互斥课程 / Exclusion",
    "recommended_preparation": "建议准备 / Recommended preparation",
    "enrolment_requirements": "注册要求 / Enrolment requirements",
    "requirement_notes": "其他要求 / Requirement notes",
    "source_url": "官方课程目录",
    "source_retrieved_at": "目录采集日期",
    "offering_status": "所选学期开课记录",
    "timetable_source_url": "官方课表",
    "timetable_retrieved_at": "课表核验时间",
    "timetable_checked_at": "课表核验时间",
    "match_reason": "匹配原因 / Why it matches",
    "category_summary": "分类 / BR",
}
STATUS_LABELS = {
    "offered": "课表已列出",
    "cancelled": "记录已取消",
    "not_found": "该期课表未检索到",
    "unknown": "未核验 / Unknown",
}
RESULT_COLUMNS = [
    "course_code",
    "course_name",
    "category_summary",
    "offering_status",
    "campus",
    "course_level",
    "department",
    "credit",
    "breadth_requirements",
    "distribution_requirements",
    "match_reason",
    "source_url",
]


def text_value(value: object) -> str:
    return "" if value is None or pd.isna(value) else str(value).strip()


def file_signature() -> tuple:
    if not DUCKDB_PATH.exists():
        return (str(DUCKDB_PATH), None, None)
    stat = DUCKDB_PATH.stat()
    return str(DUCKDB_PATH), stat.st_mtime_ns, stat.st_size


@st.cache_data(show_spinner=False)
def load_tables(signature: tuple) -> dict:
    """Read a published snapshot once; invalidate the cache when the DB changes."""
    tables = load_finder_data(db_path=DUCKDB_PATH)
    required = {"course_code", "course_name", "campus", "department", "course_level", "source_url"}
    if not required.issubset(tables["courses"].columns):
        raise ValueError("课程索引字段不完整，请重新构建官方课程索引。")
    tables["category_options"] = sorted(
        {label for _, course in tables["courses"].iterrows() for label in course_categories(course)}
    )
    tables["department_options"] = sorted(
        {area for _, course in tables["courses"].iterrows() for area in course_departments(course)}
    )
    return tables


def display_table(frame: pd.DataFrame, columns: list[str] | None = None) -> None:
    visible = frame[[column for column in columns if column in frame]].copy() if columns else frame.copy()
    if "offering_status" in visible:
        visible["offering_status"] = (
            visible["offering_status"].map(STATUS_LABELS).fillna(STATUS_LABELS["unknown"])
        )
    st.dataframe(
        visible.rename(columns=LABELS),
        hide_index=True,
        width="stretch",
        height="auto",
        column_config={
            LABELS["course_code"]: st.column_config.TextColumn(width="small"),
            LABELS["course_name"]: st.column_config.TextColumn(width="medium"),
            LABELS["category_summary"]: st.column_config.TextColumn(width="small"),
            LABELS["offering_status"]: st.column_config.TextColumn(width="small"),
            LABELS["source_url"]: st.column_config.LinkColumn(display_text="课程目录 ↗"),
            LABELS["timetable_source_url"]: st.column_config.LinkColumn(display_text="官方课表 ↗"),
        },
    )


def download_csv(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label, frame.to_csv(index=False).encode("utf-8-sig"), file_name=filename, mime="text/csv", key=key
    )


def setup_page(message: str) -> None:
    st.info(message)
    st.write("从已保存的官方课程目录与课表快照构建本地索引。")
    st.code("python run_pipeline.py\nstreamlit run app/streamlit_app.py", language="bash")
    if st.button("构建官方课程索引 / Build course index", type="primary"):
        with st.spinner("正在导入官方数据并构建课程索引…"):
            try:
                result = subprocess.run(
                    [sys.executable, str(PROJECT_ROOT / "run_pipeline.py")],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                st.error(f"构建未完成：{error}")
            else:
                if result.returncode == 0:
                    load_tables.clear()
                    st.rerun()
                else:
                    st.error("课程索引构建失败，请查看日志后重试。")
                    st.code((result.stderr or result.stdout)[-6000:], language="text")
    st.stop()


def render_requirements(course: pd.Series) -> None:
    st.subheader(f"{course['course_code']} · {course['course_name']}")
    summary = [text_value(course.get(field)) for field in ["campus", "department"]]
    if text_value(course.get("credit")):
        summary.append(f"{course['credit']} 学分")
    else:
        summary.append("学分未列出")
    st.caption(" · ".join(part for part in summary if part))
    if text_value(course.get("department_source")) == "course_prefix":
        st.caption("此课程按代码前缀归为学科组；该分组不是官方院系名称。")
    credit_note = text_value(course.get("credit_note"))
    if credit_note:
        st.caption(credit_note)
    source_url = text_value(course.get("source_url"))
    if source_url.startswith("https://"):
        st.markdown(f"[查看该课程的官方目录]({source_url})")
    st.caption(f"目录采集日期：{text_value(course.get('source_retrieved_at')) or '未记录'}")
    description = text_value(course.get("description"))
    if description:
        with st.expander("课程介绍（官方原文）"):
            st.write(description)
    st.markdown("**所选学期开课记录**")
    status = text_value(course.get("offering_status"))
    st.write(STATUS_LABELS.get(status, STATUS_LABELS["unknown"]))
    checked_at = text_value(course.get("timetable_retrieved_at")) or text_value(
        course.get("timetable_checked_at")
    )
    st.caption(f"所选学期：{session_label} · 课表核验时间：{checked_at or '尚无核验记录'}")
    timetable_url = text_value(course.get("timetable_source_url"))
    if timetable_url.startswith("https://"):
        st.markdown(f"[查看官方开课课表]({timetable_url})")
    if status == "unknown":
        st.info("该校区或学期尚未完成课表核验，不能据此判断是否开课。")
    elif status == "not_found":
        st.caption("在已完整核验的该期官方课表中未找到此课程记录；目录收录与当期开课是两回事。")
    st.caption("课表已列出只表示官方开课记录，不表示仍有名额、满足注册条件或可以跨校区修读。")
    categories = course_categories(course)
    st.markdown("**官方课程分类**")
    st.write(" / ".join(categories) if categories else "官方来源未列出可解析类别。")
    st.caption("课程分类采用各校区自己的体系；匹配类别不等于已满足个人毕业要求。")
    st.markdown("**修读要求（官方原文）**")
    st.caption("未列出字段不等于没有要求。本工具不自动判断先修资格、注册优先级或毕业要求是否满足。")
    fields = [
        "breadth_requirements",
        "distribution_requirements",
        "prerequisite",
        "corequisite",
        "exclusion",
        "recommended_preparation",
        "enrolment_requirements",
        "requirement_notes",
    ]
    for field in fields:
        if field == "distribution_requirements" and course.get("requirement_system") != "utm_distribution":
            continue
        if field == "breadth_requirements" and course.get("requirement_system") == "utm_distribution":
            continue
        st.markdown(f"**{LABELS[field]}**")
        st.write(text_value(course.get(field)) or "该字段未在官方来源中列出。")


st.title("CourseInsight · UofT 找课")
st.markdown("### 按校区、级别、院系与课程类别，快速找到符合条件的课")
st.caption("使用 St. George 文理学院、UTM 与 UTSC 的官方本科目录及实际课表记录。默认展示全部目录课程。")
if not DUCKDB_PATH.exists():
    setup_page("尚未找到本地官方课程索引。")
try:
    tables = load_tables(file_signature())
except (duckdb.Error, OSError, ValueError, KeyError) as error:
    st.warning(f"课程索引无法读取：{error}")
    setup_page("请重新构建当前版本的官方课程索引。")

courses = tables["courses"]
coverage = tables["coverage"]
if courses.empty:
    setup_page("官方课程索引为空，请检查已保存的目录快照后重新构建。")

query_column, session_column = st.columns([3, 2])
with query_column:
    query = st.text_input(
        "搜索课程代码、名称或修读要求", placeholder="例如：CSC108H1、Economics、calculus", key="course_query"
    )
with session_column:
    session_options = available_sessions(coverage)
    session_labels = {code: label for code, label in session_options}
    session_codes = [code for code, _ in session_options]
    session = st.selectbox(
        "开课学期 / Timetable session",
        [None, *session_codes],
        key="session_filter",
        format_func=lambda code: session_labels.get(
            code, "全部已发布学期" if session_codes else "暂无已核验学期"
        ),
    )
    session_label = session_labels.get(session, "全部已发布学期" if session_codes else "暂无已核验学期")

with st.sidebar:
    st.header("筛选条件 / Find a course")
    st.caption("多选可组合条件；留空表示不限。")
    campuses = st.multiselect(
        "校区 / Campus", sorted(courses["campus"].dropna().unique()), key="campus_filter"
    )
    levels = st.multiselect(
        "课程级别 / Level",
        sorted(courses["course_level"].dropna().unique()),
        key="level_filter",
        format_func=lambda level: "预科 / 其他（0级）" if level == 0 else f"{int(level)} 级",
    )
    departments = st.multiselect("院系 / Department", tables["department_options"], key="department_filter")
    category_options = tables["category_options"]
    categories = st.multiselect("课程类别 / BR & Distribution", category_options, key="classification_filter")
    st.caption(
        "类别选项保留校区前缀：St. George BR 1–5、UTM Distribution、UTSC Breadth；选择多个类别时匹配任一类别。"
    )
    only_offered = st.checkbox("仅看该学期课表已列出的课程", key="only_offered")
    st.caption("未核验课程仍在默认结果中；启用此项后只保留已核实的开课记录。")
    if st.button("刷新本地索引 / Refresh"):
        load_tables.clear()
        st.rerun()

results = filter_courses(
    courses,
    campuses=campuses,
    levels=levels,
    departments=departments,
    categories=categories,
    query=query,
    offering_status="offered" if only_offered else None,
    session=session,
)
results["selected_session_label"] = session_label
results["category_summary"] = results.apply(
    lambda row: (
        " / ".join(
            label.split(" · ")[1] if label.startswith("St. George") else label.split(" · ")[-1]
            for label in course_categories(row)
        )
        or "未列出"
    ),
    axis=1,
)
criteria = (
    tuple(campuses),
    tuple(levels),
    tuple(departments),
    tuple(categories),
    query,
    only_offered,
    session,
)
if st.session_state.get("active_criteria") != criteria:
    st.session_state["results_page"] = 1
    st.session_state["active_criteria"] = criteria
st.markdown(f"**找到 {len(results):,} 门课程** · 全部目录 {len(courses):,} 门 · {session_label}")
st.caption("课程依据所选条件匹配；匹配原因解释筛选依据，不评价课程好坏。目录收录不代表当前学期一定开课。")

if coverage.empty or ("complete" in coverage and not coverage["complete"].fillna(False).all()):
    st.info("部分校区或学期的官方课表尚未完整核验，相关课程会明确显示“未核验”，不会被当作未开课。")

find_tab, compare_tab = st.tabs(["课程结果与详情", "课程对比"])
with find_tab:
    if results.empty:
        st.info("没有匹配课程。请减少筛选条件、清空搜索词，或关闭“仅看课表已列出”后查看未核验课程。")
    else:
        page_size_column, page_column = st.columns([1, 1])
        with page_size_column:
            page_size = st.selectbox("每页课程数", [20, 50], key="page_size")
        total_pages = max(1, (len(results) + page_size - 1) // page_size)
        if st.session_state.get("results_page", 1) > total_pages:
            st.session_state["results_page"] = 1
        with page_column:
            page = st.number_input("页码", min_value=1, max_value=total_pages, step=1, key="results_page")
        page_start = (page - 1) * page_size
        page_courses = results.iloc[page_start : page_start + page_size]
        st.caption(
            f"第 {page:,} / {total_pages:,} 页 · 当前显示 {page_start + 1:,}–{page_start + len(page_courses):,} 门"
        )
        display_table(page_courses, RESULT_COLUMNS)
        download_csv(results, "下载当前找课结果 CSV", "uoft_course_results.csv", "results_csv")
        st.divider()
        lookup = page_courses.set_index("course_code", drop=False)
        selected_code = st.selectbox(
            "查看课程要求与来源 / Course details",
            page_courses["course_code"].tolist(),
            key="detail_course",
            format_func=lambda code: f"{code} · {lookup.loc[code, 'course_name']}",
        )
        render_requirements(lookup.loc[selected_code])

with compare_tab:
    st.caption("从当前筛选结果中选择 2–4 门课程，比较官方分类与修读要求。")
    comparison_codes = st.multiselect(
        "选择比较课程", results["course_code"].tolist(), key="compare_courses", max_selections=4
    )
    if len(comparison_codes) < 2:
        st.info("请选择至少两门课程。")
    else:
        comparison = results.set_index("course_code").loc[comparison_codes].reset_index()
        display_table(
            comparison,
            [
                "course_code",
                "course_name",
                "campus",
                "course_level",
                "credit",
                "breadth_requirements",
                "distribution_requirements",
                "offering_status",
                "prerequisite",
                "corequisite",
                "exclusion",
                "source_url",
            ],
        )
        download_csv(comparison, "下载课程对比 CSV", "uoft_course_comparison.csv", "comparison_csv")

with st.expander("数据来源与更新时间 / Sources & freshness"):
    st.write("课程要求来自各校区官方目录，开课记录来自官方课表快照。页面保留原文、来源链接与采集时间。")
    if "source_retrieved_at" in courses:
        dates = sorted(courses["source_retrieved_at"].dropna().astype(str).unique())
        st.caption("课程目录采集日期：" + ("、".join(dates) if dates else "未记录"))
    if not coverage.empty:
        display_table(coverage.rename(columns={"source_url": "timetable_source_url"}))
    else:
        st.info("尚无可用的课表核验记录。")
    quality = tables.get("quality", pd.DataFrame())
    if "status" in quality and quality["status"].eq("FAIL").any():
        st.warning("发布数据存在未通过的质量检查，请维护者检查索引。")

st.caption("CourseInsight · 多伦多大学三校区官方课程查找器")
