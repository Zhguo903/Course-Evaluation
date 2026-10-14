#!/usr/bin/env python3
"""Discover link metadata from public UTM/UTSC teaching indexes, on demand.

No PDF is saved: verification reads at most 512 bytes and checks its signature.
Run manually; this script is deliberately independent of app startup/pipeline.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import ssl
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.catalog import _CalendarHTML, load_catalog  # noqa: E402

SHORT_UTSC = re.compile(r"\b[A-Z]{3}[A-D]\d{2}(?=[HY]3\b|\b)")
FULL_UTSC = re.compile(r"\b([A-Z]{3}[A-D]\d{2})([HY])3\b")
SHORT_UTM = re.compile(r"\b(?:CSC|STA|MAT|GGR|JGE)\s?\d{3}(?=[HY]5\b|\b)")
TERM = re.compile(r"\b(Winter|Summer|Fall)\s+(20\d{2}|19\d{2})\b", re.I)
SEASON = {"Winter": 1, "Summer": 5, "Fall": 9}
SEASON_NAME = {value: key for key, value in SEASON.items()}
BIO = "https://www.utsc.utoronto.ca/biosci/course-syllabi"
PHY_BASE = "https://www.utsc.utoronto.ca/physsci/"
PSY_ARCHIVE = "https://hive.utsc.utoronto.ca/public/psych/syllabi/"
NOSEDAL = "https://mcs.utm.utoronto.ca/~nosedal/"
CSSC = "https://cssc.utm.utoronto.ca/resources/"
GEOG = "https://geog.utm.utoronto.ca/desrochers/"
SOURCE_SEEDS = {
    BIO: "/tmp/ci-bio-syllabi.html",
    PHY_BASE + "chemistry-course-syllabi": "/tmp/ci-phy-chemistry.html",
    PHY_BASE + "environmental-science-course-syllabi": "/tmp/ci-phy-environmental.html",
    PHY_BASE + "food-environmental-studies-course-syllabi": "/tmp/ci-phy-food.html",
    PHY_BASE + "physics-astrophysics-course-syllabi": "/tmp/ci-phy-physics.html",
    PSY_ARCHIVE: "/tmp/ci-utsc-psych-archive.html",
    PSY_ARCHIVE + "20269/": "/tmp/ci-psych20269.html",
    PSY_ARCHIVE + "20265/": "/tmp/ci-psych20265.html",
    PSY_ARCHIVE + "20261/": "/tmp/ci-psych20261.html",
    NOSEDAL + "teaching.html": "/tmp/ci-nosedal-teaching.html",
    CSSC: "/tmp/ci-cssc-index.html",
    GEOG: "/tmp/ci-utm-geog-desrochers.html",
}


@dataclass(frozen=True)
class Candidate:
    course_code: str
    campus: str
    url: str
    source_url: str
    academic_period: str
    provider: str
    resource_type: str = "syllabus"
    source_kind: str = "official"
    label: str = ""


class Discovery:
    def __init__(self, cache_dir: Path, verified_at: str):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.verified_at = verified_at
        self.catalog = {(r["campus"], r["course_code"]): r for r in load_catalog()}
        self.short = defaultdict(list)
        for campus, code in self.catalog:
            self.short[(campus, code[:-2])].append(code)
        self.sources = {}
        self.skipped = Counter()
        self.failures = []
        self.checks = {}
        self.lock = threading.Lock()
        self.last_request = 0.0

    def _request(self, url: str, pdf: bool = False) -> tuple[bytes, dict]:
        # Global spacing plus at most three workers avoids a request burst.
        with self.lock:
            time.sleep(max(0, self.last_request + 0.15 - time.monotonic()))
            self.last_request = time.monotonic()
        headers = {"User-Agent": "Course-Insight-Public-Resource-Indexer/1.0"}
        if pdf:
            headers["Range"] = "bytes=0-511"
        parts = urlsplit(url)
        request_url = urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
                quote(parts.query, safe="%=&?/:@!$'()*+,;=-._~"),
                "",
            )
        )
        request = Request(request_url, headers=headers)
        try:
            with urlopen(request, timeout=25) as response:
                data = response.read(512 if pdf else 5_000_000)
                info = {
                    "status": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "final_url": response.url,
                    "verified_at": self.verified_at,
                }
        except URLError as exc:
            if pdf or not isinstance(exc.reason, ssl.SSLCertVerificationError):
                raise
            # curl uses the macOS system trust store, with TLS checks enabled.
            # This fallback reads public HTML only; PDFs remain capped at 512B.
            result = subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--location",
                    "--max-time",
                    "25",
                    "--max-filesize",
                    "5000000",
                    "--write-out",
                    "\n%{http_code}|%{content_type}|%{url_effective}",
                    request_url,
                ],
                check=True,
                capture_output=True,
            )
            data, metadata = result.stdout.rsplit(b"\n", 1)
            status, content_type, final_url = metadata.decode().split("|", 2)
            info = {
                "status": int(status),
                "content_type": content_type,
                "final_url": final_url,
                "verified_at": self.verified_at,
            }
        return data, info

    def html(self, url: str) -> _CalendarHTML:
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / f"{key}.html"
        if not path.exists():
            seed = Path(SOURCE_SEEDS.get(url, "/nonexistent"))
            if seed.is_file():
                path.write_bytes(seed.read_bytes())
            else:
                data, info = self._request(url)
                if "html" not in info["content_type"].lower():
                    raise ValueError(f"Not an HTML index: {url}")
                path.write_bytes(data)
        parser = _CalendarHTML()
        parser.feed(path.read_text(errors="replace"))
        return parser

    def resolve(self, campus: str, text: str, url: str) -> list[str]:
        decoded_url = unquote(url)
        raw = text.upper()
        pattern = SHORT_UTSC if campus == "Scarborough" else SHORT_UTM
        # The visible index label is the course association. Filename is only
        # a fallback for generic "syllabus" links and explicit suffix checking.
        shorts = pattern.findall(raw)
        if not shorts:
            shorts = pattern.findall(decoded_url.upper())
        output = []
        for short in dict.fromkeys(s.replace(" ", "") for s in shorts):
            choices = self.short[(campus, short)]
            if len(choices) != 1:
                self.skipped["not_current_or_ambiguous_course"] += 1
                continue
            full = choices[0]
            explicit = FULL_UTSC.findall(raw + " " + decoded_url.upper())
            if any(code == short and code + weight + "3" != full for code, weight in explicit):
                self.skipped["historical_credit_suffix_mismatch"] += 1
                continue
            output.append(full)
        return output

    def syllabus_index(self, url: str, provider: str, period: str = "") -> list[Candidate]:
        parser = self.html(url)
        result = []
        link_count = 0
        for node in parser.root.walk():
            if node.tag in {"h2", "h3", "h4", "strong"}:
                match = TERM.search(node.text())
                if match:
                    period = f"{match[1].title()} {match[2]}"
            href = node.attrs.get("href") or ""
            if node.tag != "a" or ".pdf" not in href.lower():
                continue
            link_count += 1
            target = urljoin(url, href).replace(" ", "%20")
            file_period = re.search(r"/(20\d{2})([159])-", target)
            candidate_period = period
            if file_period:
                candidate_period = f"{SEASON_NAME[int(file_period[2])]} {file_period[1]}"
            for code in self.resolve("Scarborough", node.text(), target):
                result.append(Candidate(code, "Scarborough", target, url, candidate_period, provider))
        self.sources[url] = {"pdf_links": link_count, "current_course_candidates": len(result)}
        return result

    def pdf_check(self, url: str) -> dict:
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / f"{key}.check.json"
        if path.exists():
            check = json.loads(path.read_text())
            if check.get("verified_at") == self.verified_at:
                return check
        try:
            data, check = self._request(url, pdf=True)
            check["pdf_signature"] = data.startswith(b"%PDF-")
            check["ok"] = check["status"] in {200, 206} and check["pdf_signature"]
            if not check["ok"]:
                check["error"] = "Response does not have a PDF signature"
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            check = {"ok": False, "error": str(exc), "verified_at": self.verified_at}
        path.write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n")
        return check

    def select_syllabi(self, candidates: list[Candidate]) -> list[Candidate]:
        grouped = defaultdict(list)
        for candidate in candidates:
            grouped[candidate.course_code].append(candidate)

        def rank(candidate: Candidate) -> tuple:
            match = TERM.fullmatch(candidate.academic_period)
            return (int(match[2]), SEASON[match[1].title()]) if match else (0, 0)

        for code in grouped:
            grouped[code] = sorted(grouped[code], key=rank, reverse=True)

        def choose(pair: tuple[str, list[Candidate]]) -> Candidate | None:
            _, options = pair
            seen = set()
            for candidate in options:
                if candidate.url in seen:
                    continue
                seen.add(candidate.url)
                check = self.pdf_check(candidate.url)
                with self.lock:
                    self.checks[candidate.url] = check
                    if not check["ok"]:
                        self.failures.append(
                            {"url": candidate.url, "source_url": candidate.source_url, **check}
                        )
                if check["ok"]:
                    return candidate
            return None

        output = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(choose, pair) for pair in sorted(grouped.items())]
            for i, future in enumerate(as_completed(futures), 1):
                candidate = future.result()
                if candidate:
                    output.append(candidate)
                if i % 25 == 0:
                    print(
                        f"Checked {i}/{len(futures)} course groups; selected {len(output)} syllabi",
                        flush=True,
                    )
        return output

    def utm_materials(self) -> list[Candidate]:
        output = []
        parser = self.html(NOSEDAL + "teaching.html")
        for anchor in parser.root.walk():
            href = anchor.attrs.get("href") or ""
            if anchor.tag != "a" or not re.search(r"\bSTA\s?\d{3}\b", anchor.text()):
                continue
            site = urljoin(NOSEDAL, href)
            codes = self.resolve("Mississauga", anchor.text(), site)
            if not codes:
                continue
            code = codes[0]
            page = self.html(site)
            output.append(
                Candidate(
                    code,
                    "Mississauga",
                    site,
                    NOSEDAL + "teaching.html",
                    "",
                    "Alvaro Nosedal, UTM Mathematical and Computational Sciences",
                    "course_site",
                )
            )
            links = []
            for node in page.root.walk():
                target = node.attrs.get("href") or ""
                if node.tag != "a" or ".pdf" not in target.lower():
                    continue
                links.append((node.text(), urljoin(site, target)))
            self.sources[site] = {"pdf_links": len(links), "current_course_candidates": 1}
            # One lecture, one explicitly marked practice document per course.
            # These are real links from an instructor's course-specific page.
            rules = [
                ("lecture_notes", r"chapter|chap\d|lecture|lec\d|part\s*\d|intro|time series"),
                ("practice_exam", r"practice.*(?:test|exam)|sample.*(?:test|exam)|mock.*(?:test|exam)"),
                ("practice_problems", r"exercise|practice|problem|assignment"),
                ("course_materials", r"tutorial"),
            ]
            selected_urls = set()
            for kind, pattern in rules:
                for label, target in links:
                    if target in selected_urls:
                        continue
                    if not re.search(pattern, label + " " + unquote(target), re.I) or re.search(
                        r"solution|answer", label + " " + target, re.I
                    ):
                        continue
                    check = self.pdf_check(target)
                    self.checks[target] = check
                    if check["ok"]:
                        selected_urls.add(target)
                        output.append(
                            Candidate(
                                code,
                                "Mississauga",
                                target,
                                site,
                                "",
                                "Alvaro Nosedal, UTM Mathematical and Computational Sciences",
                                kind,
                                label=label,
                            )
                        )
                        break
                    self.failures.append({"url": target, "source_url": site, **check})
        parser = self.html(CSSC)
        for anchor in parser.root.walk():
            href = anchor.attrs.get("href") or ""
            if anchor.tag != "a" or not re.fullmatch(r"/resources/(?:csc|sta|mat)\d{3}/?", href):
                continue
            target = urljoin(CSSC, href)
            codes = self.resolve("Mississauga", anchor.text(), target)
            if not codes:
                continue
            page = self.html(target)
            body = page.root.text()
            if codes[0][:-2] not in body.upper().replace(" ", ""):
                raise ValueError(f"CSSC page does not identify {codes[0]}: {target}")
            output.append(
                Candidate(
                    codes[0],
                    "Mississauga",
                    target,
                    target,
                    "",
                    "UTM Computer Science Student Community (CSSC)",
                    "student_guide",
                    "student_organization",
                )
            )
            self.sources[target] = {"html_verified": True, "current_course_candidates": 1}
        return output

    def utm_geography(self) -> list[Candidate]:
        # These actual public pages were discovered in the instructor's links
        # and search results, rather than constructing an unverified URL grid.
        discovered = [
            "ggr-209-economic-geography-course/",
            "ggr-365-trade-and-globalization-course/",
            "ggr-329-environment-and-the-roots-of-globalization-course/",
            "ggr-333-energy-and-society/",
            "ggr-387-food-and-globalization-course/",
            "ggr-489-special-topics-in-human-geography-cities-industry-and-the-environment/",
            "ggr-417-research-project/",
        ]
        provider = "Pierre Desrochers, UTM Geography, Geomatics and Environment"
        output = []
        for path in discovered:
            site = urljoin(GEOG, path)
            try:
                page = self.html(site)
            except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
                self.failures.append({"url": site, "error": str(exc), "kind": "html"})
                continue
            titles = [n.text() for n in page.root.walk() if n.tag == "h1"]
            title = titles[-1] if titles else ""
            codes = self.resolve("Mississauga", title, "")
            if not codes:
                continue
            code = codes[0]
            text = page.root.text()
            match = re.search(
                r"Period:\s*((?:Fall|Winter|Summer|Spring)\s+20\d{2}(?:\s*[–-]\s*(?:Fall|Winter|Summer|Spring)\s+20\d{2})?)",
                text,
            )
            period = match[1] if match else ""
            output.append(
                Candidate(code, "Mississauga", site, site, period, provider, "course_site", label=title)
            )
            self.sources[site] = {"html_verified": True, "current_course_candidates": 1}
            for anchor in page.root.walk():
                href = anchor.attrs.get("href") or ""
                if anchor.tag != "a" or not href.startswith(GEOG):
                    continue
                if not re.search(r"lecture", href, re.I):
                    continue
                try:
                    lectures = self.html(href)
                except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
                    self.failures.append({"url": href, "error": str(exc), "kind": "html"})
                    continue
                lecture_titles = [n.text() for n in lectures.root.walk() if n.tag == "h1"]
                lecture_title = lecture_titles[-1] if lecture_titles else ""
                if code not in self.resolve("Mississauga", lecture_title, ""):
                    continue
                output.append(
                    Candidate(
                        code,
                        "Mississauga",
                        href,
                        site,
                        period,
                        provider,
                        "lecture_notes",
                        label=lecture_title,
                    )
                )
                self.sources[href] = {"html_verified": True, "current_course_candidates": 1}
                break
        return output

    def row(self, candidate: Candidate) -> dict:
        code = candidate.course_code
        academic_period = candidate.academic_period
        label = candidate.label.strip()
        title = f"{code} — {label or candidate.resource_type.replace('_', ' ').title()}"
        if academic_period:
            title += f" ({academic_period})"
        limitation = "Historical or published course materials are for reference; confirm the enrolled term's outline with the instructor. Course association and period come from the official index; PDF content is not reproduced."
        if candidate.resource_type == "student_guide":
            limitation = "Student-written guidance expresses its author's experience; it is not an official registration rule, current syllabus, or representative course evaluation."
        elif not academic_period:
            limitation += (
                " The source does not state an academic period; no current-term availability is implied."
            )
        return {
            "resource_id": "res_"
            + hashlib.sha256(f"{code}|{candidate.url}|{candidate.resource_type}".encode()).hexdigest()[:20],
            "course_code": code,
            "campus": candidate.campus,
            "title": title,
            "resource_type": candidate.resource_type,
            "url": candidate.url,
            "provider": candidate.provider,
            "source_kind": candidate.source_kind,
            "academic_period": academic_period,
            "access_requirement": "public",
            "rights_note": "Only link metadata is stored. Copyright remains with the source author; public access does not grant permission to reproduce or redistribute course files.",
            "verified_at": self.verified_at,
            "source_url": candidate.source_url,
            "limitations": limitation,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp/ci-resource-expansion"))
    parser.add_argument("--verified-at", default=datetime.now(ZoneInfo("America/Toronto")).date().isoformat())
    parser.add_argument("--psych-since", type=int, default=1994)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/reference/resources_utm_utsc_expansion.json"
    )
    parser.add_argument("--report", type=Path, default=ROOT / "docs/resource_expansion_utm_utsc.md")
    args = parser.parse_args()
    discovery = Discovery(args.cache_dir, args.verified_at)
    candidates = discovery.syllabus_index(BIO, "University of Toronto Scarborough, Biological Sciences")
    for area in ["chemistry", "environmental-science", "food-environmental-studies", "physics-astrophysics"]:
        candidates.extend(
            discovery.syllabus_index(
                PHY_BASE + area + "-course-syllabi",
                "University of Toronto Scarborough, Physical and Environmental Sciences",
            )
        )
    archive = discovery.html(PSY_ARCHIVE)
    terms = {}
    for node in archive.root.walk():
        href = node.attrs.get("href") or ""
        if (
            node.tag == "a"
            and re.fullmatch(r"(?:19|20)\d{2}[159]/", href)
            and int(href[:4]) >= args.psych_since
        ):
            terms[href] = urljoin(PSY_ARCHIVE, href)
    for folder, url in sorted(terms.items(), reverse=True):
        period = f"{SEASON_NAME[int(folder[4])]} {folder[:4]}"
        try:
            candidates.extend(
                discovery.syllabus_index(
                    url, "University of Toronto Scarborough, Psychology and Neuroscience", period
                )
            )
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            discovery.failures.append({"url": url, "error": str(exc), "kind": "index"})
    print(
        f"Discovered {len(candidates)} current-course syllabus candidates across {len(terms)} psychology term indexes",
        flush=True,
    )
    selected = discovery.select_syllabi(candidates)
    selected.extend(discovery.utm_materials())
    selected.extend(discovery.utm_geography())
    existing = json.loads((ROOT / "data/reference/course_resources.json").read_text())

    def identity(row: dict) -> tuple:
        return (row["course_code"], row["campus"], row["url"].rstrip("/"), row["resource_type"])

    seen = {identity(row) for row in existing}
    rows = []
    for candidate in sorted(selected, key=lambda x: (x.campus, x.course_code, x.resource_type, x.url)):
        row = discovery.row(candidate)
        if identity(row) not in seen:
            seen.add(identity(row))
            rows.append(row)
    assert rows and all((r["campus"], r["course_code"]) in discovery.catalog for r in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    stats = {
        "verified_at": args.verified_at,
        "dataset_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "records": len(rows),
        "unique_course_campus_pairs": len({(r["course_code"], r["campus"]) for r in rows}),
        "unique_urls": len({r["url"] for r in rows}),
        "by_campus": dict(Counter(r["campus"] for r in rows)),
        "courses_by_campus": {
            campus: len({r["course_code"] for r in rows if r["campus"] == campus})
            for campus in ["Mississauga", "Scarborough"]
        },
        "by_type": dict(Counter(r["resource_type"] for r in rows)),
        "by_course_prefix": dict(sorted(Counter(r["course_code"][:3] for r in rows).items())),
        "source_index_count": len(discovery.sources),
        "raw_pdf_links_in_indexes": sum(s.get("pdf_links", 0) for s in discovery.sources.values()),
        "current_syllabus_candidates": len(candidates),
        "pdf_urls_checked": len(discovery.checks),
        "pdf_check_success": sum(c["ok"] for c in discovery.checks.values()),
        "pdf_check_failure": sum(not c["ok"] for c in discovery.checks.values()),
        "successful_pdf_http_mime": dict(
            Counter(
                f"{check.get('status')} {check.get('content_type')}"
                for check in discovery.checks.values()
                if check["ok"]
            )
        ),
        "unavailable_syllabus_courses": sorted(
            {c.course_code for c in candidates}
            - {c.course_code for c in selected if c.resource_type == "syllabus"}
        ),
        "skipped": dict(discovery.skipped),
        "sources": discovery.sources,
        "failures": discovery.failures,
    }
    description = """# UTM 与 UTSC 公开课程资料扩充记录

