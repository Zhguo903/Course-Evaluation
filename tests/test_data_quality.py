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


def test_course_codes_support_all_three_campuses_and_legacy_imports() -> None:
    courses = pd.DataFrame(
        {
            "course_code": [
                "STA130H1",
                "ENG100Y1",
                "CSC108H5",
                "CSCA08H3",
                "ENGB04H3",
                "STA303",
                "CSCE08H3",
                "CSC108H2",
                "sta130h1",
            ]
        }
    )
    assert check_course_code_format(courses).tolist() == [
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
    ]


def _official_data() -> dict:
    data = _valid_data()
    data["courses"] = pd.DataFrame(
        {
            "course_id": [1, 2, 3],
            "course_code": ["STA130H1", "CSC108H5", "CSCA08H3"],
            "course_name": [
                "Introduction to Statistical Reasoning",
                "Introduction to Computer Programming",
                "Introduction to Computer Science I",
            ],
            "department": ["Statistics", "Computer Science", "Computer Science"],
            "course_level": [100, 100, 100],
            "credit": [0.5, 0.5, 0.5],
            "campus": ["St. George", "Mississauga", "Scarborough"],
            "metadata_source": ["official_calendar"] * 3,
            "source_retrieved_at": ["2026-10-13"] * 3,
            "source_url": [
                "https://artsci.calendar.utoronto.ca/course/sta130h1",
                "https://utm.calendar.utoronto.ca/course/csc108h5",
                "https://utsc.calendar.utoronto.ca/course/csca08h3",
            ],
            "breadth_categories": ["[5]", "[]", "[]"],
            "requirement_system": ["artsci_breadth", "utm_distribution", "utsc_breadth"],
            "requirement_categories": [
                '["The Physical and Mathematical Universes (5)"]',
                '["Science"]',
                '["Quantitative Reasoning"]',
            ],
            "breadth_requirements": [
                "The Physical and Mathematical Universes (5)",
                "",
                "Quantitative Reasoning",
            ],
            "distribution_requirements": ["", "Science", ""],
            "corequisite": [""] * 3,
            "exclusion": [""] * 3,
            "recommended_preparation": [""] * 3,
            "enrolment_requirements": [""] * 3,
            "requirement_notes": [""] * 3,
            "prerequisite": ["", "", "MHF4U or equivalent"],
            "prerequisite_status": ["not_listed", "not_listed", "listed"],
        }
    )
    return data


def test_official_course_metadata_passes_with_campus_specific_requirements() -> None:
    from src.data_quality import assert_quality, run_data_quality_checks

    assert_quality(run_data_quality_checks(_official_data()))


def test_official_metadata_rejects_wrong_campus_provenance_and_br_system() -> None:
    from src.data_quality import run_data_quality_checks

    data = _official_data()
    data["courses"].loc[0, "source_url"] = "https://example.com/course/sta130h1"
    data["courses"].loc[0, "source_retrieved_at"] = "invalid"
    data["courses"].loc[1, "breadth_categories"] = "[5]"
    data["courses"].loc[1, "requirement_system"] = "artsci_breadth"
    data["courses"].loc[2, "prerequisite_status"] = "not_listed"
    report = run_data_quality_checks(data).set_index("check_name")
    for check in [
        "official_course_source_url",
        "official_source_retrieved_at",
        "official_sg_breadth_categories_only",
        "official_requirement_system",
        "official_prerequisite_status",
    ]:
        assert report.loc[check, "failed_count"] == 1


def test_breadth_metadata_rejects_out_of_range_and_non_integer_ids() -> None:
    from src.data_quality import run_data_quality_checks

    data = _official_data()
    data["courses"]["breadth_categories"] = ["[0,6]", '["5"]', "[true]"]
    report = run_data_quality_checks(data).set_index("check_name")
    assert report.loc["breadth_categories_valid", "failed_count"] == 3


def test_official_metadata_rejects_category_labels_and_ids_mismatching_literal_text() -> None:
    from src.data_quality import run_data_quality_checks

    data = _official_data()
    # Genuine official links cannot make imported category labels authoritative.
    data["courses"].loc[0, "breadth_categories"] = "[1]"
    data["courses"].loc[0, "requirement_categories"] = '["Creative and Cultural Representations (1)"]'
    data["courses"].loc[1, "requirement_categories"] = '["Quantitative Reasoning"]'
    data["courses"].loc[2, "requirement_categories"] = '["Science"]'
    report = run_data_quality_checks(data).set_index("check_name")
    assert report.loc["official_course_source_url", "status"] == "PASS"
    assert report.loc["official_requirement_categories", "status"] == "PASS"
    assert report.loc["official_metadata_consistent", "failed_count"] == 3
    assert report.loc["official_metadata_consistent", "status"] == "FAIL"


def test_official_metadata_validation_preserves_grade_and_or_credit_and_consent_text() -> None:
    from src.data_quality import assert_quality, run_data_quality_checks
    from src.etl import clean_courses

    data = _official_data()
    requirement = "(A minimum of 60% in CSC108H5 AND MAT102H5) OR 4.0 credits and consent of the department."
    data["courses"].loc[1, "prerequisite"] = requirement
    data["courses"].loc[1, "prerequisite_status"] = "listed"
    data["courses"] = clean_courses(data["courses"])
    assert_quality(run_data_quality_checks(data))
    assert data["courses"].loc[1, "prerequisite"] == requirement


def test_official_metadata_consistency_survives_csv_empty_requirement_fields() -> None:
    from io import StringIO
    from src.data_quality import assert_quality, run_data_quality_checks

    data = _official_data()
    buffer = StringIO()
    data["courses"].to_csv(buffer, index=False)
    buffer.seek(0)
    data["courses"] = pd.read_csv(buffer)
    assert_quality(run_data_quality_checks(data))


def test_legacy_missing_metadata_source_does_not_trigger_official_checks() -> None:
    from src.data_quality import assert_quality, run_data_quality_checks

    data = _valid_data()
    data["courses"]["metadata_source"] = pd.NA
    assert_quality(run_data_quality_checks(data))
