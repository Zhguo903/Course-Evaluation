"""Interactive, Chinese-first course explorer for the synthetic CourseInsight demo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES  # noqa: E402
from src.recommender import recommend_courses, similar_courses  # noqa: E402

st.set_page_config(page_title="CourseInsight · 课程探索", page_icon="🎓", layout="wide")

LABELS = {
    "course_code": "课程代码 / Code",
    "course_name": "课程名称 / Course",
    "department": "院系 / Department",
    "course_level": "课程级别 / Level",
    "review_count": "评论数 / Reviews",
    "avg_rating": "综合评分 / Rating",
    "avg_difficulty": "难度 / Difficulty",
    "avg_workload": "工作量 / Workload",
    "avg_usefulness": "实用性 / Usefulness",
    "recommend_score": "基础分 / Base score",
    "preference_score": "偏好匹配分 / Preference score",
    "gpa_friendly_score": "轻松度指标（规则估计）",
    "tags": "课程标签 / Tags",
    "keywords": "文本关键词 / Keywords",
    "recommendation_reason": "推荐理由 / Why this course",
    "similarity_score": "文本相似度 / Similarity",
    "common_tags": "共同标签 / Shared tags",
    "rating": "评分",
    "difficulty": "难度",
    "workload": "工作量",
    "usefulness": "实用性",
    "review_text": "评论原文 / Review",
    "review_date": "评论日期",
}
COURSE_COLUMNS = [
    "course_code",
    "course_name",
    "department",
    "review_count",
    "avg_rating",
    "avg_difficulty",
    "avg_workload",
    "avg_usefulness",
    "tags",
]
REQUIRED_PATHS = [DUCKDB_PATH]


def file_signature() -> tuple:
    """Invalidate cached data when the pipeline replaces any input artifact."""
    paths = [DUCKDB_PATH, *(PROCESSED_DATA_DIR / name for name in PROCESSED_FILES.values())]
    return tuple(
        (str(path), path.stat().st_mtime_ns, path.stat().st_size)
        if path.exists()
        else (str(path), None, None)
        for path in paths
    )


@st.cache_data(show_spinner=False)
def load_tables(signature: tuple) -> dict[str, pd.DataFrame]:
    """Use the signature as part of the cache key; keep UI calls outside the cache."""
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
        conn.execute("BEGIN TRANSACTION")
        profile = conn.execute("SELECT * FROM ads_course_profile").df()
        reviews = conn.execute("SELECT * FROM dwd_reviews_clean").df()
        tags = conn.execute("SELECT course_id, tags, keywords FROM dws_course_tags").df()
        published_quality = conn.execute("SELECT * FROM ads_data_quality_report").df()
        conn.execute("COMMIT")
    quality_path = PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"]
    quality = pd.read_csv(quality_path) if quality_path.exists() else published_quality
    if not {"status", "check_name", "table_name", "failed_count", "total_count"}.issubset(quality.columns):
        raise ValueError("质量报告字段不完整，请重新运行数据流程。")
    table = profile.merge(tags, on="course_id", how="left")
    table[["tags", "keywords"]] = table[["tags", "keywords"]].fillna("")
    required_columns = {
        "course_id",
        "course_code",
        "course_name",
        "department",
        "avg_rating",
        "avg_difficulty",
        "avg_workload",
        "avg_usefulness",
        "tags",
        "keywords",
    }
    if not required_columns.issubset(table.columns):
        raise ValueError("数据仓库版本过旧或字段不完整，请重新运行数据流程。")
    # Older warehouses may not carry review_count in ADS; derive it from the same reviews.
    if "review_count" not in table:
        table["review_count"] = table["course_id"].map(reviews.groupby("course_id").size()).fillna(0)
    table["review_count"] = table["review_count"].fillna(0).astype(int)
    table["course_code"] = table["course_code"].astype(str)
    table = table.sort_values("course_code").reset_index(drop=True)
    return {"profile": profile, "reviews": reviews, "quality": quality, "courses": table}


def display_table(frame: pd.DataFrame, columns: list[str] | None = None) -> None:
    """Keep original column names for exports while displaying readable labels."""
    if columns is not None:
        frame = frame[[column for column in columns if column in frame]]
    st.dataframe(frame.rename(columns=LABELS), hide_index=True, width="stretch")


def download_csv(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def format_metric(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.2f}"


def empty_courses() -> bool:
    if filtered.empty:
        st.info("当前筛选没有匹配课程。请扩大院系范围、降低最低评分或评论数，或清空搜索词。")
        return True
    return False


def missing_data(message: str) -> None:
    """A clean checkout should open a useful setup page without building on reruns."""
    st.info(message)
    st.markdown("首次使用时，先生成模拟数据并构建本地数据仓库。")
    st.code("python run_pipeline.py\nstreamlit run app/streamlit_app.py", language="bash")
    st.caption("也可以点击下方按钮生成演示数据。只有点击按钮才会运行；运行会更新本地演示数据文件。")
    if st.button("生成演示数据 / Build demo data", type="primary"):
        with st.spinner("正在生成数据、提取标签并构建数仓…"):
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
                    st.error("数据构建失败，请查看日志，修复后重试。")
                    st.code((result.stderr or result.stdout)[-6000:], language="text")
    st.stop()


st.title("CourseInsight")
st.markdown("### 看懂课程评价，找到适合自己的课")
st.caption("课程探索 · 指标比较 · 可解释推荐 | Course review analytics & explainable recommendations")
st.info(
    "演示数据说明：本项目使用合成课程与评论，不代表真实学校或教师。"
    "评分、标签和推荐用于展示分析流程；GPA Friendly 仅是基于评价指标的规则标签，不预测真实成绩。",
    icon="ℹ️",
)

if any(not path.exists() for path in REQUIRED_PATHS):
    missing_data("尚未找到完整的本地演示数据。")
try:
    tables = load_tables(file_signature())
except (duckdb.Error, OSError, ValueError, KeyError) as error:
    st.warning(f"本地数据无法读取：{error}")
    missing_data("请重新构建演示数据，或在终端运行数据流程查看错误。")

courses = tables["courses"]
reviews = tables["reviews"]
latest_quality = tables["quality"]
if "status" in latest_quality and latest_quality["status"].eq("FAIL").any():
    st.warning("最近一次数据质量检查未通过；当前分析使用上一次成功发布的数仓快照。请在数据质量页查看失败项。")

with st.sidebar:
    st.header("课程筛选 / Filters")
    st.caption("筛选同时影响概览、画像、比较和推荐结果。")
    search = st.text_input("搜索课程、标签或关键词", placeholder="例如：Python、Statistics、Project")
    departments = sorted(courses["department"].dropna().unique().tolist())
    selected_departments = st.multiselect("院系 / Department", departments, default=departments)
    levels = []
    if "course_level" in courses:
        level_options = sorted(courses["course_level"].dropna().unique().tolist(), key=str)
        levels = st.multiselect("课程级别 / Level", level_options, default=level_options)
    min_reviews = st.number_input("最低评论数 / Minimum reviews", min_value=0, value=0, step=5)
    min_rating = st.slider("最低综合评分 / Minimum rating", 1.0, 5.0, 1.0, 0.1)
    max_difficulty = st.slider("最高难度 / Maximum difficulty", 1.0, 5.0, 5.0, 0.1)
    max_workload = st.slider("最高工作量 / Maximum workload", 1.0, 5.0, 5.0, 0.1)
    st.caption("所有评价指标均为 1–5 分。难度、工作量越低越轻松；评分、实用性越高越好。")
    if st.button("刷新本地数据 / Refresh data"):
        load_tables.clear()
        st.rerun()

mask = (
    courses["department"].isin(selected_departments)
    & courses["review_count"].ge(min_reviews)
    & (courses["avg_rating"].ge(min_rating) | (courses["avg_rating"].isna() & (min_rating == 1.0)))
    & (
        courses["avg_difficulty"].le(max_difficulty)
        | (courses["avg_difficulty"].isna() & (max_difficulty == 5.0))
    )
    & (courses["avg_workload"].le(max_workload) | (courses["avg_workload"].isna() & (max_workload == 5.0)))
)
if "course_level" in courses:
    mask &= courses["course_level"].isin(levels)
if search.strip():
    search_columns = ["course_code", "course_name", "department", "tags", "keywords"]
    searchable = (
        courses[[column for column in search_columns if column in courses]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
    )
    mask &= searchable.str.contains(search.strip(), case=False, regex=False)
filtered = courses.loc[mask].copy()
filtered_reviews = reviews.loc[reviews["course_id"].isin(filtered["course_id"])].copy()
st.caption(f"当前范围：{len(filtered):,} / {len(courses):,} 门课程 · {len(filtered_reviews):,} 条评论")


def render_overview() -> None:
    if empty_courses():
        return
    metric_columns = st.columns(5)
    metric_columns[0].metric("匹配课程", f"{len(filtered):,}")
    metric_columns[1].metric("评论样本", f"{len(filtered_reviews):,}")
    for column, label, metric_column in zip(
        ["rating", "difficulty", "workload"], ["平均评分", "平均难度", "平均工作量"], metric_columns[2:]
    ):
        metric_column.metric(label, format_metric(filtered_reviews[column].mean()))
    st.caption("概览均值直接按当前范围内的评论计算，每条评论权重相同；课程列表展示各课程的评论均值。")
    count_by_department = filtered.groupby("department").size().rename("course_count").reset_index()
    review_departments = filtered_reviews.merge(
        filtered[["course_id", "department"]], on="course_id", how="left"
    )
    rating_by_department = review_departments.groupby("department")["rating"].mean().reset_index()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            px.bar(
                count_by_department,
                x="course_count",
                y="department",
                orientation="h",
                title="各院系匹配课程数",
                labels={"course_count": "课程数", "department": "院系"},
                color_discrete_sequence=["#2563eb"],
            ),
            width="stretch",
        )
    with right:
        figure = px.bar(
            rating_by_department,
            x="rating",
            y="department",
            orientation="h",
            title="各院系平均评分（按评论计算）",
            labels={"rating": "平均评分", "department": "院系"},
            color_discrete_sequence=["#0d9488"],
        )
        figure.update_xaxes(range=[0, 5])
        st.plotly_chart(figure, width="stretch")
    st.subheader("课程一览 / Course catalog")
    display_table(filtered.sort_values(["avg_rating", "review_count"], ascending=False), COURSE_COLUMNS)
    download_csv(filtered, "下载筛选课程 CSV", "courseinsight_courses.csv", "catalog_csv")


def render_profile() -> None:
    if empty_courses():
        return
    lookup = filtered.set_index("course_code")
    selected_code = st.selectbox(
        "选择课程 / Choose a course",
        filtered["course_code"].tolist(),
        format_func=lambda code: f"{code} · {lookup.loc[code, 'course_name']}",
        key="profile_course",
    )
    selected = lookup.loc[selected_code]
    st.subheader(f"{selected_code} · {selected['course_name']}")
    st.caption(f"{selected['department']} · {int(selected['review_count']):,} 条评论")
    for column, metric in zip(
        st.columns(4), ["avg_rating", "avg_difficulty", "avg_workload", "avg_usefulness"]
    ):
        column.metric(LABELS[metric].split(" /")[0], format_metric(selected[metric]))
    if "smoothed_rating" in selected and selected["review_count"] > 0:
        st.caption(
            f"平滑评分 {format_metric(selected['smoothed_rating'])} · "
            f"评论支持权重 {selected['confidence']:.0%}（自身评论均分在平滑评分中的权重，不是准确率）"
        )
    if selected["review_count"] == 0:
        st.info("这门课程尚无评论；保留在目录中供查看，但不参与推荐排序。")
    st.markdown("**课程标签 / Tags**")
    tags = [tag.strip() for tag in str(selected.get("tags", "")).split(",") if tag.strip()]
    st.write(" · ".join(tags) if tags else "暂未提取到标签。")
    st.markdown("**文本关键词 / Keywords**")
    st.write(selected.get("keywords", "") or "暂未提取到关键词。")
    st.caption("标签使用评论关键词与规则生成，可能遗漏语境或否定表达；请结合评论阅读。")
    st.subheader("评论样本 / Sample reviews")
    samples = reviews[reviews["course_id"] == selected["course_id"]].copy()
    if "review_date" in samples:
        samples = samples.sort_values("review_date", ascending=False)
    st.caption("按日期倒序展示前 12 条，供查看原始样本；并非自动选取的代表性评论。")
    display_table(
        samples.head(12), ["review_date", "rating", "difficulty", "workload", "usefulness", "review_text"]
    )


def render_comparison() -> None:
    if empty_courses():
        return
    st.subheader("放在一起比较 / Compare courses")
    selected_codes = st.multiselect(
        "选择 2–4 门课程",
        filtered["course_code"].tolist(),
        default=filtered["course_code"].head(min(2, len(filtered))).tolist(),
        key="compare_courses",
    )
    if len(selected_codes) < 2:
        st.info("请至少选择两门课程进行比较。")
        return
    if len(selected_codes) > 4:
        st.info("为保证可读性，请最多选择四门课程。")
        return
    comparison = filtered.set_index("course_code").loc[selected_codes].reset_index()
    display_table(comparison, COURSE_COLUMNS)
    metrics = ["avg_rating", "avg_difficulty", "avg_workload", "avg_usefulness"]
    chart_data = comparison.melt(
        id_vars="course_code", value_vars=metrics, var_name="metric", value_name="value"
    )
    chart_data["metric"] = chart_data["metric"].map(lambda metric: LABELS[metric].split(" /")[0])
    figure = px.bar(
        chart_data,
        x="metric",
        y="value",
        color="course_code",
        barmode="group",
        labels={"metric": "评价维度", "value": "平均分", "course_code": "课程"},
    )
    figure.update_yaxes(range=[0, 5])
    st.plotly_chart(figure, width="stretch")
    st.caption("难度和工作量越低越轻松；综合评分和实用性越高越好。评论数用于判断样本量，不代表统计置信度。")
    download_csv(comparison, "下载比较结果 CSV", "courseinsight_comparison.csv", "comparison_csv")


def render_recommendations() -> None:
    if empty_courses():
        return
    st.subheader("按你的偏好排序 / Personalize the ranking")
    left, middle, right = st.columns(3)
    preferences = {
        "prefer_low_workload": left.checkbox("工作量较低 / Lower workload", value=True),
        "prefer_high_rating": left.checkbox("综合评分较高 / Higher rating", value=True),
        "prefer_project_based": middle.checkbox("项目实践 / Project based", value=False),
        "prefer_data_science": middle.checkbox("数据科学相关 / Data science", value=False),
        "prefer_gpa_friendly": right.checkbox("轻松度规则标签 / GPA Friendly", value=False),
        "avoid_exam_heavy": right.checkbox("减少考试密集课程 / Fewer exams", value=False),
    }
    top_n = st.select_slider("展示数量 / Results", options=[5, 10, 15, 20], value=10)
    results = recommend_courses(preferences, top_n=top_n, recommendation_table=filtered)
    st.caption(
        "偏好匹配分 = 基础课程分 + 已选偏好的加减权重。勾选后即时重新排序；"
        "分数用于当前偏好下的相对比较，不是概率或预测成绩。侧栏筛选决定候选课程。"
    )
    if results.empty:
        st.info("当前候选课程尚无有效评论，暂时无法推荐。请调整筛选范围。")
        return
    result_columns = [
        "course_code",
        "course_name",
        "department",
        "review_count",
        "preference_score",
        "recommend_score",
        "avg_rating",
        "avg_workload",
        "tags",
        "recommendation_reason",
    ]
    display_table(results, result_columns)
    download_csv(results, "下载推荐结果 CSV", "courseinsight_recommendations.csv", "recommendation_csv")
    with st.expander("如何理解推荐 / About the recommendation"):
        st.write(
            "推荐由课程评价均值、规则标签及显式偏好共同计算。推荐理由来自实际匹配的指标或标签，"
            "没有匹配到特定偏好时会说明基础排序依据。GPA Friendly 并未使用真实 GPA 数据。"
            "偏好会调整排序；如需限制难度、工作量或院系，请使用侧栏筛选。"
        )


def render_similar() -> None:
    st.subheader("从喜欢的课程出发 / Discover similar courses")
    if courses.empty:
        st.info("暂无可用于相似检索的课程。")
        return
    source_code = st.selectbox(
        "参考课程 / Reference course", courses["course_code"].tolist(), key="similar_course"
    )
    # The source remains available even when filters exclude it; only candidates are filtered.
    source = courses[courses["course_code"] == source_code]
    candidates = (
        pd.concat([filtered, source], ignore_index=True).drop_duplicates("course_code").reset_index(drop=True)
    )
    st.caption("参考课程可从全部课程中选择；结果遵循侧栏筛选。文本相似度依据课程名、院系、标签和关键词计算。")
    if len(candidates) <= 1:
        st.info("当前筛选范围内没有其他候选课程，请扩大筛选范围。")
        return
    similar = similar_courses(source_code, top_n=5, recommendation_table=candidates)
    if similar.empty:
        st.info("未找到可匹配的课程文本。")
        return
    display_table(similar)
    st.caption("相似度为 0–1 的文本余弦相似度，不代表内容等价、学分互认或推荐成功率。")
    download_csv(similar, "下载相似课程 CSV", "courseinsight_similar_courses.csv", "similar_csv")


def render_quality() -> None:
    quality = tables["quality"]
    st.subheader("数据质量 / Data quality")
    st.caption("此页展示完整数据集的最近一次检查，不受侧栏课程筛选影响。")
    if quality.empty:
        st.info("尚未找到质量报告。请运行 python run_pipeline.py 生成完整演示数据。")
        return
    pass_count = int(quality["status"].eq("PASS").sum())
    fail_count = int(quality["status"].eq("FAIL").sum())
    left, middle, right = st.columns(3)
    left.metric("检查总数", len(quality))
    middle.metric("通过 / PASS", pass_count)
    right.metric("失败 / FAIL", fail_count)
    if "check_time" in quality:
        st.caption(f"最近检查：{quality['check_time'].astype(str).max()}（UTC）")
    if fail_count:
        st.warning("存在未通过的检查，请查看失败行并修复数据后重新运行流程。")
        display_table(quality[quality["status"] == "FAIL"])
    else:
        st.success("所有已配置的数据质量检查均通过。")
    if {"check_name", "failure_rate", "status"}.issubset(quality.columns) and fail_count:
        chart = px.bar(
            quality,
            x="failure_rate",
            y="check_name",
            color="status",
            orientation="h",
            labels={"failure_rate": "失败比例", "check_name": "检查项目", "status": "状态"},
            color_discrete_map={"PASS": "#0d9488", "FAIL": "#dc2626"},
        )
        chart.update_xaxes(tickformat=".0%")
        st.plotly_chart(chart, width="stretch")
    display_table(quality)
    download_csv(quality, "下载质量报告 CSV", "courseinsight_data_quality.csv", "quality_csv")


tabs = st.tabs(["数据概览", "课程画像", "课程比较", "偏好推荐", "相似课程", "数据质量"])
for tab, render in zip(
    tabs,
    [
        render_overview,
        render_profile,
        render_comparison,
        render_recommendations,
        render_similar,
        render_quality,
    ],
):
    with tab:
        render()

st.caption("CourseInsight · Python / DuckDB / TF-IDF / Streamlit · 合成数据演示项目")
