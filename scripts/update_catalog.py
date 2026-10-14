"""Explicitly refresh the 200-course reference from official UofT calendars.

Usage: python scripts/update_catalog.py [--html-dir saved-official-html]
The optional directory supports parser audits/replay without network access;
filenames must match source keys printed by ``--list-sources`` (e.g.
``sg-computer-science.html``). A failed fetch or validation keeps the snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog import (  # noqa: E402
    REFERENCE_DIR,
    catalog_sources,
    parse_calendar_section,
    select_courses,
    validate_catalog,
)


def _write_temp(destination: Path, payload: bytes) -> Path:
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def refresh_catalog(
    *, html_dir: Path | None = None, output_dir: Path = REFERENCE_DIR, retrieved_at: str | None = None
) -> dict:
    retrieved_at = retrieved_at or date.today().isoformat()
    date.fromisoformat(retrieved_at)
    selected = []
    source_summaries = []
    for source in catalog_sources():
        if html_dir is not None:
            content = (html_dir / f"{source['key']}.html").read_bytes()
        else:
            request = Request(
                source["url"], headers={"User-Agent": "CourseInsight/2.1 (course metadata refresh)"}
            )
            with urlopen(request, timeout=45) as response:
                content = response.read()
            # A single request at a time; the app/pipeline never invokes this.
            time.sleep(0.25)
        records = parse_calendar_section(
            content.decode("utf-8"),
            campus=source["campus"],
            department=source["department"],
            retrieved_at=retrieved_at,
        )
        records = select_courses(records, source)
        selected.extend(records)
        source_summaries.append(
            {
                "key": source["key"],
                "url": source["url"],
                "selected_courses": len(records),
                "html_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        print(f"{source['key']}: {len(records)} verified course records")

    # Interleave subjects/campuses for useful small demonstration subsets.
    groups = [
        selected[
            sum(item["count"] for item in catalog_sources()[:index]) : sum(
                item["count"] for item in catalog_sources()[: index + 1]
            )
        ]
        for index in range(len(catalog_sources()))
    ]
    selected = [group[index] for index in range(10) for group in groups if index < len(group)]
    validate_catalog(selected, expected_count=200)
    coverage = dict(Counter(record["campus"] for record in selected))
    if coverage != {"St. George": 80, "Mississauga": 60, "Scarborough": 60}:
        raise ValueError(f"Unexpected campus coverage: {coverage}")
    payload = (json.dumps(selected, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest = {
        "schema_version": 1,
        "source_retrieved_at": retrieved_at,
        "course_count": len(selected),
        "campus_coverage": coverage,
        "scope": "Curated sample across 8 subjects and 3 campuses; not the complete university catalogue",
        "metadata_source": "official_calendar",
        "catalog_sha256": hashlib.sha256(payload).hexdigest(),
        "missing_requirements": "Empty official field means not listed, not automatically no requirement",
        "requirements": "Original calendar text, whitespace normalized; no eligibility inference",
        "review_data": "Excluded; student reviews and instructors in the demo remain synthetic",
        "sources": source_summaries,
    }
    manifest_payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # Every source and both documents are validated before either file changes.
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "uoft_courses.json"
    manifest_target = output_dir / "catalog_manifest.json"
    temporary = _write_temp(target, payload)
    manifest_temporary = _write_temp(manifest_target, manifest_payload)
    try:
        os.replace(temporary, target)
        os.replace(manifest_temporary, manifest_target)
    finally:
        temporary.unlink(missing_ok=True)
        manifest_temporary.unlink(missing_ok=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--retrieved-at", help="ISO retrieval date of archived official HTML")
    parser.add_argument("--list-sources", action="store_true")
    args = parser.parse_args()
    if args.list_sources:
        print(json.dumps(catalog_sources(), ensure_ascii=False, indent=2))
        return
    result = refresh_catalog(
        html_dir=args.html_dir, output_dir=args.output_dir, retrieved_at=args.retrieved_at
    )
    print(f"Saved {result['course_count']} verified records to {args.output_dir}")


if __name__ == "__main__":
    main()
