"""Real feedback must keep its provenance, scale and access limitations."""

from copy import deepcopy
import json
import shutil

import pytest

from src.config import REFERENCE_DIR
from src.support import SUPPORT_FILES, load_support_snapshot, validate_support


def test_actual_curated_snapshot_contains_source_linked_opinions_and_resources():
    data, manifest = load_support_snapshot()
    assert len(data["reviews"]) == manifest["files"]["reviews"]["count"] > 0
    assert len(data["resources"]) == manifest["files"]["resources"]["count"] > 0
    assert all(row["verification_level"] == "public_self_report" for row in data["reviews"])
    assert all(row["rating_dimension"] == "recommendation" for row in data["reviews"])
    assert len({row["reviewer_label"] for row in data["reviews"]}) == 1
    assert all(row["rating_scale_max"] == 10 for row in data["reviews"])
    assert any(row["access_requirement"] == "utorid_required" for row in data["resources"])
    assert any(row["course_code"] == "" for row in data["resources"])


def test_changed_rating_or_missing_source_cannot_publish_as_verified_feedback():
    data, _ = load_support_snapshot()
    changed = deepcopy(data)
    changed["reviews"][0]["rating"] = 11
    with pytest.raises(ValueError, match="scale"):
        validate_support(changed)
    changed["reviews"][0]["rating"] = None
    with pytest.raises(ValueError, match="numeric"):
        validate_support(changed)
    changed = deepcopy(data)
    changed["reviews"][0]["source_id"] = "uoft_index"
    with pytest.raises(ValueError, match="link-only"):
        validate_support(changed)


def test_campus_mapping_and_https_links_are_required():
    data, _ = load_support_snapshot()
    changed = deepcopy(data)
    specific = next(row for row in changed["resources"] if row["course_code"])
    specific["campus"] = "Scarborough" if specific["campus"] != "Scarborough" else "St. George"
    with pytest.raises(ValueError, match="mismatch"):
        validate_support(changed)
    changed = deepcopy(data)
    changed["resources"][0]["url"] = "javascript:alert(1)"
    with pytest.raises(ValueError, match="HTTPS"):
        validate_support(changed)
    changed = deepcopy(data)
    changed["reviews"][0]["verification_level"] = "verified_student"
    with pytest.raises(ValueError, match="identity"):
        validate_support(changed)


def test_corrupt_or_partial_support_snapshot_is_not_silently_ignored(tmp_path):
    assert load_support_snapshot(tmp_path)[0]["reviews"] == []
    for filename in [*SUPPORT_FILES.values(), "support_manifest.json"]:
        shutil.copy2(REFERENCE_DIR / filename, tmp_path / filename)
    records = json.loads((tmp_path / "student_reviews.json").read_text())
    records[0]["rating"] = 5
    (tmp_path / "student_reviews.json").write_text(json.dumps(records))
    with pytest.raises(ValueError, match="hash"):
        load_support_snapshot(tmp_path)
    (tmp_path / "student_reviews.json").unlink()
    with pytest.raises(ValueError, match="all be present"):
        load_support_snapshot(tmp_path)
