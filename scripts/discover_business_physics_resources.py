#!/usr/bin/env python3
"""Explicitly discover and validate linked official outlines and past-exam metadata.

Only links found in publisher indexes are considered. No PDF content is stored.
This research command does not run during app startup or replace live snapshots.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.catalog import _CalendarHTML, load_catalog

ROTMAN = "https://rotmancommerce.utoronto.ca/current-students/choosing-your-courses/course-outlines-archive/"
ECON_ARCHIVE = "https://www.economics.utoronto.ca/index.php/index/undergraduate/previousyears"
VERIFIED_AT = datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
PHYSICS = [
    "https://www.physics.utoronto.ca/~poppitz/poppitz/PHY354.html",
    "https://www.physics.utoronto.ca/~poppitz/poppitz/PHY450.html",
]
CODE = re.compile(r"\b(?:[A-Z]{3}\d{3}[HY][015]|[A-Z]{3}[A-D]\d{2}[HY]3)")


def fetch(url: str, cache: Path, timeout: float) -> str:
    path = cache / (sha256(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text()
    request = Request(url, headers={"User-Agent": "CourseInsight public course-resource metadata research"})
    with urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    path.write_text(html)
    time.sleep(0.25)
    return html


def dom(html: str):
    parser = _CalendarHTML()
    parser.feed(html)
    return parser.root


def resource(code: str, url: str, source: str, period: str, kind: str, provider: str, label="") -> dict:
    return {
        "resource_id": "res_" + sha256(f"St. George|{code}|{url}".encode()).hexdigest()[:20],
        "course_code": code,
        "campus": "St. George",
        "title": f"{code} · {period or 'Historical materials'} · {label or kind.replace('_', ' ')}",
        "resource_type": kind,
        "url": url,
        "provider": provider,
        "source_kind": "official",
        "academic_period": period,
        "access_requirement": "public",
        "rights_note": "Original publisher link and factual metadata only; no document text is mirrored. Follow the original publisher's usage terms.",
        "verified_at": VERIFIED_AT,
        "source_url": source,
        "limitations": "Course identifier and term come from the official index. Historical content may differ from the current course; no current assessment policy is inferred.",
    }


def rotman_candidates(html: str, codes: set[str]) -> list[dict]:
    period = ""
    records = []
    for node in dom(html).walk():
        if node.tag == "p" and any(c.tag == "a" and c.attrs.get("name") for c in node.walk()):
            period = node.text().replace(" Courses", "").replace("-Term", "")
            if period == "Fall-Winter":
                period = "Full-year (year not listed in archive heading)"
        if node.tag != "li" or not period:
            continue
        matches = CODE.findall(node.text())
        if not matches or matches[0] not in codes:
            continue
        code = matches[0]
        for link in node.walk():
            url = urljoin(ROTMAN, link.attrs.get("href", ""))
            if link.tag == "a" and urlparse(url).path.lower().endswith(".pdf"):
                records.append(
                    resource(
                        code,
                        url,
                        ROTMAN,
                        period,
                        "syllabus",
                        "University of Toronto Rotman Commerce",
                        "Course outline",
                    )
                )
                break  # One section representative per course/term; no multiplication by lecturer.
    return records


def econ_candidates(html: str, source: str, codes: set[str]) -> list[dict]:
    root = dom(html)
    heading = next((n.text() for n in root.walk() if n.tag == "h3" and "Courses offered" in n.text()), "")
    period = heading.replace("Courses offered", "").strip()
    records = []
    code = ""
    course_period = period
    for node in root.walk():
        if node.tag != "tr":
            continue
        matches = CODE.findall(node.text())
        if matches and "Calendar entry" in node.text():
            code = matches[0]
            suffix = re.search(re.escape(code) + r"([FSY])\b", node.text())
            term = suffix.group(1) if suffix else ""
            years = [int(year) for year in re.findall(r"20\d{2}", period)]
            course_period = period
            # The department calls the whole Fall/Winter archive "Winter".
            # Its F/S/Y course suffix identifies the actual constituent term.
            if "Winter" in period and len(years) == 2 and years[1] == years[0] + 1:
                course_period = {
                    "F": f"Fall {years[0]}",
                    "S": f"Winter {years[1]}",
                    "Y": f"Full-year {years[0]}–{years[1]}",
                }.get(term, f"{years[0]}–{years[1]} archive (section term not listed)")
            elif "Summer" in period and term:
                course_period = f"{period} ({term} section)"
        if code not in codes:
            continue
        for link in node.walk():
            href = link.attrs.get("href", "")
            if link.tag == "a" and "downloadCourseOutline/" in href:
                records.append(
                    resource(
                        code,
                        urljoin(source, href),
                        source,
                        course_period,
                        "syllabus",
                        "University of Toronto Department of Economics",
                        "Course outline",
                    )
                )
                break
    return records


def newest_outlines(records: list[dict], limit: int = 2) -> list[dict]:
    def chronology(row):
        years = [int(y) for y in re.findall(r"20\d{2}", row["academic_period"])]
        text = row["academic_period"].lower()
        season = 3 if "fall" in text else 2 if "summer" in text else 1
        return max(years, default=0), season

    chosen = []
    by_course = {}
    for row in sorted(records, key=chronology, reverse=True):
        periods = by_course.setdefault(row["course_code"], set())
        if row["academic_period"] in periods or len(periods) >= limit:
            continue
        periods.add(row["academic_period"])
        chosen.append(row)
    return chosen


def physics_candidates(html: str, source: str, codes: set[str]) -> list[dict]:
    match = re.search(r"PHY\d{3}", source)
    if not match:
        return []
    matches = [code for code in codes if code.startswith(match.group())]
    if len(matches) != 1:
        return []
    code = matches[0]
    records = []
    for node in dom(html).walk():
        if node.tag != "a":
            continue
        href = node.attrs.get("href", "")
        if not urlparse(href).path.lower().endswith(".pdf"):
            continue
        if not re.search(r"(?:midterm|final)", href, re.I):
            continue
        row = resource(
            code,
            urljoin(source, href),
            source,
            "Historical exam (year not specified)",
            "past_exam",
            "University of Toronto Department of Physics — Erich Poppitz",
            "Published past midterm" if "midterm" in href.lower() else "Published past final",
        )
        row["limitations"] = (
            "Listed as a past exam by the instructor's course page. Exact exam year is not specified in the index; filenames can preserve an older course number. Offered as historical reference, not the current assessment."
        )
        records.append(row)
    return records


def verify(row: dict, timeout: float) -> tuple[dict | None, dict]:
    time.sleep(0.25)
    try:
        request = Request(
            row["url"],
            headers={"User-Agent": "CourseInsight resource link verification", "Range": "bytes=0-1023"},
        )
        with urlopen(request, timeout=timeout) as response:
            prefix = response.read(1024)
            final = response.geturl()
            status = response.status
            mime = response.headers.get("Content-Type", "")
        check = {
            "url": row["url"],
            "status": status,
            "content_type": mime,
            "final_url": final,
            "pdf_signature": prefix.lstrip().startswith(b"%PDF-"),
        }
        if status not in {200, 206} or not check["pdf_signature"]:
            return None, {**check, "accepted": False, "reason": "not_a_public_pdf"}
        return row, {**check, "accepted": True}
    except (OSError, ValueError) as error:
        return None, {"url": row["url"], "accepted": False, "reason": str(error)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/courseinsight-official-materials"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/reference/resources_business_physics_expansion.json")
    )
    parser.add_argument("--timeout", type=float, default=18)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    codes = {r["course_code"] for r in load_catalog() if r["campus"] == "St. George"}
    candidates = rotman_candidates(fetch(ROTMAN, args.cache_dir, args.timeout), codes)
    archives = dom(fetch(ECON_ARCHIVE, args.cache_dir, args.timeout))
    indexes = []
    for node in archives.walk():
        href = node.attrs.get("href", "")
        if node.tag == "a" and re.search(r"/undergraduate/courses/[12]/0/202[345]$", href):
            indexes.append(href)
    for url in dict.fromkeys(indexes):
        candidates.extend(econ_candidates(fetch(url, args.cache_dir, args.timeout), url, codes))
    candidates = newest_outlines(candidates)
    for url in PHYSICS:
        candidates.extend(physics_candidates(fetch(url, args.cache_dir, args.timeout), url, codes))
    candidates = list({(r["campus"], r["course_code"], r["url"]): r for r in candidates}.values())
    print(f"Checking {len(candidates)} course-linked PDF targets from official indexes", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda row: verify(row, args.timeout), candidates))
    records = [row for row, _ in results if row]
    evidence = [e for _, e in results]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "verified_at": VERIFIED_AT,
        "candidate_count": len(candidates),
        "accepted_count": len(records),
        "distinct_courses": len({r["course_code"] for r in records}),
        "sources": [ROTMAN, ECON_ARCHIVE, *dict.fromkeys(indexes), *PHYSICS],
        "checks": evidence,
        "method": "Official index links, exact catalogue codes, at most two outline periods per course, public HTTP 200/206 and PDF signature. First 1024 bytes inspected transiently; no document content saved.",
    }
    args.output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Saved {len(records)} verified links for {manifest['distinct_courses']} courses", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
