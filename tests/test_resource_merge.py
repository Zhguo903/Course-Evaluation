"""Curated link batches must deduplicate safely without damaging published snapshots."""

from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from scripts.merge_resources import merge_resources, publish
from src.config import REFERENCE_DIR
from src.support import SUPPORT_FILES, load_support_snapshot


def snapshot_copy(destination):
    for name in [*SUPPORT_FILES.values(), "support_manifest.json", "resource_manifest.json"]:
        shutil.copy2(REFERENCE_DIR / name, destination / name)


def test_fragment_duplicates_retain_newest_metadata_and_merge_is_idempotent():
    rows = json.loads((REFERENCE_DIR / "course_resources.json").read_text())
    original = next(row for row in rows if row["course_code"])
    refreshed = {**original, "url": original["url"] + "#notes", "verified_at": "2099-01-01"}
    refreshed["title"] = "Refreshed publisher metadata"
    merged = merge_resources([original], [[refreshed, original]])
    assert len(merged) == 1
    assert merged[0]["url"] == original["url"]
    assert merged[0]["title"] == refreshed["title"]
    assert merge_resources(merged, [[refreshed]]) == merged


def test_invalid_course_association_leaves_all_published_files_unchanged(tmp_path):
    snapshot_copy(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    rows = json.loads((tmp_path / "course_resources.json").read_text())
    invalid = deepcopy(next(row for row in rows if row["course_code"]))
    invalid["campus"] = "Scarborough" if invalid["campus"] != "Scarborough" else "St. George"
    batch = tmp_path / "invalid_batch.json"
    batch.write_text(json.dumps([invalid]))
    with pytest.raises(ValueError, match="mismatch"):
        publish(tmp_path, [batch])
    assert all((tmp_path / name).read_bytes() == payload for name, payload in before.items())


def test_resource_merge_cannot_reauthenticate_changed_student_reviews(tmp_path):
    snapshot_copy(tmp_path)
    reviews_path = tmp_path / "student_reviews.json"
    reviews = json.loads(reviews_path.read_text())
    reviews[0]["rating"] = 5 if reviews[0]["rating"] != 5 else 6
    reviews_path.write_text(json.dumps(reviews))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    batch = tmp_path / "empty_batch.json"
    batch.write_text("[]")
    with pytest.raises(ValueError, match="hash"):
        publish(tmp_path, [batch])
    assert all((tmp_path / name).read_bytes() == payload for name, payload in before.items())


def test_published_hashes_and_distinct_course_counts_agree(tmp_path):
    snapshot_copy(tmp_path)
    rows = json.loads((tmp_path / "course_resources.json").read_text())
    batch = tmp_path / "duplicate_batch.json"
    batch.write_text(json.dumps(rows))
    manifest = publish(tmp_path, [batch])
    data, support_manifest = load_support_snapshot(tmp_path)
    assert len(data["resources"]) == len(rows) == manifest["resource_count"]
    assert len({r["url"] for r in data["resources"]}) == manifest["unique_url_count"]
    assert (
        len({(r["campus"], r["course_code"]) for r in rows if r["course_code"]})
        == manifest["distinct_course_count"]
    )
    assert support_manifest["files"]["resources"]["count"] == len(rows)
    assert not list(Path(tmp_path).glob(".*.tmp"))


def test_partial_publication_failure_restores_resources_and_both_manifests(tmp_path, monkeypatch):
    snapshot_copy(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    batch = tmp_path / "valid_batch.json"
    batch.write_text((tmp_path / "course_resources.json").read_text())
    original_replace = Path.replace

    def fail_final_manifest(self, target):
        if self.name == ".support_manifest.json.tmp":
            raise OSError("simulated final manifest write failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_final_manifest)
    with pytest.raises(OSError, match="final manifest"):
        publish(tmp_path, [batch])
    assert all((tmp_path / name).read_bytes() == payload for name, payload in before.items())
    assert not list(Path(tmp_path).glob(".*.tmp"))
