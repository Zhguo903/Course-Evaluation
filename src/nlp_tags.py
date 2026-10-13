"""Explainable English lexicon tags and TF-IDF keywords (not a trained NLP model)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

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
TAG_MENTION_THRESHOLD = 0.30
TAG_KEYWORDS = {
    "Project Based": ["project", "projects", "case study", "case studies"],
    "Coding Heavy": ["python", "sql", "coding", "programming", "debugging"],
    "Math Heavy": ["math", "proof", "proofs", "formula", "formulas", "calculus", "linear algebra"],
    "Exam Heavy": [
        "exam heavy",
        "exam based",
        "many exams",
        "multiple exams",
        "difficult exams",
        "exams were difficult",
        "exams were hard",
        "challenging exams",
        "midterm and final",
    ],
    "Theory Heavy": ["theory", "theoretical", "proof", "proofs", "abstract"],
    "Practical": ["practical", "useful", "case study", "case studies", "project", "projects"],
}
WORKLOAD_KEYWORDS = [
    "heavy workload",
    "workload was heavy",
    "workload is heavy",
    "time consuming",
    "heavy assignments",
    "assignments were heavy",
    "heavy problem sets",
    "problem sets were heavy",
    "too much work",
    "demanding workload",
]
DATA_KEYWORDS = ["data", "python", "sql", "project", "projects", "machine learning", "visualization"]
_NEGATORS = {
    "not",
    "no",
    "never",
    "hardly",
    "isn't",
    "wasn't",
    "weren't",
    "aren't",
    "don't",
    "doesn't",
    "didn't",
}


def clean_text(text: object) -> str:
    """Normalize English text, including hyphenated phrases, without substring matches."""
    if pd.isna(text):
        return ""
    value = str(text).lower().replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s']", " ", value)).strip()


def _phrase_polarities(text: object, phrase: str) -> tuple[int, ...]:
    """Normalize missing inputs before using a bounded cache of repeated text rules."""
    if pd.isna(text):
        return ()
    return _cached_phrase_polarities(str(text), phrase)


@lru_cache(maxsize=16384)
def _cached_phrase_polarities(text: str, phrase: str) -> tuple[int, ...]:
    """Find bounded phrases; negate within three preceding words in the same clause."""
    polarities = []
    clauses = re.split(r"[.!?;,:\n]|\b(?:but|however|yet)\b", str(text).lower())
    pattern = r"(?<!\w)" + re.escape(clean_text(phrase)) + r"(?!\w)"
    for clause in clauses:
        normalized = clean_text(clause)
        for match in re.finditer(pattern, normalized):
            preceding = normalized[: match.start()].split()[-3:]
            # 'not only practical' is affirmative, unlike 'not very practical'.
            context = " ".join(preceding).replace("not only", "only").split()
            polarities.append(-1 if any(word in _NEGATORS for word in context) else 1)
    return tuple(polarities)


def mention_ratio(texts: Iterable[object], phrases: Iterable[str]) -> float:
    """Share of non-empty reviews with an affirmed phrase; repeated words count once."""
    texts = [text for text in texts if clean_text(text)]
    phrases = tuple(phrases)
    if not texts:
        return 0.0
    return sum(any(1 in _phrase_polarities(text, phrase) for phrase in phrases) for text in texts) / len(
        texts
    )


def sentiment_label(text: object) -> str:
    """Rule sentiment with phrase boundaries and simple clause-local negation."""
    score = sum(sum(_phrase_polarities(text, word)) for word in POSITIVE_WORDS)
    score -= sum(sum(_phrase_polarities(text, word)) for word in NEGATIVE_WORDS)
    return "positive" if score > 0 else "negative" if score < 0 else "neutral"


def extract_keywords(reviews: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Extract deterministic TF-IDF keywords, retaining empty course documents."""
    grouped = (
        reviews.assign(review_text=reviews["review_text"].apply(clean_text))
        .groupby("course_id")["review_text"]
        .apply(lambda values: " ".join(values))
        .reset_index()
    )
    result = grouped[["course_id"]].copy()
    result["keywords"] = ""
    if grouped.empty or top_n <= 0:
        return result
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=300)
    try:
        matrix = vectorizer.fit_transform(grouped["review_text"])
    except ValueError as exc:
        if "empty vocabulary" not in str(exc):
            raise
        return result
    terms = vectorizer.get_feature_names_out()
    for idx in range(len(grouped)):
        row = matrix[idx].toarray().ravel()
        indices = sorted(
            (i for i, weight in enumerate(row) if weight > 0), key=lambda i: (-row[i], terms[i])
        )[:top_n]
        result.loc[idx, "keywords"] = ", ".join(terms[i] for i in indices)
    return result


def generate_course_tags(
    courses: pd.DataFrame | None = None, reviews: pd.DataFrame | None = None, output_path=None
) -> pd.DataFrame:
    """Tag by review mention share (30%), with explicit numeric evidence for GPA/workload."""
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
            positive_ratio=("sentiment", lambda values: (values == "positive").mean()),
            review_count=("review_id", "count"),
        )
        .reset_index()
    )
    review_texts = reviews.groupby("course_id")["review_text"].apply(list).to_dict()
    base = courses.merge(review_metrics, on="course_id", how="left").merge(
        extract_keywords(reviews), on="course_id", how="left"
    )
    rows = []
    for _, row in base.iterrows():
        texts = review_texts.get(row["course_id"], [])
        tags = []
        if row["avg_rating"] > 4 and row["avg_difficulty"] < 3.5:
            tags.append("GPA Friendly")
        if row["avg_workload"] > 4 or mention_ratio(texts, WORKLOAD_KEYWORDS) >= TAG_MENTION_THRESHOLD:
            tags.append("Heavy Workload")
        for tag, words in TAG_KEYWORDS.items():
            if mention_ratio(texts, words) >= TAG_MENTION_THRESHOLD:
                tags.append(tag)
        if (
            row["department"] in {"Data Science", "Computer Science", "Statistics"}
            and mention_ratio(texts, DATA_KEYWORDS) >= TAG_MENTION_THRESHOLD
        ):
            tags.append("Data Science Friendly")
        if row["avg_rating"] >= 4.1 and row["positive_ratio"] >= 0.35:
            tags.append("Good Instructor")
        rows.append(
            {
                "course_id": row["course_id"],
                "course_code": row["course_code"],
                "course_name": row["course_name"],
                "department": row["department"],
                "keywords": row["keywords"] if pd.notna(row["keywords"]) else "",
                "tags": ", ".join(tags),
            }
        )
    tags_df = pd.DataFrame(
        rows, columns=["course_id", "course_code", "course_name", "department", "keywords", "tags"]
    )
    write_csv(tags_df, output_path)
    log_step(f"Course tags saved to {output_path}")
    return tags_df


if __name__ == "__main__":
    generate_course_tags()
