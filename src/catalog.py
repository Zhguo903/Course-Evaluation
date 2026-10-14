"""Verified University of Toronto course metadata, separate from demo reviews.

The checked-in snapshot is usable offline. Run ``scripts/update_catalog.py``
explicitly to refresh it from the three official calendars; ordinary pipeline
runs never scrape the university or infer eligibility from prerequisite text.
"""

from __future__ import annotations

import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode


REFERENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "reference"
CATALOG_PATH = REFERENCE_DIR / "uoft_courses.json"

ARTSCI_CATEGORIES = {
    1: "Creative and Cultural Representations (1)",
    2: "Thought, Belief and Behaviour (2)",
    3: "Society and its Institutions (3)",
    4: "Living Things and Their Environment (4)",
    5: "The Physical and Mathematical Universes (5)",
}
UTSC_CATEGORIES = (
    "Arts, Literature and Language",
    "History, Philosophy and Cultural Studies",
    "Social and Behavioural Sciences",
    "Natural Sciences",
    "Quantitative Reasoning",
)
UTM_CATEGORIES = ("Science", "Humanities", "Social Science")
CAMPUS_RULES = {
    "St. George": ("artsci.calendar.utoronto.ca", "artsci_breadth", "1"),
    "Mississauga": ("utm.calendar.utoronto.ca", "utm_distribution", "5"),
    "Scarborough": ("utsc.calendar.utoronto.ca", "utsc_breadth", "3"),
}
DEPARTMENT_SECTIONS = (
    ("Statistics", "STA", "Statistical-Sciences", "Statistics, Applied", "Statistics"),
    ("Computer Science", "CSC", "Computer-Science", "Computer Science", "Computer-Science"),
    ("Economics", "ECO", "Economics", "Economics", "Economics-for-Management-Studies"),
    ("Mathematics", "MAT", "Mathematics", "Mathematical Sciences", "Mathematics"),
    ("Biology", "BIO", "Cell-and-Systems-Biology", "Biology", "Biological-Sciences"),
    ("Psychology", "PSY", "Psychology", "Psychology", "Psychology"),
    ("English", "ENG", "English", "English", "English"),
    ("History", "HIS", "History", "History", "History"),
)
COURSE_CODE_RE = re.compile(r"(?:[A-Z]{3}\d{3}[HY][15]|[A-Z]{3}[A-D]\d{2}[HY]3)")
_HEADER_RE = re.compile(r"^([A-Z]{3}(?:\d{3}[HY][15]|[A-D]\d{2}[HY]3))\s*[-•:]\s*(.+)$")
_REQUIREMENT_FIELDS = (
    "prerequisite",
    "corequisite",
    "exclusion",
    "recommended_preparation",
    "enrolment_requirements",
    "requirement_notes",
)


def catalog_sources() -> list[dict]:
    """The curated 200-course coverage: 80 St. George, 60 UTM, 60 UTSC.

    Each campus includes all eight subjects. UTM uses its course-search program
    area filter, while St. George and UTSC publish full subject sections.
    """
    sources = []
    for campus, (host, _, _) in CAMPUS_RULES.items():
        for index, (department, prefix, sg, utm, utsc) in enumerate(DEPARTMENT_SECTIONS):
            slug = department.lower().replace(" ", "-")
            campus_key = {"St. George": "sg", "Mississauga": "utm", "Scarborough": "utsc"}[campus]
            if campus == "Mississauga":
                url = f"https://{host}/course-search?{urlencode({'field_sections_value': utm})}"
            else:
                url = f"https://{host}/section/{sg if campus == 'St. George' else utsc}"
            sources.append(
                {
                    "key": f"{campus_key}-{slug}",
                    "campus": campus,
                    "department": department,
                    "prefix": "CSB"
                    if campus == "St. George" and department == "Biology"
                    else ("MGE" if campus == "Scarborough" and department == "Economics" else prefix),
                    "url": url,
                    "count": 10 if campus == "St. George" else (8 if index < 4 else 7),
                }
            )
    return sources


