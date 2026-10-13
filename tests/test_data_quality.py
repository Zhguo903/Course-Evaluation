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


def _valid_data() -> dict:
    return {
        "courses": pd.DataFrame(
            {
                "course_id": [1],
                "course_code": ["STA303"],
                "course_name": ["Regression"],
                "department": ["Statistics"],
                "campus": ["Main"],
                "course_level": [300],
                "credit": [0.5],
            }
        ),
        "instructors": pd.DataFrame(
            {"instructor_id": [1], "instructor_name": ["Dr. Chen"], "department": ["Statistics"]}
        ),
        "semesters": pd.DataFrame(
            {
                "semester_id": [1],
                "year": [2025],
                "term": ["Fall"],
                "start_date": ["2025-09-08"],
                "end_date": ["2025-12-20"],
            }
        ),
        "offerings": pd.DataFrame(
            {
                "offering_id": [1],
                "course_id": [1],
                "instructor_id": [1],
                "semester_id": [1],
                "capacity": [20],
                "enrolled_count": [10],
                "delivery_mode": ["Online"],
            }
        ),
        "reviews": pd.DataFrame(
            {
                "review_id": [1],
                "course_id": [1],
                "instructor_id": [1],
                "semester_id": [1],
                "rating": [4],
                "difficulty": [3],
                "workload": [3],
                "usefulness": [4],
                "review_text": ["Good regression course"],
                "review_date": ["2025-10-01"],
            }
        ),
    }


def test_valid_data_passes_quality_gate() -> None:
    from src.data_quality import assert_quality, run_data_quality_checks

    report = run_data_quality_checks(_valid_data())
    assert_quality(report)
    assert report["status"].eq("PASS").all()


def test_quality_counts_missing_and_invalid_values_and_references() -> None:
    import pytest
    from src.data_quality import DataQualityError, assert_quality, run_data_quality_checks

    data = _valid_data()
    data["reviews"] = pd.concat([data["reviews"]] * 2, ignore_index=True)
    data["reviews"].loc[0, "usefulness"] = 6
    data["reviews"].loc[1, "usefulness"] = float("nan")
    data["reviews"].loc[0, "instructor_id"] = 999
    data["reviews"].loc[1, "review_date"] = "bad"
    report = run_data_quality_checks(data).set_index("check_name")
    assert report.loc["usefulness_between_1_and_5", "failed_count"] == 2
    assert report.loc["usefulness_between_1_and_5", "total_count"] == 2
    assert report.loc["usefulness_between_1_and_5", "failure_rate"] == 1.0
    assert report.loc["review_matches_offering", "failed_count"] == 1
    assert report.loc["review_date_valid", "failed_count"] == 1
    with pytest.raises(DataQualityError, match="usefulness"):
        assert_quality(report.reset_index())


def test_quality_empty_tables_have_honest_counts_and_fail_presence() -> None:
    from src.data_quality import run_data_quality_checks

    report = run_data_quality_checks({key: value.iloc[:0] for key, value in _valid_data().items()})
    assert report["total_count"].eq(0).all()
    assert report["failed_count"].eq(0).all()
    assert report["failure_rate"].eq(0).all()
    assert report.loc[report.check_name.eq("table_row_count_gt_0"), "status"].eq("FAIL").all()


def test_enrollment_rejects_negative_and_fractional_counts() -> None:
    offerings = pd.DataFrame({"enrolled_count": [-1, 1.5, 1], "capacity": [20, 20, 0]})
    assert not check_enrollment_capacity(offerings).any()
