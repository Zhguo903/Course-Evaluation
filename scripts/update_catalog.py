"""Refresh complete official UofT undergraduate calendar catalogues.

Unfiltered print exports provide every course in three requests. For each campus,
we verify the first/last search pages, page size and last-page index against the
export. Official sitemap subject sections supply academic-area labels. Neither
sampling nor synthetic course/review data is used. All validation finishes before
the offline snapshot is replaced.

Usage: python scripts/update_catalog.py [--html-dir archived-official-html]
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog import (  # noqa: E402
    REFERENCE_DIR,
    catalog_sources,
    course_headers,
    parse_calendar_section,
    search_last_page,
    section_subjects,
    validate_catalog,
)


def _write_temp(destination: Path, payload: bytes) -> Path:
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def _section_filename(key: str, url: str) -> str:
    return key + "-" + hashlib.sha256(url.encode()).hexdigest()[:12] + ".html"


def _completeness(first: str, last: str, records: list[dict]) -> dict:
    first_codes = [code for code, _ in course_headers(first)]
    last_codes = [code for code, _ in course_headers(last)]
    export_codes = [row["course_code"] for row in records]
    last_page = search_last_page(first)
    if not first_codes or not last_codes:
        raise ValueError("Cannot prove catalogue completeness without first/last course pages")
    expected = last_page * len(first_codes) + len(last_codes) if last_page else len(first_codes)
    if expected != len(export_codes):
        raise ValueError(
            f"Incomplete export: search pagination implies {expected}, export has {len(export_codes)}"
        )
    if export_codes[: len(first_codes)] != first_codes or export_codes[-len(last_codes) :] != last_codes:
        raise ValueError("Print export and search first/last course sequences differ")
    if len(set(export_codes)) != len(export_codes):
        raise ValueError("Duplicate course codes in official full export")
    return {
        "verified": True,
        "last_page_index": last_page,
        "page_size": len(first_codes),
        "last_page_count": len(last_codes),
        "expected_course_count": expected,
        "export_course_count": len(export_codes),
        "first_last_sequences_match": True,
        "first_course": export_codes[0],
        "last_course": export_codes[-1],
        "first_page_sha256": hashlib.sha256(first.encode()).hexdigest(),
        "last_page_sha256": hashlib.sha256(last.encode()).hexdigest(),
    }


def refresh_catalog(
    *, html_dir: Path | None = None, output_dir: Path = REFERENCE_DIR, retrieved_at: str | None = None
) -> dict:
    retrieved_at = retrieved_at or date.today().isoformat()
    date.fromisoformat(retrieved_at)

    def read(url: str, filename: str) -> bytes:
        if html_dir is not None:
            path = html_dir / filename
            if not path.exists() and filename.endswith(".html") and "/section/" in url:
                raise HTTPError(url, 404, "Section missing from archived sitemap", None, None)
            return path.read_bytes()
        request = Request(
            url, headers={"User-Agent": "CourseInsight/3.0 (official catalogue metadata refresh)"}
        )
        with urlopen(request, timeout=60) as response:
            if urlparse(response.url).hostname != urlparse(url).hostname:
                raise ValueError(f"Unexpected non-calendar redirect from {url}")
            return response.read()

    records = []
    source_summaries = []
    sections = []
    for source in catalog_sources():
        key = source["key"]
        export = read(source["url"], f"{key}-export.html")
        first = read(source["search_url"], f"{key}-first.html").decode("utf-8")
        last_page = search_last_page(first)
        last_url = source["search_url"] + f"?page={last_page}"
        last = read(last_url, f"{key}-last.html").decode("utf-8") if last_page else first
        campus_records = parse_calendar_section(
            export.decode("utf-8"), campus=source["campus"], retrieved_at=retrieved_at
        )
        check = _completeness(first, last, campus_records)
        records.extend(campus_records)
        source_summaries.append(
            {
                "campus": source["campus"],
                "source_url": source["url"],
                "search_url": source["search_url"],
                "last_page_url": last_url,
                "export_sha256": hashlib.sha256(export).hexdigest(),
                "course_count": len(campus_records),
                "pagination": check,
            }
        )
        sitemap = read(source["sitemap_url"], f"{key}-sitemap.xml")
        tree = ET.fromstring(sitemap)
        urls = [
            node.text
            for node in tree.iter()
            if node.tag.endswith("loc") and node.text and "/section/" in node.text
        ]
        if not urls:
            raise ValueError(f"Official sitemap does not contain subject sections: {key}")
        for url in dict.fromkeys(urls):
            if urlparse(url).hostname != urlparse(source["url"]).hostname:
                raise ValueError(f"Unexpected host in official sitemap: {url}")
            sections.append({"key": key, "campus": source["campus"], "url": url})
        print(
            f"{source['campus']}: {len(campus_records)} courses, full-export pagination verified", flush=True
        )

    def section_data(section):
        url = section["url"]
        try:
            content = read(url, _section_filename(section["key"], url))
        except HTTPError as exc:
            if exc.code != 404:
                raise
            return section, None, {"source_url": url, "status": "not_found_404"}
        title, codes = section_subjects(content.decode("utf-8"))
        if codes and not title:
            raise ValueError(f"Missing official section title: {url}")
        return (
            section,
            (title, codes),
            {
                "source_url": url,
                "status": "retrieved",
                "section_title": title,
                "listed_course_count": len(codes),
                "html_sha256": hashlib.sha256(content).hexdigest(),
            },
        )

    areas = defaultdict(list)
    section_manifest = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for section, result, summary in pool.map(section_data, sections):
            section_manifest.append(summary)
            if result is not None:
                title, codes = result
                for code in codes:
                    item = (title, section["url"])
                    if item not in areas[code]:
                        areas[code].append(item)

    for row in records:
        matches = areas.get(row["course_code"], [])
        if matches:
            row["department"] = matches[0][0]
            row["department_source"] = "official_calendar_section"
            row["department_source_url"] = matches[0][1]
            row["subject_areas"] = json.dumps(
                list(dict.fromkeys(title for title, _ in matches)), ensure_ascii=False
            )

    validate_catalog(records)
    coverage = dict(Counter(row["campus"] for row in records))
    if set(coverage) != {"St. George", "Mississauga", "Scarborough"}:
        raise ValueError(f"Incomplete campus coverage: {coverage}")
    payload = (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fallback = [row["course_code"] for row in records if row["department_source"] == "course_prefix"]
    manifest = {
        "schema_version": 2,
        "complete": True,
        "source_retrieved_at": retrieved_at,
        "course_count": len(records),
        "campus_coverage": coverage,
        "scope": "All courses in the unfiltered St. George Arts & Science, UTM and UTSC official undergraduate calendars. Other St. George faculties and graduate calendars are outside scope.",
        "metadata_source": "official_calendar",
        "catalog_sha256": hashlib.sha256(payload).hexdigest(),
        "missing_requirements": "Empty official field means not listed, not automatically no requirement",
        "requirements": "Original calendar text, whitespace normalized; no eligibility inference",
        "offering_status": "Calendar inclusion does not establish current offering; see the separately sourced timetable snapshot",
        "department_mapping": {
            "official_section_courses": len(records) - len(fallback),
            "prefix_fallback_courses": len(fallback),
            "prefix_fallback_codes": fallback,
            "meaning": "Official calendar academic-area labels, possibly multiple per course; fallback is explicitly labeled course subject prefix, not an administrative department",
        },
        "excluded_course_headers": [],
        "synthetic_records": 0,
        "sources": source_summaries,
        "subject_section_sources": section_manifest,
    }
    manifest_payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
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
    print(f"Saved {result['course_count']} complete official course records to {args.output_dir}")


if __name__ == "__main__":
    main()