class _Node:
    def __init__(self, tag: str, attrs: dict | None = None, parent: _Node | None = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.parent = parent
        self.children: list[_Node | str] = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()

    def raw_text(self) -> str:
        if self.tag in {"script", "style"}:
            return ""
        text = "".join(child if isinstance(child, str) else child.raw_text() for child in self.children)
        return f"\n{text}\n" if self.tag in {"p", "li", "br", "div", "h3"} else text

    def text(self) -> str:
        return re.sub(r"\s+", " ", self.raw_text().replace("\u200b", "")).strip()


class _CalendarHTML(HTMLParser):
    """Minimal DOM sufficient for the Drupal course accordion markup."""

    _VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self._VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self._VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _field(node: _Node, *classes: str) -> str:
    values = []
    for child in node.walk():
        if any(child.has_class(f"views-field-{name}") for name in classes):
            content = next((item for item in child.walk() if item.has_class("field-content")), None)
            if content is not None and content.text():
                values.append(content.text())
    return "\n".join(dict.fromkeys(values))


def _body_notes(node: _Node) -> str:
    """Retain restrictions in prose, without copying entire descriptions."""
    clauses = []
    for child in node.walk():
        if child.has_class("views-field-body") or child.has_class("views-field-field-desc"):
            paragraphs = [item for item in child.walk() if item.tag == "p"] or [child]
            for paragraph in paragraphs:
                text = paragraph.text()
                if re.search(
                    r"\b(restrict\w*|prerequisit\w*|permission|consent|priority|reserved|not open|"
                    r"available only|only available|only to|not permitted|not eligible|may not take|cannot take|"
                    r"must (?:complete|obtain|have|be)|open only|only open|admission stream|"
                    r"enrolment|enrollment|not available|not be taken)\b",
                    text,
                    re.I,
                ):
                    clauses.append(text)
    explicit_notes = _field(node, "field-note")
    if explicit_notes:
        clauses.append(explicit_notes)
    return "\n".join(dict.fromkeys(clauses))


def _categories(text: str, campus: str) -> tuple[list[int], list[str]]:
    if campus == "St. George":
        ids = sorted({int(number) for number in re.findall(r"\(([1-5])\)", text)})
        if text.strip() and not ids:
            raise ValueError(f"Unrecognized official St. George breadth field: {text}")
        return ids, [ARTSCI_CATEGORIES[number] for number in ids]
    known = UTM_CATEGORIES if campus == "Mississauga" else UTSC_CATEGORIES
    labels = [label for label in known if re.search(rf"(?<!\w){re.escape(label)}(?!\w)", text)]
    # 'Science' is part of 'Social Science'; retain the actual official label.
    if (
        campus == "Mississauga"
        and "Social Science" in labels
        and not re.search(r"(?<!Social )\bScience\b", text)
    ):
        labels.remove("Science")
    if text.strip() and not labels:
        raise ValueError(f"Unrecognized official {campus} requirement field: {text}")
    return [], labels


def parse_calendar_section(html: str, *, campus: str, department: str, retrieved_at: str) -> list[dict]:
    """Extract literal course requirements from an official subject/search page.

    Only recognized full course-code headers are accepted. Program admission
    requirements above the course accordion cannot become course prerequisites.
    Missing fields remain empty and are explicitly distinguished from 'none'.
    """
    host, requirement_system, suffix = CAMPUS_RULES[campus]
    date.fromisoformat(retrieved_at)
    parser = _CalendarHTML()
    parser.feed(html)
    records = []
    for header in parser.root.walk():
        if header.tag != "h3" or not header.has_class("js-views-accordion-group-header"):
            continue
        match = _HEADER_RE.fullmatch(header.text())
        if not match:
            continue
        code, name = match.groups()
        if not code.endswith(suffix):
            continue
        siblings = header.parent.children
        following = siblings[siblings.index(header) + 1 :]
        body = next((node for node in following if isinstance(node, _Node)), None)
        if body is None:
            raise ValueError(f"Missing course accordion body: {code}")
        breadth = _field(body, "field-breadth-requirements")
        distribution = _field(body, "field-distribution-requirements")
        categories, labels = _categories(distribution if campus == "Mississauga" else breadth, campus)
        prerequisite = _field(body, "field-prerequisite")
        records.append(
            {
                "course_code": code,
                "course_name": name,
                "department": department,
                "course_level": (ord(code[3]) - ord("A") + 1) * 100 if suffix == "3" else int(code[3]) * 100,
                "credit": 0.5 if code[-2] == "H" else 1.0,
                "campus": campus,
                "requirement_system": requirement_system,
                "requirement_categories": json.dumps(labels, ensure_ascii=False),
                "breadth_categories": json.dumps(categories),
                "breadth_requirements": breadth,
                "distribution_requirements": distribution,
                "prerequisite": prerequisite,
                "prerequisite_status": "listed" if prerequisite else "not_listed",
                "corequisite": _field(body, "field-corequisite"),
                "exclusion": _field(body, "field-exclusion"),
                "recommended_preparation": _field(body, "field-recommended", "field-recommended-preparation"),
                "enrolment_requirements": _field(
                    body, "field-enrolment-limits", "field-enrolment-requirements"
                ),
                "requirement_notes": _body_notes(body),
                "source_url": f"https://{host}/course/{code.lower()}",
                "source_retrieved_at": retrieved_at,
                "metadata_source": "official_calendar",
            }
        )
    if not records:
        raise ValueError(
            f"No recognized courses found for {campus} / {department}; calendar markup may have changed"
        )
    return records


def select_courses(records: list[dict], source: dict) -> list[dict]:
    """Deterministic subject sample with a spread of levels and familiar courses."""
    candidates = sorted(
        (record for record in records if record["course_code"].startswith(source["prefix"])),
        key=lambda record: record["course_code"],
    )
    count = source["count"]
    if len(candidates) < count:
        raise ValueError(f"{source['key']} has only {len(candidates)} courses; need {count}")
    preferred = {
        "sg-statistics": ["STA130H1", "STA303H1"],
        "sg-computer-science": ["CSC108H1", "CSC148H1"],
        "utm-computer-science": ["CSC108H5", "CSC148H5"],
        "utsc-computer-science": ["CSCA08H3", "CSCA48H3"],
    }.get(source["key"], [])
    selected = [record for record in candidates if record["course_code"] in preferred]
    if len(selected) != len(preferred):
        raise ValueError(f"Missing expected official course in {source['key']}")
    queues = {
        level: [record for record in candidates if record["course_level"] == level and record not in selected]
        for level in (100, 200, 300, 400)
    }
    while len(selected) < count:
        for queue in queues.values():
            if queue and len(selected) < count:
                selected.append(queue.pop(0))
        if not any(queues.values()) and len(selected) < count:
            raise ValueError(f"Insufficient level 100–400 courses for {source['key']}")
    return selected


def validate_catalog(records: list[dict], *, expected_count: int | None = None) -> None:
    """Reject incomplete, fabricated-code or cross-campus category snapshots."""
    if not records or (expected_count is not None and len(records) != expected_count):
        raise ValueError(f"Unexpected catalogue size: {len(records)} (expected {expected_count})")
    codes = set()
    for record in records:
        code = record.get("course_code", "")
        if not COURSE_CODE_RE.fullmatch(code) or code in codes:
            raise ValueError(f"Invalid or duplicate official course code: {code}")
        codes.add(code)
        if not record.get("course_name") or not record.get("department"):
            raise ValueError(f"Missing official name/department: {code}")
        if record.get("campus") not in CAMPUS_RULES:
            raise ValueError(f"Unknown campus: {code}")
        host, system, suffix = CAMPUS_RULES[record["campus"]]
        if not code.endswith(suffix) or record.get("source_url") != f"https://{host}/course/{code.lower()}":
            raise ValueError(f"Course/campus/source mismatch: {code}")
        if record.get("metadata_source") != "official_calendar" or record.get("requirement_system") != system:
            raise ValueError(f"Invalid metadata source/requirement system: {code}")
        date.fromisoformat(record["source_retrieved_at"])
        breadth = json.loads(record["breadth_categories"])
        labels = json.loads(record["requirement_categories"])
        if not isinstance(breadth, list) or any(
            type(item) is not int or item not in range(1, 6) for item in breadth
        ):
            raise ValueError(f"Invalid Arts & Science breadth category: {code}")
        if not isinstance(labels, list) or any(not isinstance(item, str) for item in labels):
            raise ValueError(f"Invalid requirement categories: {code}")
        if suffix != "1" and breadth:
            raise ValueError(f"St. George BR numbers cannot be assigned to {record['campus']}: {code}")
        raw = record["distribution_requirements"] if suffix == "5" else record["breadth_requirements"]
        expected_breadth, expected_labels = _categories(raw, record["campus"])
        if breadth != expected_breadth or labels != expected_labels:
            raise ValueError(f"Requirement categories do not match official text: {code}")
        if not raw and (breadth or labels):
            raise ValueError(f"Categories invented without an official field: {code}")
        for field in _REQUIREMENT_FIELDS:
            if not isinstance(record.get(field), str):
                raise ValueError(f"Missing requirement field {field}: {code}")
        if record.get("prerequisite_status") != ("listed" if record["prerequisite"] else "not_listed"):
            raise ValueError(f"Prerequisite missing/listed status mismatch: {code}")
        if record.get("credit") != (0.5 if code[-2] == "H" else 1.0):
            raise ValueError(f"Course credit does not match official H/Y code: {code}")
        expected_level = (ord(code[3]) - ord("A") + 1) * 100 if suffix == "3" else int(code[3]) * 100
        if record.get("course_level") != expected_level:
            raise ValueError(f"Course level does not match code: {code}")


def load_catalog(path: str | Path | None = None) -> list[dict]:
    """Load and validate the offline snapshot; no network calls or mock metadata."""
    records = json.loads(Path(path or CATALOG_PATH).read_text(encoding="utf-8"))
    validate_catalog(records, expected_count=200 if path is None else None)
    if path is None:
        coverage = {campus: sum(row["campus"] == campus for row in records) for campus in CAMPUS_RULES}
        if coverage != {"St. George": 80, "Mississauga": 60, "Scarborough": 60}:
            raise ValueError(f"Incomplete default campus coverage: {coverage}")
    return records
