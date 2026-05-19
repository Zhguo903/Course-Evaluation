"""Tests for data quality rule helpers."""

import pandas as pd

from src.data_quality import check_course_code_format, check_enrollment_capacity, check_rating_range


def test_rating_range_check() -> None:
    """Rating range check should fail values outside 1 to 5."""
    reviews = pd.DataFrame({"rating": [1, 3.5, 5, 0, 6]})
    result = check_rating_range(reviews, "rating")
    assert result.tolist() == [True, True, True, False, False]


def test_course_code_format_check() -> None:
    """Course code format should require three uppercase letters and three digits."""
    courses = pd.DataFrame({"course_code": ["STA303", "CSC343", "sta303", "MAT23"]})
    result = check_course_code_format(courses)
    assert result.tolist() == [True, True, False, False]


def test_enrollment_capacity_check() -> None:
    """Enrollment check should fail rows where enrolled_count exceeds capacity."""
    offerings = pd.DataFrame({"enrolled_count": [80, 101], "capacity": [100, 100]})
    result = check_enrollment_capacity(offerings)
    assert result.tolist() == [True, False]