本批次只保存公开原站的链接与核验元数据，不保存或转发 PDF 正文、教材、答案及受限试卷。课程完整代码与校区均逐条匹配当前官方课程目录；不把旧代码、课程前缀或其他校区自动当作同一门课。每门 UTSC 课程只取官方索引中学期最新且可访问的一份大纲；同一文件被官方明确列给多门课时保留各课程关联，并分别报告链接数与课程数。

主要来源为 [UTSC Biology 大纲索引](https://www.utsc.utoronto.ca/biosci/course-syllabi)、[Chemistry](https://www.utsc.utoronto.ca/physsci/chemistry-course-syllabi)、[Environmental Science](https://www.utsc.utoronto.ca/physsci/environmental-science-course-syllabi)、[Food & Environmental Studies](https://www.utsc.utoronto.ca/physsci/food-environmental-studies-course-syllabi)、[Physics & Astrophysics](https://www.utsc.utoronto.ca/physsci/physics-astrophysics-course-syllabi)、[Psychology/Neuroscience 公开档案](https://hive.utsc.utoronto.ca/public/psych/syllabi/)；后者的官方关联入口为 [Psychology syllabus archive](https://www.utsc.utoronto.ca/psych/syllabus-archive)。UTM 来源为 [Alvaro Nosedal 教学索引](https://mcs.utm.utoronto.ca/~nosedal/teaching.html)、[Pierre Desrochers 官方 Geography 课程页](https://geog.utm.utoronto.ca/desrochers/)与 [CSSC 学生资源](https://cssc.utm.utoronto.ca/resources/)。CSSC 页面属于学生观点，不代表全体学生或官方注册要求。

年份来自官方列表的学期标题；Psychology 文件名含明确学期编码时优先文件名，避免索引误放造成误标。关联核验依据可见课程标签、明确文件名与当前目录。PDF 仅发起最多读取 512 字节的公开 GET，记录 HTTP/MIME 并验证 `%PDF-` 签名；不读取全文。HTTP 404、登录页面、无 PDF 签名及不匹配的旧学分后缀均不收录。旧材料只能参考，不能证明当期授课、考核、先修或教材要求；未知学期保持空值，不能补成当前学年。公开访问不等于开放授权。

可手动运行 `python scripts/discover_utm_utsc_resources.py --verified-at YYYY-MM-DD` 重查；最多三请求并发、全局限速，缓存位于临时目录。正常应用启动与离线 pipeline 不执行网络抓取。合并前还需审阅失败列表、确认当前课程代码、去重现有资源，并使用主项目的支持资料核验流程更新完整性摘要。

UTM Psychology 当前公开页面仅指向统一 Timetable，未发现可核验的课程级公开 archive；UTM Economics 的 syllabus supplement 为部门通用规则，未重复附到每一门课以扩大数量。未猜测受限 CIS 或 Quercus 文件地址。

## 核验统计与来源审计

下列数字是本次新增文件的实际条目数、课程数及 URL 数；`sources` 保留每个具体列表的候选数，`failures` 保留未收录原因。所有成功 PDF 的 HTTP、MIME 与签名检查记录仅缓存在临时目录，不镜像 PDF 文件。

```json
"""
    args.report.write_text(description + json.dumps(stats, ensure_ascii=False, indent=2) + "\n```\n")
    print(
        json.dumps(
            {k: v for k, v in stats.items() if k not in {"sources", "failures"}}, ensure_ascii=False, indent=2
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
