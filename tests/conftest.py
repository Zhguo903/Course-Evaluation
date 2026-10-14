"""Small fixtures taken from the versioned official catalogue, never generated ratings."""

import hashlib
import json

import pytest

from src.catalog import load_catalog


@pytest.fixture
def official_sample():
    records = load_catalog()
    return [
        next(row for row in records if row["campus"] == campus)
        for campus in ["St. George", "Mississauga", "Scarborough"]
    ]


@pytest.fixture
def sample_manifest(official_sample):
    payload = json.dumps(official_sample).encode()
    return {
        "complete": True,
        "course_count": len(official_sample),
        "campus_coverage": {"St. George": 1, "Mississauga": 1, "Scarborough": 1},
        "catalog_sha256": hashlib.sha256(payload).hexdigest(),
    }
