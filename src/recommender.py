"""Deterministic preference ranking and TF-IDF similarity for CourseInsight."""

from __future__ import annotations

from typing import Dict

import duckdb
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import join_non_empty
    from src.warehouse import build_course_profile
except ImportError:  # pragma: no cover
    from config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES
    from utils import join_non_empty
    from warehouse import build_course_profile


DEFAULT_PREFERENCES = {
    "prefer_low_workload": True,
    "prefer_high_rating": True,
    "prefer_project_based": False,
    "prefer_data_science": False,
    "prefer_gpa_friendly": False,
    "avoid_exam_heavy": False,
}
RESULT_COLUMNS = [
    "course_code",
    "course_name",
    "department",
    "avg_rating",
    "avg_difficulty",
    "avg_workload",
    "recommend_score",
    "preference_score",
    "review_count",
    "smoothed_rating",
    "confidence",
    "tags",
    "recommendation_reason",
]
SIMILARITY_COLUMNS = ["course_code", "course_name", "department", "similarity_score", "common_tags"]
DATA_DEPARTMENTS = {"Data Science", "Computer Science", "Statistics"}


def _load_course_profile() -> pd.DataFrame:
    """Load ADS, or score processed CSVs with the exact same versioned SQL."""
    if DUCKDB_PATH.exists():
        with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
            return conn.execute("SELECT * FROM ads_course_profile").df()
    courses = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["courses"])
    reviews = pd.read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["reviews"])
    metrics = (
        reviews.groupby("course_id")
        .agg(
            review_count=("review_id", "count"),
            avg_rating=("rating", "mean"),
            avg_difficulty=("difficulty", "mean"),
            avg_workload=("workload", "mean"),
            avg_usefulness=("usefulness", "mean"),
        )
        .round(3)
        .reset_index()
    )
    profile = courses.merge(metrics, on="course_id", how="left")
    profile["review_count"] = profile["review_count"].fillna(0).astype(int)
    profile["positive_review_ratio"] = (
        reviews.groupby("course_id")["rating"]
        .apply(lambda values: (values >= 4).mean())
        .reindex(profile["course_id"])
        .to_numpy()
        .round(3)
    )
    profile["negative_review_ratio"] = (
        reviews.groupby("course_id")["rating"]
        .apply(lambda values: (values <= 2).mean())
        .reindex(profile["course_id"])
        .to_numpy()
        .round(3)
    )
    return build_course_profile(profile, reviews)


def build_recommendation_table() -> pd.DataFrame:
    """Merge course metadata, observed metrics, explainable scores, tags, and keywords."""
    if DUCKDB_PATH.exists():
        # Both derived datasets come from one committed warehouse snapshot.
        with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
            conn.execute("BEGIN TRANSACTION")
            profile = conn.execute("SELECT * FROM ads_course_profile").df()
            tags = conn.execute("SELECT course_id, tags, keywords FROM dws_course_tags").df()
            conn.execute("COMMIT")
    else:
        profile = _load_course_profile()
        tags_path = PROCESSED_DATA_DIR / PROCESSED_FILES["course_tags"]
        tags = (
            pd.read_csv(tags_path)
            if tags_path.exists()
            else pd.DataFrame(columns=["course_id", "tags", "keywords"])
        )
    table = profile.merge(
        tags[["course_id", "tags", "keywords"]], on="course_id", how="left", validate="one_to_one"
    )
    table[["tags", "keywords"]] = table[["tags", "keywords"]].fillna("")
    return table.sort_values("course_code", kind="stable").reset_index(drop=True)


def _tag_set(tags: object) -> set[str]:
    if pd.isna(tags):
        return set()
    return {tag.strip().casefold() for tag in str(tags).split(",") if tag.strip()}


def _has_tag(tags: object, tag: str) -> bool:
    """Match complete comma-separated tags, with case and whitespace normalized."""
    return tag.strip().casefold() in _tag_set(tags)


def _preference_adjustments(row: pd.Series, preferences: Dict[str, bool]) -> list[tuple[str, float]]:
    """One source of truth for both numerical adjustments and their explanations."""
    adjustments = []
    if preferences.get("prefer_low_workload"):
        adjustments.append(("lower-workload preference", (6 - row["avg_workload"]) * 0.6))
    if preferences.get("prefer_high_rating"):
        adjustments.append(("rating preference", row["smoothed_rating"] * 0.5))
    if preferences.get("prefer_project_based") and _has_tag(row["tags"], "Project Based"):
        adjustments.append(("project-based tag", 1.2))
    if preferences.get("prefer_data_science") and (
        _has_tag(row["tags"], "Data Science Friendly") or row["department"] in DATA_DEPARTMENTS
    ):
        adjustments.append(("data relevance (department or tag)", 1.2))
    if preferences.get("prefer_gpa_friendly") and _has_tag(row["tags"], "GPA Friendly"):
        adjustments.append(("GPA-friendly tag", 1.0))
    if preferences.get("avoid_exam_heavy") and _has_tag(row["tags"], "Exam Heavy"):
        adjustments.append(("exam-heavy penalty", -1.5))
    return adjustments


