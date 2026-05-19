"""Course recommendation and similarity logic for CourseInsight."""

from __future__ import annotations

from typing import Dict, Iterable, List

import duckdb
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import join_non_empty
except ImportError:  # pragma: no cover
    from config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES
    from utils import join_non_empty


DEFAULT_PREFERENCES = {
    "prefer_low_workload": True,
    "prefer_high_rating": True,
    "prefer_project_based": False,
    "prefer_data_science": False,
    "prefer_gpa_friendly": False,
    "avoid_exam_heavy": False,
}


def _load_course_profile() -> pd.DataFrame:
    """Load ADS course profile from DuckDB or derive a fallback from processed CSVs."""
    if DUCKDB_PATH.exists():
        with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
            return conn.execute("SELECT * FROM ads_course_profile").df()

    courses = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["courses"])
    reviews = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["reviews"])
    metrics = (
        reviews.groupby("course_id")
        .agg(
            avg_rating=("rating", "mean"),
            avg_difficulty=("difficulty", "mean"),
            avg_workload=("workload", "mean"),
            avg_usefulness=("usefulness", "mean"),
        )
        .reset_index()
    )
    profile = courses.merge(metrics, on="course_id", how="left").fillna(0)
    profile["gpa_friendly_score"] = (
        0.4 * profile["avg_rating"] + 0.3 * (5 - profile["avg_difficulty"]) + 0.3 * (5 - profile["avg_workload"])
    )
    profile["course_value_score"] = profile["avg_usefulness"] / profile["avg_workload"].replace(0, pd.NA)
    profile["data_career_relevance_score"] = profile["department"].isin(
        ["Data Science", "Computer Science", "Statistics"]
    ).map({True: 4.0, False: 2.0})
    profile["recommend_score"] = (
        0.25 * profile["avg_rating"]
        + 0.20 * profile["gpa_friendly_score"]
        + 0.20 * profile["data_career_relevance_score"]
        + 0.15 * profile["course_value_score"].fillna(0)
        + 0.10 * profile["avg_usefulness"]
        + 0.10 * (5 - profile["avg_workload"])
    )
    return profile


def build_recommendation_table() -> pd.DataFrame:
    """Merge course profiles, tags, and keywords into a recommendation-ready table."""
    profile = _load_course_profile()
    tags_path = PROCESSED_DATA_DIR / PROCESSED_FILES["course_tags"]
    tags = pd.read_csv(tags_path) if tags_path.exists() else pd.DataFrame(columns=["course_id", "tags", "keywords"])
    table = profile.merge(tags[["course_id", "tags", "keywords"]], on="course_id", how="left")
    table["tags"] = table["tags"].fillna("")
    table["keywords"] = table["keywords"].fillna("")
    return table


def _has_tag(tags: str, tag: str) -> bool:
    """Return whether a comma-separated tag string contains a specific tag."""
    return tag.lower() in str(tags).lower()


def _recommendation_reason(row: pd.Series, preferences: Dict[str, bool]) -> str:
    """Generate a concise human-readable recommendation reason."""
    reasons: List[str] = []
    if preferences.get("prefer_high_rating") and row["avg_rating"] >= 4:
        reasons.append("high rating")
    if preferences.get("prefer_low_workload") and row["avg_workload"] <= 3.2:
        reasons.append("manageable workload")
    if preferences.get("prefer_project_based") and _has_tag(row["tags"], "Project Based"):
        reasons.append("project-based content")
    if preferences.get("prefer_data_science") and (
        _has_tag(row["tags"], "Data Science Friendly") or row["department"] in {"Data Science", "Computer Science", "Statistics"}
    ):
        reasons.append("strong data science relevance")
    if preferences.get("prefer_gpa_friendly") and _has_tag(row["tags"], "GPA Friendly"):
        reasons.append("GPA-friendly profile")
    if not reasons:
        reasons.append("balanced rating, usefulness, and workload metrics")
    return "Recommended because this course has " + join_non_empty(reasons) + "."


def recommend_courses(
    preferences: Dict[str, bool] | None = None,
    top_n: int = 10,
    recommendation_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return top N recommended courses based on explicit user preferences."""
    preferences = {**DEFAULT_PREFERENCES, **(preferences or {})}
    table = recommendation_table.copy() if recommendation_table is not None else build_recommendation_table()
    table["preference_score"] = table["recommend_score"].fillna(0)

    if preferences.get("prefer_low_workload"):
        table["preference_score"] += (5 - table["avg_workload"].fillna(5)) * 0.6
    if preferences.get("prefer_high_rating"):
        table["preference_score"] += table["avg_rating"].fillna(0) * 0.5
    if preferences.get("prefer_project_based"):
        table["preference_score"] += table["tags"].apply(lambda tags: 1.2 if _has_tag(tags, "Project Based") else 0)
    if preferences.get("prefer_data_science"):
        table["preference_score"] += table.apply(
            lambda row: 1.2
            if _has_tag(row["tags"], "Data Science Friendly")
            or row["department"] in {"Data Science", "Computer Science", "Statistics"}
            else 0,
            axis=1,
        )
    if preferences.get("prefer_gpa_friendly"):
        table["preference_score"] += table["tags"].apply(lambda tags: 1.0 if _has_tag(tags, "GPA Friendly") else 0)
    if preferences.get("avoid_exam_heavy"):
        table["preference_score"] -= table["tags"].apply(lambda tags: 1.5 if _has_tag(tags, "Exam Heavy") else 0)

    result = table.sort_values("preference_score", ascending=False).head(top_n).copy()
    result["recommendation_reason"] = result.apply(lambda row: _recommendation_reason(row, preferences), axis=1)
    columns = [
        "course_code",
        "course_name",
        "department",
        "avg_rating",
        "avg_difficulty",
        "avg_workload",
        "recommend_score",
        "tags",
        "recommendation_reason",
    ]
    return result[columns].reset_index(drop=True)


def similar_courses(
    course_code: str,
    top_n: int = 5,
    recommendation_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Recommend similar courses using TF-IDF over tags, keywords, and department."""
    table = recommendation_table.copy() if recommendation_table is not None else build_recommendation_table()
    table["course_code"] = table["course_code"].astype(str)
    if course_code not in set(table["course_code"]):
        return pd.DataFrame(columns=["course_code", "course_name", "department", "similarity_score", "common_tags"])

    corpus = (
        table["department"].fillna("")
        + " "
        + table["tags"].fillna("")
        + " "
        + table["keywords"].fillna("")
        + " "
        + table["course_name"].fillna("")
    )
    matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    idx = table.index[table["course_code"] == course_code][0]
    scores = cosine_similarity(matrix[idx], matrix).ravel()
    table = table.copy()
    table["similarity_score"] = scores
    source_tags = {tag.strip() for tag in str(table.loc[idx, "tags"]).split(",") if tag.strip()}
    table["common_tags"] = table["tags"].apply(
        lambda tags: join_non_empty(sorted(source_tags.intersection({tag.strip() for tag in str(tags).split(",") if tag.strip()})))
    )
    return (
        table[table["course_code"] != course_code]
        .sort_values("similarity_score", ascending=False)
        .head(top_n)[["course_code", "course_name", "department", "similarity_score", "common_tags"]]
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    print(recommend_courses(DEFAULT_PREFERENCES, top_n=10))
