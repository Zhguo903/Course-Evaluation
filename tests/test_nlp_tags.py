"""Regression tests for review-volume independent, phrase-aware rule tags."""

import pandas as pd

from src.nlp_tags import extract_keywords, generate_course_tags, mention_ratio, sentiment_label


def test_phrase_boundaries_and_negation() -> None:
    assert sentiment_label("The lecture was unclear.") == "negative"
    assert sentiment_label("Not difficult, but useful.") == "positive"
    assert sentiment_label("Not useful.") == "negative"
    assert sentiment_label("Not only useful but practical.") == "positive"
    assert mention_ratio(["No coding is required", "encoding techniques"], ["coding"]) == 0
    assert mention_ratio(["a time-consuming workload"], ["time consuming"]) == 1


def test_mention_proportion_does_not_reward_repetition() -> None:
    texts = ["project " * 20, "a clear lecture", "a useful lecture", "a fair lecture"]
    assert mention_ratio(texts, ["project"]) == 0.25
    assert mention_ratio(texts * 10, ["project"]) == 0.25


def test_empty_and_stopword_corpora_keep_course_ids() -> None:
    reviews = pd.DataFrame({"course_id": [1, 2], "review_text": [None, "the and is"]})
    result = extract_keywords(reviews)
    assert result["course_id"].tolist() == [1, 2]
    assert result["keywords"].tolist() == ["", ""]
    assert extract_keywords(reviews.iloc[:0]).empty


def test_workload_word_alone_and_no_reviews_do_not_generate_tags(tmp_path) -> None:
    courses = pd.DataFrame(
        {
            "course_id": [1, 2],
            "course_code": ["A", "B"],
            "course_name": ["Alpha", "Beta"],
            "department": ["Statistics"] * 2,
        }
    )
    reviews = pd.DataFrame(
        {
            "course_id": [1] * 4,
            "review_id": range(4),
            "rating": [3] * 4,
            "difficulty": [3] * 4,
            "workload": [3] * 4,
            "review_text": [
                "The workload was manageable. A project project project.",
                "The workload was manageable.",
                "No coding required.",
                "Clear lectures.",
            ],
        }
    )
    result = generate_course_tags(courses, reviews, tmp_path / "tags.csv")
    assert "Heavy Workload" not in result.loc[0, "tags"]
    assert "Project Based" not in result.loc[0, "tags"]
    assert "Coding Heavy" not in result.loc[0, "tags"]
    assert result.loc[1, "tags"] == ""
