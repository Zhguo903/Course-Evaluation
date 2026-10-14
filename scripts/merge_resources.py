#!/usr/bin/env python3
"""Merge deliberately verified resource-link batches and publish their metadata atomically."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import urldefrag
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import REFERENCE_DIR
from src.support import SUPPORT_FILES, load_support_snapshot, validate_support


def merge_resources(base: list[dict], batches: list[list[dict]]) -> list[dict]:
    """One row per campus/course/canonical URL; fragment variations are one document."""
    merged = {}
    for rows in [base, *batches]:
        for raw in rows:
            row = dict(raw)
            row["url"] = urldefrag(row["url"])[0]
            key = (row["campus"], row["course_code"], row["url"])
            previous = merged.get(key)
            if previous is None:
                # Independent batch authors may use different ID conventions.
                row["resource_id"] = "res_" + sha256("|".join(key).encode()).hexdigest()[:20]
                merged[key] = row
            elif row.get("verified_at", "") > previous.get("verified_at", ""):
                row["resource_id"] = previous["resource_id"]
                merged[key] = row
    return sorted(
        merged.values(), key=lambda row: (row["campus"], row["course_code"], row["resource_type"], row["url"])
    )


def publish(directory: Path, inputs: list[Path]) -> dict:
    # A resource-only merge cannot authenticate unrelated edits to reviews or sources.
    support, _ = load_support_snapshot(directory)
    batches = [json.loads(path.read_text()) for path in inputs]
    if not all(isinstance(batch, list) for batch in batches):
        raise ValueError("Each resource batch must be a JSON array")
    support["resources"] = merge_resources(support["resources"], batches)
    validate_support(support)
    verified_at = datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
    content = (json.dumps(support["resources"], ensure_ascii=False, indent=2) + "\n").encode()
    old_manifest_path = directory / "resource_manifest.json"
    old = json.loads(old_manifest_path.read_text()) if old_manifest_path.exists() else {}
    batch_history = {row["file"]: row for row in old.get("collection_batches", [])}
    for path, batch in zip(inputs, batches):
        batch_history[path.name] = {
            "file": path.name,
            "records_before_deduplication": len(batch),
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    specific = [row for row in support["resources"] if row["course_code"]]
    resource_manifest = {
        **old,
        "schema_version": 2,
        "verified_at": verified_at,
        "resource_count": len(support["resources"]),
        "course_specific_resource_count": len(specific),
        "distinct_course_count": len({(row["campus"], row["course_code"]) for row in specific}),
        "unique_url_count": len({row["url"] for row in support["resources"]}),
        "campus_coverage": dict(Counter(row["campus"] for row in support["resources"])),
        "course_coverage_by_campus": {
            campus: len({row["course_code"] for row in specific if row["campus"] == campus})
            for campus in sorted({row["campus"] for row in specific})
        },
        "resource_type_counts": dict(Counter(row["resource_type"] for row in support["resources"])),
        "source_kind_counts": dict(Counter(row["source_kind"] for row in support["resources"])),
        "resource_sha256": sha256(content).hexdigest(),
        "sources": sorted({row["source_url"] for row in support["resources"]}),
        "collection_batches": list(batch_history.values()),
        "scope": "Verified public-publisher metadata and original resource links; course coverage is not exhaustive. One course can have multiple types/periods; shared URLs are reported separately.",
        "content_policy": "Links and metadata only. No course, textbook, answer or exam document contents are mirrored; authenticated portals remain links.",
    }
    payloads = {
        "course_resources.json": content,
        "resource_manifest.json": (
            json.dumps(resource_manifest, ensure_ascii=False, indent=2) + "\n"
        ).encode(),
    }
    support_manifest = {
        "schema_version": 1,
        "verified_at": verified_at,
        "files": {
            key: {
                "file": name,
                "count": len(support[key]),
                "sha256": sha256(payloads.get(name, (directory / name).read_bytes())).hexdigest(),
            }
            for key, name in SUPPORT_FILES.items()
        },
        "review_policy": "Public self-reported individual opinions. Student identity is not verified. No averaging or quality ranking.",
        "resource_policy": resource_manifest["content_policy"],
    }
    payloads["support_manifest.json"] = (
        json.dumps(support_manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    originals = {
        name: (directory / name).read_bytes() if (directory / name).exists() else None for name in payloads
    }
    try:
        for name, payload in payloads.items():
            (directory / ("." + name + ".tmp")).write_bytes(payload)
        for name in payloads:
            (directory / ("." + name + ".tmp")).replace(directory / name)
    except OSError:
        for name, original in originals.items():
            path = directory / name
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        raise
    finally:
        for name in payloads:
            (directory / ("." + name + ".tmp")).unlink(missing_ok=True)
    return resource_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--directory", type=Path, default=REFERENCE_DIR)
    args = parser.parse_args()
    try:
        manifest = publish(args.directory, args.input)
    except (OSError, ValueError, KeyError) as error:
        print(f"Resource merge failed; previous snapshots retained: {error}", file=sys.stderr)
        return 1
    print(
        f"Published {manifest['resource_count']:,} resource entries, {manifest['unique_url_count']:,} unique URLs, "
        f"{manifest['distinct_course_count']:,} current courses"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
