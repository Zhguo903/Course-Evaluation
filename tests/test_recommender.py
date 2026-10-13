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


def test_unknown_counts_are_preserved_for_legacy_callers() -> None:
    result = recommend_courses(recommendation_table=_sample_table())
    assert result["review_count"].isna().all()
    assert "preference_score" in result and "course_id" in result


def test_no_review_courses_do_not_rank_as_easy() -> None:
    table = _sample_table()
    table["review_count"] = [0, 50]
    table.loc[0, "recommend_score"] = 100
    result = recommend_courses(recommendation_table=table)
    assert result["course_code"].tolist() == ["MAT235"]


def test_exam_penalty_matches_explanation_and_exact_tag() -> None:
    from src.recommender import DEFAULT_PREFERENCES

    preferences = {key: False for key in DEFAULT_PREFERENCES}
    preferences["avoid_exam_heavy"] = True
    table = _sample_table()
    table["recommend_score"] = 4.0
    table["tags"] = ["Not Exam Heavy", "Exam Heavy"]
    result = recommend_courses(preferences, recommendation_table=table)
    assert result["preference_score"].tolist() == [4.0, 2.5]
    assert "exam-heavy penalty -1.50" in result.loc[1, "recommendation_reason"]
    assert "penalty" not in result.loc[0, "recommendation_reason"]


def test_deterministic_ties_and_empty_results() -> None:
    from src.recommender import DEFAULT_PREFERENCES

    preferences = {key: False for key in DEFAULT_PREFERENCES}
    table = _sample_table().iloc[::-1]
    table["recommend_score"] = 4
    result = recommend_courses(preferences, recommendation_table=table)
    assert result["course_code"].tolist() == ["JSC370", "MAT235"]
    assert recommend_courses(recommendation_table=table.iloc[:0]).empty
    assert recommend_courses(top_n=0, recommendation_table=table).empty


def test_similarity_handles_non_default_index_and_no_overlap() -> None:
    from src.recommender import similar_courses

    table = _sample_table()
    table.index = [10, 20]
    table.loc[20, "keywords"] = "python"
    result = similar_courses("JSC370", recommendation_table=table)
    assert result["course_code"].tolist() == ["MAT235"]
    assert result.loc[0, "similarity_score"] > 0
    table.loc[20, "keywords"] = "proof"
    assert similar_courses("JSC370", recommendation_table=table).empty
    assert similar_courses("missing", recommendation_table=table).empty


def test_similarity_empty_vocabulary_is_safe() -> None:
    from src.recommender import similar_courses

    table = _sample_table()
    table[["department", "course_name", "keywords", "tags"]] = "the and"
    assert similar_courses("JSC370", recommendation_table=table).empty
