"""Tests for recommendation logic."""

import pandas as pd

from src.recommender import recommend_courses


def _sample_table() -> pd.DataFrame:
    """Return a small recommendation table for unit tests."""
    return pd.DataFrame(
        {
            "course_id": [1, 2],
            "course_code": ["JSC370", "MAT235"],
            "course_name": ["Data Science Project", "Calculus"],
            "department": ["Data Science", "Mathematics"],
            "avg_rating": [4.5, 3.4],
            "avg_difficulty": [3.0, 4.2],
            "avg_workload": [3.1, 4.4],
            "avg_usefulness": [4.6, 3.5],
            "recommend_score": [4.3, 2.8],
            "tags": ["Project Based, Data Science Friendly", "Exam Heavy, Math Heavy"],
            "keywords": ["python, project, data", "proof, exam, formula"],
        }
    )


def test_recommend_courses_returns_non_empty_results() -> None:
    """recommend_courses should return at least one course for valid input."""
    result = recommend_courses(
        {"prefer_project_based": True, "prefer_data_science": True},
        top_n=1,
        recommendation_table=_sample_table(),
    )
    assert not result.empty


def test_recommendation_reason_not_empty() -> None:
    """recommend_courses should include a non-empty recommendation reason."""
    result = recommend_courses(
        {"prefer_project_based": True, "prefer_data_science": True},
        top_n=1,
        recommendation_table=_sample_table(),
    )
    assert result.loc[0, "recommendation_reason"]
