"""Synthetic data must support honest, reproducible demo recommendations."""

import random

import numpy as np
import pandas as pd

from src.data_quality import assert_quality, run_data_quality_checks
from src.generate_mock_data import (
    RANDOM_SEED,
    generate_courses,
    generate_instructors,
    generate_offerings,
    generate_reviews,
    generate_semesters,
)


def _generate() -> dict:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    courses = generate_courses()
    instructors = generate_instructors()
    semesters = generate_semesters()
    offerings = generate_offerings(courses, instructors, semesters)
    reviews = generate_reviews(courses, offerings, semesters)
    return dict(
        courses=courses, instructors=instructors, semesters=semesters, offerings=offerings, reviews=reviews
    )


def test_default_generation_is_reproducible_complete_and_clean() -> None:
    first, second = _generate(), _generate()
    for key in first:
        pd.testing.assert_frame_equal(first[key], second[key])
    assert {key: len(value) for key, value in first.items()} == {
        "courses": 200,
        "instructors": 60,
        "semesters": 8,
        "offerings": 800,
        "reviews": 12000,
    }
    assert first["offerings"].course_id.nunique() == 200
    assert_quality(run_data_quality_checks(first))


def test_review_text_and_scores_are_course_specific() -> None:
    data = _generate()
    course_names = data["courses"].set_index("course_id").course_name
    assert all(course_names.loc[row.course_id] in row.review_text for row in data["reviews"].itertuples())
    course_means = data["reviews"].groupby("course_id")[["difficulty", "workload"]].mean()
    assert course_means["difficulty"].std() > 0.5
    assert course_means["workload"].std() > 0.4
    heavy = data["reviews"].loc[data["reviews"].workload >= 3.8]
    assert heavy.review_text.str.contains("Heavy workload").all()


def test_default_courses_use_verified_three_campus_catalog_metadata() -> None:
    import json

    courses = generate_courses()
    assert courses["metadata_source"].eq("official_calendar").all()
    assert courses["campus"].value_counts().to_dict() == {
        "St. George": 80,
        "Mississauga": 60,
        "Scarborough": 60,
    }
    assert set(courses["requirement_system"]) == {"artsci_breadth", "utm_distribution", "utsc_breadth"}
    assert (
        courses["course_code"].str.fullmatch(r"(?:[A-Z]{3}[1-4]\d{2}[HY][15]|[A-Z]{3}[A-D]\d{2}[HY]3)").all()
    )
    assert courses["source_url"].str.startswith("https://").all()
    assert courses["source_retrieved_at"].notna().all()
    for row in courses.itertuples():
        categories = json.loads(row.breadth_categories)
        assert isinstance(categories, list)
        assert all(type(category) is int and 1 <= category <= 5 for category in categories)
        assert row.campus == "St. George" or not categories
        assert (row.prerequisite_status == "listed") == bool(row.prerequisite)


def test_catalog_subsets_never_fabricate_extra_courses() -> None:
    import pytest

    full = generate_courses()
    pd.testing.assert_frame_equal(generate_courses(7), full.iloc[:7])
    assert generate_courses(0).empty
    with pytest.raises(ValueError, match="n_courses"):
        generate_courses(201)


def test_synthetic_reviews_are_explicit_about_source_limitations() -> None:
    data = _generate()
    assert data["reviews"].data_source.eq("synthetic_community_inspired").all()
    assert (
        data["reviews"]
        .source_note.str.contains(
            "no original group messages or real review records are ingested", regex=False
        )
        .all()
    )
