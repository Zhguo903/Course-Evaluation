"""Lightweight NLP keyword extraction, sentiment labels, and course tags."""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from src.config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from src.utils import log_step, read_csv, write_csv
except ImportError:  # pragma: no cover
    from config import PROCESSED_DATA_DIR, PROCESSED_FILES
    from utils import log_step, read_csv, write_csv


POSITIVE_WORDS = {
    "useful",
    "clear",
    "practical",
    "fair",
    "interesting",
    "helpful",
    "good",
    "great",
    "manageable",
}

NEGATIVE_WORDS = {
    "hard",
    "difficult",
    "heavy",
    "unclear",
    "confusing",
    "stressful",
    "time consuming",
    "boring",
}

TAG_KEYWORDS = {
    "Project Based": ["project", "practical", "case study"],
    "Coding Heavy": ["python", "sql", "coding", "programming", "debugging"],
    "Math Heavy": ["math", "proof", "formula", "calculus", "linear algebra"],
    "Exam Heavy": ["exam", "exams", "midterm", "final"],
    "Theory Heavy": ["theory", "theoretical", "proof", "abstract"],
    "Practical": ["practical", "useful", "case study", "project"],
}


def clean_text(text: object) -> str:
    """Clean text for NLP analysis with simple English normalization."""
    if pd.isna(text):
        return ""
    value = str(text).lower()
    value = re.sub(r"[^a-z0-9\s'-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def sentiment_label(text: object) -> str:
    """Assign a simple positive, negative, or neutral label using keyword rules."""
    cleaned = clean_text(text)
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in cleaned)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in cleaned)
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"


def extract_keywords(reviews: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Extract top TF-IDF keywords for each course from review text."""
    grouped = (
        reviews.assign(review_text=reviews["review_text"].apply(clean_text))
        .groupby("course_id")["review_text"]
        .apply(lambda values: " ".join(values))
        .reset_index()
    )
    if grouped.empty:
        return pd.DataFrame(columns=["course_id", "keywords"])
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=300)
    matrix = vectorizer.fit_transform(grouped["review_text"])
    terms = vectorizer.get_feature_names_out()
    keyword_rows = []
    for idx, course_id in enumerate(grouped["course_id"]):
        row = matrix[idx].toarray().ravel()
        top_indices = row.argsort()[::-1][:top_n]
        keywords = [terms[i] for i in top_indices if row[i] > 0]
        keyword_rows.append({"course_id": course_id, "keywords": ", ".join(keywords)})
    return pd.DataFrame(keyword_rows)


def _word_frequency(texts: Iterable[str]) -> Counter:
    """Count normalized word and phrase occurrences in a collection of texts."""
    joined = " ".join(clean_text(text) for text in texts)
    counts = Counter(joined.split())
    for phrase in ["time consuming", "case study", "machine learning", "data science"]:
        counts[phrase] = joined.count(phrase)
    return counts


def _contains_any(counts: Counter, words: List[str], min_count: int = 2) -> bool:
    """Return whether any configured keyword reaches the minimum frequency."""
    return any(counts.get(word, 0) >= min_count for word in words)


def generate_course_tags(
    courses: pd.DataFrame | None = None,
    reviews: pd.DataFrame | None = None,
    output_path=None,
) -> pd.DataFrame:
    """Generate tags and keywords for each course and save them to processed data."""
    if courses is None:
        courses = read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["courses"])
    if reviews is None:
        reviews = read_csv(PROCESSED_DATA_DIR / PROCESSED_FILES["reviews"])
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / PROCESSED_FILES["course_tags"]

    review_metrics = (
        reviews.assign(sentiment=reviews["review_text"].apply(sentiment_label))
        .groupby("course_id")
        .agg(
            avg_rating=("rating", "mean"),
            avg_difficulty=("difficulty", "mean"),
            avg_workload=("workload", "mean"),
            positive_ratio=("sentiment", lambda s: (s == "positive").mean()),
            review_count=("review_id", "count"),
        )
        .reset_index()
    )
    keywords = extract_keywords(reviews)
    review_texts: Dict[int, List[str]] = reviews.groupby("course_id")["review_text"].apply(list).to_dict()
    base = courses.merge(review_metrics, on="course_id", how="left").merge(keywords, on="course_id", how="left")

    rows = []
    for _, row in base.iterrows():
        counts = _word_frequency(review_texts.get(row["course_id"], []))
        tags: list[str] = []
        avg_rating = row.get("avg_rating", 0) if pd.notna(row.get("avg_rating", 0)) else 0
        avg_difficulty = row.get("avg_difficulty", 0) if pd.notna(row.get("avg_difficulty", 0)) else 0
        avg_workload = row.get("avg_workload", 0) if pd.notna(row.get("avg_workload", 0)) else 0
        department = str(row["department"])

        if avg_rating > 4 and avg_difficulty < 3.5:
            tags.append("GPA Friendly")
        if avg_workload > 4 or _contains_any(counts, ["heavy", "workload", "time consuming"], min_count=4):
            tags.append("Heavy Workload")
        for tag, words in TAG_KEYWORDS.items():
            if _contains_any(counts, words, min_count=2):
                tags.append(tag)
        if department in {"Data Science", "Computer Science", "Statistics"} and _contains_any(
            counts, ["data", "python", "sql", "project", "machine learning"], min_count=2
        ):
            tags.append("Data Science Friendly")
        if avg_rating >= 4.1 and row.get("positive_ratio", 0) >= 0.35:
            tags.append("Good Instructor")

        rows.append(
            {
                "course_id": row["course_id"],
                "course_code": row["course_code"],
                "course_name": row["course_name"],
                "department": department,
                "keywords": row.get("keywords", ""),
                "tags": ", ".join(dict.fromkeys(tags)),
            }
        )

    tags_df = pd.DataFrame(rows)
    write_csv(tags_df, output_path)
    log_step(f"Course tags saved to {output_path}")
    return tags_df


if __name__ == "__main__":
    generate_course_tags()
