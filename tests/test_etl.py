"""Tests for ETL cleaning functions."""

import pandas as pd

from src.etl import clean_courses, clean_reviews


def test_clean_courses_standardizes_course_code() -> None:
    """clean_courses should uppercase course_code and remove spaces."""
    raw = pd.DataFrame(
        {
            "course_id": [1],
            "course_code": [" sta 303 "],
            "course_name": ["Regression"],
            "department": [" Statistics "],
            "course_level": ["300"],
            "credit": ["0.5"],
            "prerequisite": [""],
            "campus": ["St. George"],
        }
    )
    cleaned = clean_courses(raw)
    assert cleaned.loc[0, "course_code"] == "STA303"


def test_clean_reviews_clips_scores_to_one_to_five() -> None:
    """clean_reviews should clip score columns into the 1 to 5 range."""
    raw = pd.DataFrame(
        {
            "review_id": [1, 2],
            "course_id": [1, 1],
            "instructor_id": [1, 1],
            "semester_id": [1, 1],
            "rating": [0, 6],
            "difficulty": [9, -2],
            "workload": [7, 3],
            "usefulness": [5, 0],
            "review_text": ["Great", "Hard"],
            "review_date": ["2025-01-01", "2025-01-02"],
        }
    )
    cleaned = clean_reviews(raw)
    assert cleaned["rating"].between(1, 5).all()
    assert cleaned["difficulty"].between(1, 5).all()
    assert cleaned["workload"].between(1, 5).all()
    assert cleaned["usefulness"].between(1, 5).all()


def test_clean_reviews_removes_duplicate_review_id() -> None:
    """clean_reviews should keep one row for duplicated review IDs."""
    raw = pd.DataFrame(
        {
            "review_id": [1, 1],
            "course_id": [1, 1],
            "instructor_id": [1, 1],
            "semester_id": [1, 1],
            "rating": [4, 5],
            "difficulty": [3, 2],
            "workload": [3, 2],
            "usefulness": [4, 5],
            "review_text": ["Good", "Great"],
            "review_date": ["2025-01-01", "2025-01-02"],
        }
    )
    cleaned = clean_reviews(raw)
    assert len(cleaned) == 1
