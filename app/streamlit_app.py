"""Fast, source-linked University of Toronto course finder using official data only."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

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


def https_url(value: object) -> str:
    """Only turn well-formed, credential-free HTTPS source URLs into active links."""
    raw = text_value(value)
    if not raw or any(character.isspace() for character in raw):
        return ""
    try:
        parsed = urlsplit(raw)
        valid = parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
        _ = parsed.port  # Validate malformed ports without producing Streamlit magic output.
    except ValueError:
        return ""
    return raw if valid else ""


def source_link(label: str, value: object) -> None:
    url = https_url(value)
    if url:
        st.link_button(label, url)
    else:
        st.caption("来源链接暂不可用。")


def course_records(frame: pd.DataFrame, code: str, campus: str) -> pd.DataFrame:
    if frame.empty or "course_code" not in frame:
        return frame.iloc[0:0].copy()
    mask = frame["course_code"].fillna("").eq(code)
    if "campus" in frame:
        mask &= frame["campus"].fillna("").eq(campus)
    return frame.loc[mask].copy()


ACCESS_LABELS = {
    "public": "公开访问",
    "utorid_required": "需 UTORid 登录",
    "mixed": "部分内容需登录",
    "restricted": "受限访问",
}
SOURCE_STATUS_LABELS = {
    "imported": "已导入记录",
    "external_link": "外部入口，未导入记录",
    "login_required": "需登录的外部入口，未导入记录",
    "licence_required": "需授权，未导入记录",
}


def render_student_reviews(frame: pd.DataFrame) -> None:
    st.subheader("公开学生评价 / Public student reviews")
    if frame.empty:
        st.info("这门课尚无已导入的公开学生评价记录；缺少记录不表示评价较低。")
        return
    st.caption(
        "以下为有公开来源的个人看法，作者修读身份未独立核验。"
        "每条记录保留原始评价维度和尺度，不合并为课程综合分，也不据此排序。"
    )
    if len(frame) > 1 and "reviewer_label" in frame and frame["reviewer_label"].dropna().nunique() == 1:
        st.caption("当前这些记录来自同一位作者，不代表多个独立学生的共识。")
    for _, review in frame.iterrows():
        with st.container(border=True):
            st.write(text_value(review.get("reviewer_label")) or "来源未列出作者标识")
            period = text_value(review.get("academic_period")) or "未列出修读学期"
            published = text_value(review.get("published_at")) or "未列出发布日期"
            retrieved = text_value(review.get("retrieved_at")) or "未记录"
            st.caption(f"修读学期：{period} · 发布：{published} · 采集：{retrieved}")
            rating = text_value(review.get("rating"))
            if rating:
                lower = text_value(review.get("rating_scale_min")) or "未列出"
                upper = text_value(review.get("rating_scale_max")) or "未列出"
                dimension = text_value(review.get("rating_dimension"))
                dimension = (
                    "作者个人推荐程度" if dimension == "recommendation" else (dimension or "来源未列出维度")
                )
                st.write(f"原站数值：{rating} · {dimension} · 原始尺度 {lower}–{upper}")
            summary = text_value(review.get("summary"))
            if summary:
                st.write(summary)
            source_title = text_value(review.get("source_title"))
            if source_title:
                st.caption(f"来源：{source_title}")
            source_link("查看这条评价的公开来源 ↗", review.get("source_url"))
            with st.expander("评价来源与适用范围"):
                if text_value(review.get("verification_level")) == "public_self_report":
                    st.caption("核验范围：公开自述；未核验作者选课身份。")
                for field, label in [("code_mapping", "课程代码关联依据"), ("limitations", "适用范围")]:
                    detail = text_value(review.get(field))
                    if detail:
                        st.caption(f"{label}：{detail}")


def render_historical_evaluations(frame: pd.DataFrame) -> None:
    st.subheader("历史课程评价 / Historical evaluations")
    if frame.empty:
        st.info("这门课尚无已导入且能准确关联课程代码的历史官方评价记录。")
        return
    st.caption(
        "数据为第三方公开整理的历史官方评价结果副本，尚未与登录后的官方平台逐条核验。"
        "这里按历史学期逐条展示，不将不同问题、学期或教学班合成综合分。"
    )
    st.caption("保留原题 1–5 尺度；工作量高分表示负担更重，非课程难度。历史结果不代表当前学期。")
    with st.expander("原始题目、回复数与缺失值说明"):
        st.caption(
            "总体学习体验、工作量与推荐意愿保留来源的 1–5 尺度；工作量分数越高表示负担越重，不代表课程难度。"
            "本报告回答数对应该报告的回收份数；同一问卷批次可能出现多份教师报告，不能相加当作独立学生人数。"
            "缺失值保留为空，不视为 0；历史结果不代表当前学期。"
        )
    st.write(f"已导入 {len(frame):,} 条历史报告，以下最多展示最近 50 条。")
    if "term" in frame:
        frame = frame.assign(
            _term_order=frame["term"].astype(str).str.casefold().map({"fall": 3, "summer": 2, "winter": 1})
        )
    sort_fields = [
        field for field in ["year", "_term_order", "teaching_section", "cohort_id"] if field in frame
    ]
    if sort_fields:
        frame = frame.sort_values(sort_fields, ascending=False, kind="stable", na_position="last")
    labels = {
        "year": "历史年份",
        "term": "学期",
        "teaching_section": "教学班",
        "overall_score": "总体学习体验（1–5）",
        "workload_score": "工作量（1–5，非难度）",
        "recommendation_score": "推荐意愿（1–5）",
        "response_count": "本报告回答数",
        "invited_count": "本报告受邀数",
        "source_url": "公开数据来源",
        "source_retrieved_at": "来源采集日期",
        "quality_flags": "原始数据提示",
        "cohort_id": "问卷批次",
    }
    columns = [field for field in labels if field in frame]
    visible = frame.head(50)[columns].copy()
    if "source_url" in visible:
        visible["source_url"] = visible["source_url"].map(https_url)
    if "quality_flags" in frame:
        flag_labels = {
            "multiple_reports_same_cohort": "同批次多报告",
            "teaching_section_not_identified": "教学班未识别",
            "responses_exceed_invited_in_source": "原始回答数高于受邀数",
            "invited_count_not_listed": "受邀数未列出",
        }

        def flags(value: object) -> list[str]:
            if isinstance(value, (list, tuple)):
                return list(value)
            try:
                decoded = json.loads(text_value(value) or "[]")
            except ValueError:
                return []
            return decoded if isinstance(decoded, list) else []

        if (
            frame["quality_flags"]
            .map(lambda value: "responses_exceed_invited_in_source" in flags(value))
            .any()
        ):
            st.warning("本课有来源记录的回答数高于受邀数。页面保留原始数值，并在每行提示中标注该异常。")
        visible["quality_flags"] = visible["quality_flags"].map(
            lambda value: "；".join(flag_labels.get(flag, str(flag)) for flag in flags(value))
        )
    st.dataframe(
        visible.rename(columns=labels),
        hide_index=True,
        width="stretch",
        column_config={"公开数据来源": st.column_config.LinkColumn(display_text="公开数据 ↗")},
    )
    download_csv(
        frame.drop(columns=["_term_order"], errors="ignore"),
        "下载本课完整历史评价 CSV",
        "uoft_course_historical_evaluations.csv",
        "evaluation_csv",
    )


def render_resource_cards(frame: pd.DataFrame, empty_message: str) -> None:
    if frame.empty:
        st.info(empty_message)
        return
    for _, resource in frame.iterrows():
        with st.container(border=True):
            st.write(text_value(resource.get("title")) or "学习资料入口")
            access = ACCESS_LABELS.get(text_value(resource.get("access_requirement")), "访问条件未列出")
            provider = text_value(resource.get("provider"))
            kind = text_value(resource.get("resource_type"))
            kind = {
                "lecture_notes": "讲义",
                "course_site": "课程网站",
                "syllabus": "教学大纲",
                "learning_support": "学习支持",
                "exam_portal": "往年试卷入口",
                "student_guide": "学生指南",
            }.get(kind, kind)
            campus = text_value(resource.get("campus"))
            st.caption(" · ".join(part for part in [provider, campus, kind, access] if part))
            period = text_value(resource.get("academic_period"))
            if period:
                years = [int(year) for year in re.findall(r"\b20\d{2}\b", period)]
                historical = bool(years) and max(years) < pd.Timestamp.now(tz="America/Toronto").year
                prefix = "历史资料 · " if historical else ""
                st.caption(f"{prefix}资料对应学期/年份：{period}；请核对当前课程要求。")
            verified = text_value(resource.get("verified_at"))
            if verified:
                st.caption(f"入口核验日期：{verified}")
            source_link("打开学习资料入口 ↗", resource.get("url"))
            with st.expander("资料来源与使用说明"):
                for field in ["rights_note", "limitations"]:
                    note = text_value(resource.get(field))
                    if note:
                        st.caption(note)
            source_url = https_url(resource.get("source_url"))
            if source_url and source_url != https_url(resource.get("url")):
                source_link("资料来源说明 ↗", source_url)


def render_feedback_sources(frame: pd.DataFrame) -> None:
    with st.expander("评价来源、覆盖范围与访问条件"):
        st.caption("已导入记录与外部查询入口分别登记；列出一个入口不表示已取得其中的评价数据。")
        if frame.empty:
            st.info("尚无已登记的评价来源。")
            return
        labels = {
            "title": "来源",
            "source_type": "来源类型",
            "status": "接入状态",
            "access": "访问条件",
            "covered_period": "覆盖学期/年份",
            "source_url": "来源入口",
            "limitations": "范围与限制",
        }
        visible = frame[[field for field in labels if field in frame]].copy()
        if "status" in visible:
            visible["status"] = visible["status"].map(SOURCE_STATUS_LABELS).fillna(visible["status"])
        if "access" in visible:
            visible["access"] = visible["access"].map(ACCESS_LABELS).fillna(visible["access"])
        if "source_type" in visible:
            source_types = {
                "student_review_collection": "公开个人评价",
                "historical_evaluation_dataset": "历史问卷副本",
                "official_evaluation_portal": "官方评价入口",
                "third_party_evaluation_portal": "第三方评价入口",
            }
            visible["source_type"] = visible["source_type"].map(source_types).fillna(visible["source_type"])
        if "source_url" in visible:
            visible["source_url"] = visible["source_url"].map(https_url)
        st.dataframe(
            visible.rename(columns=labels),
            hide_index=True,
            width="stretch",
            column_config={"来源入口": st.column_config.LinkColumn(display_text="来源 ↗")},
        )


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
    only_feedback = st.checkbox(
        "仅看有已导入评价的课程",
        key="only_feedback",
        disabled=not {"student_review_count", "historical_evaluation_count"}.issubset(courses.columns),
        help="至少有一条已导入的个人评价或历史问卷报告。外部查询入口不计为已导入评价。",
    )
    only_resources = st.checkbox(
        "仅看有课程专属资料的课程",
        key="only_resources",
        disabled="resource_count" not in courses,
        help="只统计与当前课程代码准确关联的资料，不包含通用入口或未关联历史资料。",
    )
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
if only_feedback:
    review_counts = pd.to_numeric(results["student_review_count"], errors="coerce").fillna(0)
    historical_counts = pd.to_numeric(results["historical_evaluation_count"], errors="coerce").fillna(0)
    results = results.loc[(review_counts + historical_counts).gt(0)].copy()
if only_resources:
    results = results.loc[pd.to_numeric(results["resource_count"], errors="coerce").fillna(0).gt(0)].copy()
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
    only_feedback,
    only_resources,
    session,
)
if st.session_state.get("active_criteria") != criteria:
    st.session_state["results_page"] = 1
    st.session_state["active_criteria"] = criteria
st.markdown(f"**找到 {len(results):,} 门课程** · 全部目录 {len(courses):,} 门 · {session_label}")
st.caption("课程依据所选条件匹配；匹配原因解释筛选依据，不评价课程好坏。目录收录不代表当前学期一定开课。")

if coverage.empty or ("complete" in coverage and not coverage["complete"].fillna(False).all()):
    st.info("部分校区或学期的官方课表尚未完整核验，相关课程会明确显示“未核验”，不会被当作未开课。")

find_tab, compare_tab, feedback_tab = st.tabs(["课程结果与详情", "课程对比", "学生评价与学习资料"])
selected_code = None
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

with feedback_tab:
    st.caption("在当前筛选范围内选课查看。默认跟随课程详情，也可以在此独立搜索其他课程。")
    if results.empty:
        st.info("当前筛选范围内没有课程，请先调整找课条件，再查看对应评价与学习资料。")
    else:
        feedback_codes = results["course_code"].tolist()
        default_code = selected_code or feedback_codes[0]
        if (
            st.session_state.get("feedback_detail_course") != default_code
            or st.session_state.get("feedback_course") not in feedback_codes
        ):
            st.session_state["feedback_course"] = default_code
            st.session_state["feedback_detail_course"] = default_code
        feedback_lookup = results.set_index("course_code", drop=False)
        feedback_code = st.selectbox(
            "查看评价与资料的课程",
            feedback_codes,
            index=None,
            key="feedback_course",
            format_func=lambda code: f"{code} · {feedback_lookup.loc[code, 'course_name']}",
        )
        if feedback_code:
            selected_course = feedback_lookup.loc[feedback_code]
            feedback_campus = text_value(selected_course.get("campus"))
            st.subheader(f"{feedback_code} · {selected_course['course_name']}")
            st.caption("评价和资料各自标注历史学期与来源，与当前开课状态分开展示。")
            render_student_reviews(
                course_records(tables.get("reviews", pd.DataFrame()), feedback_code, feedback_campus)
            )
            render_historical_evaluations(
                course_records(tables.get("evaluations", pd.DataFrame()), feedback_code, feedback_campus)
            )
            st.subheader("学习资料 / Learning resources")
            resources = tables.get("resources", pd.DataFrame())
            specific = general = pd.DataFrame()
            if not resources.empty and {"course_code", "campus"}.issubset(resources.columns):
                relevant = resources[resources["campus"].fillna("").isin([feedback_campus, "All"])]
                specific = relevant[relevant["course_code"].fillna("").eq(feedback_code)]
                general = relevant[relevant["course_code"].fillna("").eq("")]
            st.markdown("**本课程相关资料**")
            render_resource_cards(specific, "这门课尚无已导入的课程专属学习资料入口。")
            st.markdown("**通用入口与未关联资料**")
            st.caption("这些条目没有关联到当前课程；其中的历史课程资料不表示课程等价或当前适用。")
            render_resource_cards(general, "当前校区尚无已登记的通用资料入口。")
    render_feedback_sources(tables.get("feedback_sources", pd.DataFrame()))

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
