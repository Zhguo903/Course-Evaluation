"""Fail closed on unverified catalogue completeness and fabricated rating fields."""

from copy import deepcopy

import pytest

from src.data_quality import DataQualityError, assert_quality, run_data_quality_checks


def test_official_sample_passes_all_checks(official_sample, sample_manifest):
    report = run_data_quality_checks(official_sample, sample_manifest)
    assert_quality(report)
    assert report.status.eq("PASS").all()


def test_incomplete_manifest_is_rejected(official_sample, sample_manifest):
    sample_manifest["complete"] = False
    with pytest.raises(DataQualityError, match="complete_catalogue_source"):
        assert_quality(run_data_quality_checks(official_sample, sample_manifest))


def test_ratings_cannot_sneak_into_catalogue(official_sample, sample_manifest):
    courses = deepcopy(official_sample)
    courses[0]["avg_rating"] = 4.9
    report = run_data_quality_checks(courses, sample_manifest)
    with pytest.raises(DataQualityError, match="no_simulated_rating_fields"):
        assert_quality(report)


def test_counts_and_source_hash_are_checked(official_sample, sample_manifest):
    report = run_data_quality_checks(official_sample, sample_manifest, b"different payload")
    assert report.set_index("check_name").loc["catalogue_hash_matches", "status"] == "FAIL"
    sample_manifest["campus_coverage"]["St. George"] = 2
    report = run_data_quality_checks(official_sample, sample_manifest)
    assert report.set_index("check_name").loc["three_campus_counts_match", "status"] == "FAIL"
