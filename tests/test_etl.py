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


def test_clean_reviews_preserves_invalid_scores_for_quality_report() -> None:
    """Invalid source scores must be visible to quality checks."""
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
    assert cleaned["rating"].tolist() == [0, 6]
    assert cleaned["difficulty"].tolist() == [9, -2]
    assert cleaned["workload"].tolist() == [7, 3]
    assert cleaned["usefulness"].tolist() == [5, 0]


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


def test_null_fields_and_fractional_ids_remain_invalid() -> None:
    from src.etl import clean_semesters

    raw = pd.DataFrame(
        {
            "semester_id": [None, 1.5, 2],
            "year": [2025, "bad", 2025],
            "term": [None, "NaN", " fall "],
            "start_date": [None, "bad", "2025-09-08"],
            "end_date": ["bad", None, "2025-12-20"],
        }
    )
    cleaned = clean_semesters(raw)
    assert len(cleaned) == 3  # Missing keys are counted by quality checks.
    assert cleaned["semester_id"].isna().tolist() == [True, True, False]
    assert cleaned["term"].isna().tolist() == [True, True, False]
    assert cleaned["start_date"].isna().tolist() == [True, True, False]
    assert cleaned.loc[2, "term"] == "Fall"


def test_offerings_do_not_fabricate_zero_ids_or_delivery_modes() -> None:
    from src.etl import clean_offerings

    raw = pd.DataFrame(
        {
            "offering_id": [1, 1, None, None],
            "course_id": [1, 2, None, "bad"],
            "instructor_id": [1] * 4,
            "semester_id": [1] * 4,
            "capacity": [20, 20, "bad", None],
            "enrolled_count": [10] * 4,
            "delivery_mode": [" in_person ", "Online", "telepathy", None],
        }
    )
    cleaned = clean_offerings(raw)
    assert len(cleaned) == 3
    assert cleaned.loc[0, "course_id"] == 1  # First duplicate wins deterministically.
    assert cleaned.loc[0, "delivery_mode"] == "In-person"
    assert cleaned["delivery_mode"].isna().tolist() == [False, True, True]
    assert cleaned["course_id"].isna().tolist() == [False, True, True]


def test_mixed_iso_dates_preserve_valid_values_and_missing():
    from src.etl import _dates

    result = _dates(pd.Series(["2025-01-02", "2025-01-03T14:30:00Z", None, "invalid"]))
    assert result.iloc[:2].tolist() == ["2025-01-02", "2025-01-03"]
    assert result.iloc[2:].isna().all()
