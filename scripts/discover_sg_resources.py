"""Verify a bounded set of official St. George teaching-resource links.

This explicit network command stores link metadata only, never syllabus/exam text.
Run with Python + pypdf available (the Codex bundled Python provides pypdf):
    python scripts/discover_sg_resources.py --verified-at 2026-10-14
Sources are curated course pages and the department's public syllabus index;
child URLs are discovered from real anchors, never synthesized from filenames.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.catalog import load_catalog  # noqa: E402

INDEX_URL = "https://web.cs.toronto.edu/undergraduate/courses/outlines"
MAX_BYTES = 10 * 1024 * 1024
OFFICIAL_HOSTS = {
    "www.cs.toronto.edu",
    "web.cs.toronto.edu",
    "www.math.toronto.edu",
    "math.toronto.edu",
    "utstat.toronto.edu",
    "www.utstat.toronto.edu",
    "utstat.utoronto.ca",
    "www.utstat.utoronto.ca",
    "www.teach.cs.toronto.edu",
    "teach.cs.toronto.edu",
}

# These source pages were located through official-site search and read before
# addition. Blank periods mean the page did not establish a teaching year.
SEEDS = [
    ("MAT257Y1", "Fall 2009–Winter 2010", "https://www.math.toronto.edu/~vtk/257Fall09/"),
    ("MAT347Y1", "Fall 2026–Winter 2027", "https://www.math.toronto.edu/herzig/347-f26.html"),
    ("MAT347Y1", "", "https://www.math.toronto.edu/alfonso/347/347_Test1.html"),
    ("MAT354H1", "", "https://www.math.toronto.edu/nhoell/MAT354.html"),
    ("MAT475H1", "Fall 2026", "https://www.math.toronto.edu/~rafi/MAT475.html"),
    ("MAT237Y1", "Fall 2019–Winter 2020", "https://www.math.toronto.edu/courses/mat237y1/20199/"),
    ("APM236H1", "Spring 2004", "https://www.math.toronto.edu/mpugh/Teaching/APM236_04/handout.html"),
    ("CSC311H1", "Fall 2024", "https://www.cs.toronto.edu/~rahulgk/courses/csc311_f24/index.html"),
    ("CSC311H1", "Fall 2023", "https://www.cs.toronto.edu/~rahulgk/courses/csc311_f23/index.html"),
    ("CSC263H1", "Fall 2013", "https://www.cs.toronto.edu/~toni/Courses/263-2013/263.html"),
    ("CSC363H1", "Summer 2006", "https://www.cs.toronto.edu/~krueger/csc363h/tests/"),
    ("CSC373H1", "Winter 2006", "https://www.cs.toronto.edu/~krueger/csc373h/tests/"),
    ("CSC165H1", "Fall 2007", "https://www.cs.toronto.edu/~krueger/csc165h/tests/"),
    ("CSC401H1", "Spring 2024", "https://www.cs.toronto.edu/~raeidsaqur/csc401/"),
    ("CSC420H1", "Winter 2024", "https://www.cs.toronto.edu/~fidler/teaching/2024/CSC420.html"),
    ("STA302H1", "Fall 2003", "https://www.utstat.toronto.edu/alisong/Teaching/Fall03/sta302.html"),
    ("STA302H1", "Fall 2003", "https://utstat.toronto.edu/alisong/Teaching/Fall03/Sta302/pp.html"),
    ("STA303H1", "Winter 2012", "https://www.utstat.toronto.edu/alisong/Teaching/1112/Sta303/sta303.html"),
    ("STA442H1", "Fall 2010", "https://utstat.toronto.edu/reid/442F10.html"),
    ("ACT460H1", "", "https://utstat.utoronto.ca/sjaimung/courses/sta2502/2010/main.htm"),
]
EXTRA_SEEDS = [
    ("MAT224H1", "", "https://www.math.toronto.edu/nhoell/MAT224/"),
    ("MAT244H1", "Fall 2018", "https://www.math.toronto.edu/courses/mat244h1/20189/"),
    ("MAT246H1", "Winter 2021", "https://www.math.toronto.edu/campesat/mat246.html"),
    ("MAT247H1", "Winter 2012", "https://www.math.toronto.edu/vtk/247Winter2012/"),
    ("MAT344H1", "Fall 2019", "https://www.math.toronto.edu/balazse/2019_Fall_MAT344/index.html"),
    ("STA302H1", "Fall 2003", "https://utstat.toronto.edu/alisong/Teaching/Fall03/sta302.html"),
    ("STA303H1", "Winter 2012", "https://utstat.utoronto.ca/alisong/Teaching/1112/Sta303/sta303.html"),
    ("ACT460H1", "", "https://utstat.utoronto.ca/sjaimung/courses/sta2502/2010/main.htm"),
]


class Page(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.links = []
        self.anchor = None
        self.anchor_text = []
        self.skip = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if tag == "a":
            self.anchor = dict(attrs).get("href")
            self.anchor_text = []

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag == "a" and self.anchor:
            self.links.append((self.anchor, " ".join(self.anchor_text).strip()))
            self.anchor = None

    def handle_data(self, data):
        if not self.skip:
            self.text_parts.append(data)
            if self.anchor:
                self.anchor_text.append(data)

    @property
    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.text_parts))


@dataclass
class Verified:
    url: str
    text: str
    page: Page | None
    status: int


def allowed(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS and not parsed.username


def fetch(url: str) -> Verified:
    if not allowed(url):
        raise ValueError("not an allow-listed official HTTPS source")
    request = Request(url, headers={"User-Agent": "CourseInsight public-link verification/1.0"})
    with urlopen(request, timeout=25) as response:
        final_url = response.geturl()
        if not allowed(final_url) or response.status != 200:
            raise ValueError("source did not remain a public official HTTPS page")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("source larger than 10 MiB; not retained")
        if body.startswith(b"%PDF-"):
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(body))
            text = " ".join(page.extract_text() or "" for page in reader.pages[:2])
            if len(text.strip()) < 20:
                raise ValueError("PDF first pages have no readable verification text")
            return Verified(final_url, re.sub(r"\s+", " ", text), None, response.status)
        if "html" not in response.headers.get("Content-Type", "").lower() and not body.lstrip().startswith(
            b"<"
        ):
            raise ValueError("not a readable HTML page or PDF")
        page = Page(body.decode(response.headers.get_content_charset() or "utf-8", errors="replace"))
        if len(page.text.strip()) < 30:
            raise ValueError("no readable page content")
        return Verified(final_url, page.text, page, response.status)


def contains_course(text: str, code: str) -> bool:
    # The official index supplies the full H1/Y1 code. Course pages and PDF
    # headings often abbreviate it to CSC 311 / STA 302 / MAT 257Y.
    prefix, number = code[:3], code[3:6]
    explicit = re.findall(rf"\b{prefix}\s*{number}\s*([HY])\s*([015])\b", text[:1200], re.I)
    if explicit and (code[6], code[7]) != (explicit[0][0].upper(), explicit[0][1]):
        return False
    return bool(re.search(rf"\b{prefix}\s*{number}(?!\d)", text, re.I))


def explicit_period(text: str) -> str:
    match = re.search(
        r"\b(Fall|Winter|Spring|Summer)\s*(?:of\s+|,\s*)?(19\d{2}|20\d{2})\b", text[:1200], re.I
    )
    if match:
        return f"{match[1].title()} {match[2]}"
    match = re.search(r"\b(19\d{2}|20\d{2})\s+(Fall|Winter|Spring|Summer)\b", text[:1200], re.I)
    return f"{match[2].title()} {match[1]}" if match else ""


def metadata(
    code: str, period: str, url: str, kind: str, label: str, source: str, date: str, note: str
) -> dict:
    label = re.sub(r"\s+", " ", label).strip()
    if label.lower() in {"link", "here", "click here", "problems"}:
        label = kind.replace("_", " ")
    provider = "University of Toronto " + (
        "Department of Computer Science"
        if code.startswith("CSC")
        else "Department of Mathematics"
        if code.startswith(("MAT", "APM"))
        else "Department of Statistical Sciences"
    )
    return {
        "resource_id": "res_" + sha256(f"St. George|{code}|{url}".encode()).hexdigest()[:20],
        "course_code": code,
        "campus": "St. George",
        "title": f"{code} — {label}",
        "resource_type": kind,
        "url": url,
        "provider": provider,
        "source_kind": "official",
        "academic_period": period,
        "access_requirement": "public",
        "rights_note": "Link and factual metadata only. No syllabus, exam, questions, solutions or textbook content is mirrored. No open reuse licence is assumed; follow the original publisher's terms.",
        "verified_at": date,
        "source_url": source,
        "limitations": note
        + " Historical material may differ from current instruction. Public access to this link does not grant reuse rights or access to linked submission systems.",
    }


def link_kind(label: str, url: str) -> str | None:
    value = (label + " " + url).casefold()
    if any(word in value for word in ["grade", "marks", "survey", "zoom", "textbook", "registration"]):
        return None
    if re.search(r"practice|practise|sample|mock", value):
        return "practice_exam" if re.search(r"exam|midterm|test|final", value) else "practice_problems"
    if re.search(r"past.*(?:exam|test)|(?:exam|test).*past", value):
        return "past_exam"
    if re.search(r"problem|worksheet|exercise", value):
        return "practice_problems"
    if re.search(r"syllabus|outline", value):
        return "syllabus"
    return None


def main():
    parser = argparse.ArgumentParser()
    current_date = datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
    parser.add_argument("--verified-at", default=current_date)
    parser.add_argument("--max-syllabi", type=int, default=65)
    parser.add_argument(
        "--append-extra",
        action="store_true",
        help="Only verify additional curated math sources; retain prior results",
    )
    parser.add_argument(
        "--audit-existing",
        action="store_true",
        help="Re-read linked representative documents for own period and campus identity",
    )
    args = parser.parse_args()
    if args.verified_at != current_date:
        raise ValueError("Live verification date must equal the current America/Toronto date")
    codes = {row["course_code"] for row in load_catalog() if row["campus"] == "St. George"}
    output = ROOT / "data/reference/resources_sg_expansion.json"
    rows, excluded, verified_sources = [], [], []
    if args.audit_existing:
        existing = json.loads(output.read_text(encoding="utf-8"))

        def audit(row):
            if row["source_url"] == INDEX_URL:
                return row, None
            try:
                verified = fetch(row["url"])
                if not contains_course(verified.text, row["course_code"]):
                    raise ValueError(
                        "target primary course code/campus does not establish the current SG course"
                    )
                old_period = row["academic_period"]
                period_years = re.findall(r"19\d{2}|20\d{2}", old_period)
                keep_parent_period = (
                    row["source_url"] == row["url"]
                    and bool(period_years)
                    and all(year in verified.text for year in period_years)
                )
                row["academic_period"] = old_period if keep_parent_period else explicit_period(verified.text)
                if old_period and row["title"].endswith(f" ({old_period})"):
                    row["title"] = row["title"][: -len(f" ({old_period})")]
                if row["academic_period"]:
                    row["title"] += f" ({row['academic_period']})"
                row["limitations"] += (
                    " The document's own header period was audited separately; an unknown document period is not inherited from the parent course page."
                )
                return row, None
            except Exception as error:
                return None, (row["url"], str(error))

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(audit, existing))
        kept = [row for row, _ in results if row]
        output.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path = ROOT / "docs/resource_expansion_sg.md"
        report = [
            report_path.read_text(encoding="utf-8"),
            "",
            "## 代表文件二次内容核验",
            "",
            "再次读取代表文件前两页，分别核验主课程代码/校区及文件自己的期次；不把父课程页的学期自动继承给旧试卷。未知文件期次清空。",
            "",
        ]
        report += [f"- 排除 {error[0]} — {error[1]}" for _, error in results if error]
        report += [
            "",
            f"二次核验后：{len(kept)} 条，{len({row['course_code'] for row in kept})} 门课程。",
            "",
        ]
        report_path.write_text("\n".join(report), encoding="utf-8")
        print(json.dumps({"audited_records": len(kept), "removed": len(existing) - len(kept)}))
        return
    if args.append_extra:
        rows = json.loads(output.read_text(encoding="utf-8"))
    index = None if args.append_extra else fetch(INDEX_URL)
    candidates = {}
    for href, label in index.page.links if index else []:
        target = urldefrag(urljoin(INDEX_URL, href))[0]
        match = re.search(r"\b(CSC\d{3}[HY]1)", label + " " + target)
        period = re.search(r"(Fall|Winter|Summer)\s*(20\d{2})", label, re.I)
        if not match or not period or not target.lower().endswith(".pdf") or not allowed(target):
            continue
        code = match[1]
        if code not in codes:
            excluded.append(
                (target, f"Official index code {code} absent from current SG catalog; no H/Y substitution.")
            )
            continue
        term, year = period[1].title(), int(period[2])
        candidates.setdefault(code, []).append(
            ((year, {"Winter": 1, "Summer": 2, "Fall": 3}[term]), target, f"{term} {year}")
        )

    def syllabus(item):
        code, options = item
        errors = []
        for _, url, period in sorted(set(options), reverse=True):
            try:
                verified = fetch(url)
                if not contains_course(verified.text, code):
                    raise ValueError("PDF content did not identify the indexed course")
                note = "Full current course code and historical term are explicitly listed in the official department index; PDF first pages also identify the course. The index requests reference-only use and no redistribution/reuse of syllabus information."
                return metadata(
                    code,
                    period,
                    verified.url,
                    "syllabus",
                    f"official course outline ({period})",
                    INDEX_URL,
                    args.verified_at,
                    note,
                ), errors
            except Exception as error:
                errors.append((url, str(error)))
        return None, errors

    with ThreadPoolExecutor(max_workers=4) as pool:
        for row, errors in pool.map(syllabus, sorted(candidates.items())[: args.max_syllabi]):
            excluded.extend(errors)
            if row:
                rows.append(row)
    if index:
        verified_sources.append(INDEX_URL)
    for code, period, source in EXTRA_SEEDS if args.append_extra else SEEDS:
        if code not in codes:
            excluded.append((source, f"{code} absent from current SG catalog"))
            continue
        try:
            verified = fetch(source)
            if not contains_course(verified.text, code):
                raise ValueError("page content does not establish selected course")
            if not verified.page:
                raise ValueError("curated course index was not HTML")
            period_years = re.findall(r"19\d{2}|20\d{2}", period)
            if period_years and not all(year in verified.text for year in period_years):
                period = ""
            verified_sources.append(verified.url)
            note = (
                "Course identity was read on the official teaching page and matched only to the current St. George catalog code. "
                + (
                    "Teaching period is stated by the source."
                    if period
                    else "The source does not establish a teaching period; none is inferred."
                )
            )
            page_kind = (
                "practice_problems"
                if source.endswith("pp.html") or "Test1.html" in source
                else "course_materials"
            )
            rows.append(
                metadata(
                    code,
                    period,
                    verified.url,
                    page_kind,
                    "public teaching materials" + (f" ({period})" if period else " (period not listed)"),
                    verified.url,
                    args.verified_at,
                    note,
                )
            )
            selected_kinds = set()
            checked_children = 0
            for href, label in verified.page.links:
                target = urldefrag(urljoin(verified.url, href))[0]
                kind = link_kind(label, target)
                if not kind or kind in selected_kinds or not allowed(target) or target == verified.url:
                    continue
                if re.search(r"\b(?:UTM|UTSC|Mississauga|Scarborough)\b", label, re.I):
                    excluded.append((target, "Linked material explicitly identifies another campus"))
                    continue
                if checked_children >= 10:
                    break
                checked_children += 1
                # This is representative indexing, not one record per lecture or worksheet.
                try:
                    child = fetch(target)
                    if not contains_course(child.text, code):
                        raise ValueError("child content does not independently identify course")
                    child_period = explicit_period(child.text)
                    rows.append(
                        metadata(
                            code,
                            child_period,
                            child.url,
                            kind,
                            (label[:120] or kind.replace("_", " "))
                            + (f" ({child_period})" if child_period else ""),
                            verified.url,
                            args.verified_at,
                            "Discovered in an actual link on the verified course page; target HTTP 200 and readable course-identifying content were checked. "
                            + (
                                "The target states its teaching period. "
                                if child_period
                                else "The target does not establish its own teaching period; no period is inherited from the parent course page. "
                            )
                            + note,
                        )
                    )
                    selected_kinds.add(kind)
                except Exception as error:
                    excluded.append((target, str(error)))
                if len(selected_kinds) >= 3:
                    break
        except Exception as error:
            excluded.append((source, str(error)))

    unique = {(row["campus"], row["course_code"], row["url"]): row for row in rows}
    rows = sorted(unique.values(), key=lambda row: (row["course_code"], row["resource_type"], row["url"]))
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from collections import Counter

    report = [
        "# St. George 公开学习资料扩充",
        "",
        f"核验日期：{args.verified_at}。新增 {len(rows)} 条链接元数据，关联 {len({row['course_code'] for row in rows})} 门当前 St. George 课程。",
        "",
        "仅保存原站链接与事实性元数据；没有镜像大纲、题目、答案、课件或教材全文。每个课程/来源仅选择少量代表入口，完整练习集合由原站目录提供。",
        "",
        "## 核验方式",
        "",
        "官方索引或课程页提供代码、期次和真实 href；逐个 GET 核验 HTTP 200、HTTPS 官方域及可读 HTML/PDF。PDF 仅在内存检查前两页后释放，不保留原文件或摘录。当前 load_catalog 精确校验 St. George 完整代码，不跨校区、不替换 H/Y。期次未明时保留为空。",
        "",
        "CS 大纲索引要求仅供参考、不要分发或再利用大纲内信息。本集合仅索引课程代码、期次和原站链接，不复制大纲内容；原站条件仍适用。",
        "",
        "## 资源类型",
        "",
    ]
    report.extend(
        f"- {kind}: {count}" for kind, count in sorted(Counter(row["resource_type"] for row in rows).items())
    )
    report += ["", "## 已核验来源列表", ""]
    report.extend(f"- {url}" for url in dict.fromkeys(verified_sources))
    report += [
        "",
        "## 排除与失败检查",
        "",
        "以下链接未计入扩充资源。失败不推断资源永久不存在；未使用修改 URL、关闭 TLS 验证或跨校区映射来补齐。",
        "",
    ]
    report.extend(f"- {url} — {reason}" for url, reason in dict.fromkeys(excluded))
    report += [
        "",
        "明确不将旧 MAT137Y1、MAT235Y1、MAT135Y1、STA107 或 STA260 资料改配到代码相似的当前或外校区课程。",
        "",
    ]
    report_path = ROOT / "docs/resource_expansion_sg.md"
    if args.append_extra:
        report = [report_path.read_text(encoding="utf-8"), "", "---", "", *report]
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "records": len(rows),
                "courses": len({row["course_code"] for row in rows}),
                "excluded": len(excluded),
                "output": str(output),
            }
        )
    )


if __name__ == "__main__":
    main()