def _recommendation_reason(row: pd.Series, preferences: Dict[str, bool]) -> str:
    """State actual score components, including penalties and limited evidence."""
    parts = [f"Base score {row['recommend_score']:.2f}"]
    parts.extend(f"{label} {amount:+.2f}" for label, amount in _preference_adjustments(row, preferences))
    if pd.notna(row["review_count"]):
        parts.append(f"{int(row['review_count'])} reviews")
        if row["review_count"] < 10:
            parts.append("limited review evidence")
    return join_non_empty(parts, sep="; ") + "."


def recommend_courses(
    preferences: Dict[str, bool] | None = None,
    top_n: int = 10,
    recommendation_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Rank reviewed courses; preference_score is an unbounded ranking heuristic."""
    preferences = {**DEFAULT_PREFERENCES, **(preferences or {})}
    table = recommendation_table.copy() if recommendation_table is not None else build_recommendation_table()
    metadata_fields = [
        "course_id",
        "course_level",
        "campus",
        "credit",
        "breadth_categories",
        "breadth_requirements",
        "requirement_system",
        "requirement_categories",
        "distribution_requirements",
        "prerequisite",
        "corequisite",
        "exclusion",
        "recommended_preparation",
        "enrolment_requirements",
        "requirement_notes",
        "prerequisite_status",
        "source_url",
        "source_retrieved_at",
        "metadata_source",
    ]
    metadata = [column for column in metadata_fields if column in table]
    columns = metadata + RESULT_COLUMNS
    if table.empty or top_n <= 0:
        return pd.DataFrame(columns=columns)
    for column in ["course_code", "course_name", "department", "tags"]:
        if column not in table:
            table[column] = ""
        table[column] = table[column].fillna("").astype(str)
    # Legacy callers may omit review_count; unknown evidence is not fabricated.
    if "review_count" not in table:
        table["review_count"] = pd.NA
    if "smoothed_rating" not in table:
        table["smoothed_rating"] = table["avg_rating"]
    if "confidence" not in table:
        table["confidence"] = pd.NA
    for column in [
        "avg_rating",
        "avg_difficulty",
        "avg_workload",
        "recommend_score",
        "smoothed_rating",
        "review_count",
    ]:
        table[column] = pd.to_numeric(table[column], errors="coerce")
    valid = table["review_count"].isna() | (table["review_count"] > 0)
    for column in ["avg_rating", "avg_difficulty", "avg_workload", "smoothed_rating"]:
        valid &= table[column].between(1, 5)
    valid &= table["recommend_score"].notna()
    table = table[valid].copy()
    table["preference_score"] = [
        row["recommend_score"] + sum(amount for _, amount in _preference_adjustments(row, preferences))
        for _, row in table.iterrows()
    ]
    table["_tie_id"] = table["course_id"].astype(str) if "course_id" in table else ""
    result = (
        table.sort_values(
            ["preference_score", "course_code", "_tie_id"], ascending=[False, True, True], kind="stable"
        )
        .head(top_n)
        .copy()
    )
    result["recommendation_reason"] = [
        _recommendation_reason(row, preferences) for _, row in result.iterrows()
    ]
    return result[columns].reset_index(drop=True)


def similar_courses(
    course_code: str, top_n: int = 5, recommendation_table: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Return only positive-overlap content matches, using positional matrix indices."""
    table = (
        recommendation_table.copy() if recommendation_table is not None else build_recommendation_table()
    ).reset_index(drop=True)
    empty = pd.DataFrame(columns=SIMILARITY_COLUMNS)
    if table.empty or top_n <= 0:
        return empty
    for column in ["course_code", "course_name", "department", "tags", "keywords"]:
        if column not in table:
            table[column] = ""
        table[column] = table[column].fillna("").astype(str)
    source = table.index[table["course_code"] == str(course_code)]
    if source.empty:
        return empty
    corpus = table[["department", "tags", "keywords", "course_name"]].agg(" ".join, axis=1)
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    except ValueError as exc:
        if "empty vocabulary" not in str(exc):
            raise
        return empty
    idx = source[0]
    table["similarity_score"] = cosine_similarity(matrix[idx], matrix).ravel()
    display_tags = {
        tag.strip().casefold(): tag.strip() for tag in table.loc[idx, "tags"].split(",") if tag.strip()
    }
    table["common_tags"] = table["tags"].apply(
        lambda tags: join_non_empty(
            display_tags[tag] for tag in sorted(set(display_tags).intersection(_tag_set(tags)))
        )
    )
    return (
        table[(table["course_code"] != str(course_code)) & (table["similarity_score"] > 0)]
        .sort_values(["similarity_score", "course_code"], ascending=[False, True], kind="stable")
        .head(top_n)[SIMILARITY_COLUMNS]
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    print(recommend_courses(DEFAULT_PREFERENCES, top_n=10))
