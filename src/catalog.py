"""Complete official undergraduate calendar metadata across three UofT campuses.

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
from urllib.parse import urlparse, parse_qs


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
    "St. George": ("artsci.calendar.utoronto.ca", "artsci_breadth", "01"),
    "Mississauga": ("utm.calendar.utoronto.ca", "utm_distribution", "5"),
    "Scarborough": ("utsc.calendar.utoronto.ca", "utsc_breadth", "3"),
}
COURSE_CODE_RE = re.compile(r"(?:[A-Z]{3}\d{3}[HY][015]|[A-Z]{3}[A-D]\d{2}[HY]3)")
_HEADER_RE = re.compile(r"^([A-Z]{3}(?:\d{3}[HY][015]|[A-D]\d{2}[HY]3))\s*[-•:]\s*(.+)$")
_REQUIREMENT_FIELDS = (
    "prerequisite",
    "corequisite",
    "exclusion",
    "recommended_preparation",
    "enrolment_requirements",
    "requirement_notes",
)


def catalog_sources() -> list[dict]:
    """Official unfiltered full exports and search pages used to prove coverage."""
    sources = []
    for campus, (host, _, _) in CAMPUS_RULES.items():
        key = {"St. George": "sg", "Mississauga": "utm", "Scarborough": "utsc"}[campus]
        view = "course_search" if key == "sg" else "search_courses"
        path = "course-search" if key == "utm" else "search-courses"
        sources.append(
            {
                "key": key,
                "campus": campus,
                "url": f"https://{host}/print/view/pdf/{view}/print_page/debug/",
                "search_url": f"https://{host}/{path}",
                "sitemap_url": f"https://{host}/sitemap.xml",
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


_BODY_CONDITION_RE = re.compile(
    r"\b(restrict\w*|prerequisit\w*|permission (?:of|from|to|is|may|must|will|shall)|"
    r"consent (?:of|from|is|required|must)|given priority|"
    r"priority (?:enrolment|enrollment|will|is|shall|given|going|may|to)|reserved for|not open|"
    r"available only|only available|only to|not permitted|not eligible|may not take|cannot take|"
    r"must (?:complete|obtain|have|be)|open only|only open|admission stream|"
    r"enrolment|enrollment|not available|not be taken|"
    r"assumes (?:prior |previous |programming )?(?:experience|knowledge|background)|"
    r"application (?:information|process|deadline)|interview (?:is|may|will|must))\b",
    re.I,
)
_CONTEXT_SENTENCE_RE = re.compile(
    r"^(?:However|Otherwise|Alternatively|In (?:these|such) cases|For (?:these|such) students|"
    r"This (?:requirement|restriction|exception|option)|These (?:students|courses|requirements)|"
    r"Those students|Such students|Students who (?:already|do not)|If |Unless )",
    re.I,
)


def _condition_sentences(text: str) -> list[str]:
    """Select whole source sentences, preserving clauses rather than truncating."""
    protected = re.sub(
        r"\b(?:e\.g|i\.e|etc|Dr|Prof|Mr|Mrs|Ms|St|vs|U\.S|U\.K)\.",
        lambda match: match.group().replace(".", "\ue000"),
        text,
        flags=re.I,
    )
    sentences = [
        part.replace("\ue000", ".")
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])", protected)
        if part.strip()
    ]
    selected = {index for index, sentence in enumerate(sentences) if _BODY_CONDITION_RE.search(sentence)}
    # A following exception can depend on the condition before it. Keep the
    # complete short sentence; never shorten grades, AND/OR lists or term limits.
    for index in sorted(selected):
        if index + 1 < len(sentences):
            following = sentences[index + 1]
            if len(following.split()) <= 60 and _CONTEXT_SENTENCE_RE.search(following):
                selected.add(index + 1)
        sentence = sentences[index]
        if index > 0 and re.match(
            r"^(?:This restriction|This requirement|These students|Such students|Otherwise)\b", sentence, re.I
        ):
            preceding = sentences[index - 1]
            if len(preceding.split()) <= 60:
                selected.add(index - 1)
    return [sentence for index, sentence in enumerate(sentences) if index in selected]


def _body_notes(node: _Node) -> str:
    """Keep condition sentences, inline NOTE blocks and explicit note fields."""
    clauses = []
    for child in node.walk():
        if child.has_class("views-field-body") or child.has_class("views-field-field-desc"):
            paragraphs = [item for item in child.walk() if item.tag == "p"] or [child]
            for paragraph in paragraphs:
                text = paragraph.text()
                note = re.search(r"\bnotes?\s*:", text, re.I)
                if note:
                    # A labelled note can contain permissions followed by a
                    # restriction. Keep its complete source wording together.
                    clauses.extend(_condition_sentences(text[: note.start()].strip()))
                    clauses.append(text[note.start() :].strip())
                else:
                    clauses.extend(_condition_sentences(text))
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


def course_headers(html: str) -> list[tuple[str, str]]:
    """All recognizable official course headers, including off-site and 0xx codes."""
    parser = _CalendarHTML()
    parser.feed(html)
    headers = []
    for node in parser.root.walk():
        if node.tag != "h3":
            continue
        match = _HEADER_RE.fullmatch(node.text())
        if match:
            headers.append(match.groups())
        elif re.match(r"^[A-Z]{3,5}[A-Z0-9]{2,4}[HY]\d\s*[-•:]", node.text()):
            raise ValueError(f"Unrecognized official course-code format: {node.text()}")
    return headers


def search_last_page(html: str) -> int:
    parser = _CalendarHTML()
    parser.feed(html)
    pages = [
        int(page)
        for node in parser.root.walk()
        if node.tag == "a"
        for page in parse_qs(urlparse(node.attrs.get("href", "")).query).get("page", [])
        if page.isdigit()
    ]
    return max(pages, default=0)


def section_subjects(html: str) -> tuple[str, list[str]]:
    parser = _CalendarHTML()
    parser.feed(html)
    headings = [node.text() for node in parser.root.walk() if node.tag == "h1"]
    title = headings[-1] if headings else ""
    return title, [code for code, _ in course_headers(html)]


def _credit_metadata(code: str, description: str) -> tuple[float | None, str, str]:
    if re.search(r"\bthis (?:is a |is an )?non[- ]credit\b", description, re.I):
        return (
            0.0,
            "explicit_calendar_description",
            "Official Calendar identifies this as a non-credit course; see source URL.",
        )
    if code[:3] in {"COP", "PDC", "INT", "CIP"} or (code[3].isdigit() and code[3] == "0"):
        return (
            None,
            "not_listed_nonstandard_course",
            "Confirm degree-credit weight in the linked official calendar/program rules.",
        )
    return (0.5 if code[-2] == "H" else 1.0), "course_code_HY", ""


def parse_calendar_section(
    html: str, *, campus: str, retrieved_at: str, department: str | None = None
) -> list[dict]:
    """Parse either official search accordions or full unpaginated print exports.

    Printed rows are recognized by their enclosing views-row, not an accordion
    CSS class. Every course header must produce one record, including H0/Y0
    off-site courses and 0xx nonstandard courses; no subject/level sampling.
    """
    host, requirement_system, suffixes = CAMPUS_RULES[campus]
    date.fromisoformat(retrieved_at)
    parser = _CalendarHTML()
    parser.feed(html)
    records = []
    for header in parser.root.walk():
        if header.tag != "h3":
            continue
        match = _HEADER_RE.fullmatch(header.text())
        if not match:
            continue
        code, name = match.groups()
        if code[-1] not in suffixes:
            raise ValueError(f"Unexpected cross-campus code in official course rows: {code}")
        if header.has_class("js-views-accordion-group-header"):
            siblings = header.parent.children
            body = next(
                (node for node in siblings[siblings.index(header) + 1 :] if isinstance(node, _Node)), None
            )
        else:
            body = header.parent
            while body is not None and not body.has_class("views-row"):
                body = body.parent
        if body is None:
            raise ValueError(f"Missing course body: {code}")
        breadth = _field(body, "field-breadth-requirements")
        distribution = _field(body, "field-distribution-requirements")
        categories, labels = _categories(distribution if campus == "Mississauga" else breadth, campus)
        prerequisite = _field(body, "field-prerequisite")
        description = _field(body, "body", "field-desc")
        credit, credit_basis, credit_note = _credit_metadata(code, description)
        records.append(
            {
                "course_code": code,
                "course_name": name,
                "description": "",  # Course prose stays at the official source URL; publish factual metadata only.
                "department": department or f"{code[:3]} (course subject)",
                "department_source": "official_calendar_section" if department else "course_prefix",
                "department_source_url": "",
                "subject_areas": json.dumps([department] if department else []),
                "course_level": (ord(code[3]) - ord("A") + 1) * 100
                if code[-1] == "3"
                else int(code[3]) * 100,
                "credit": credit,
                "credit_basis": credit_basis,
                "credit_note": credit_note,
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
    expected_headers = course_headers(html)
    if not records:
        raise ValueError(f"No recognized courses found for {campus}; calendar markup may have changed")
    if len(expected_headers) != len(records):
        raise ValueError(f"Course headers were silently dropped for {campus}")
    return records


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
        host, system, suffixes = CAMPUS_RULES[record["campus"]]
        if code[-1] not in suffixes or record.get("source_url") != f"https://{host}/course/{code.lower()}":
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
        if record["campus"] != "St. George" and breadth:
            raise ValueError(f"St. George BR numbers cannot be assigned to {record['campus']}: {code}")
        raw = record["distribution_requirements"] if code[-1] == "5" else record["breadth_requirements"]
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
        if record.get("credit_basis") == "course_code_HY" and record.get("credit") != (
            0.5 if code[-2] == "H" else 1.0
        ):
            raise ValueError(f"Course credit does not match official H/Y code: {code}")
        if record.get("credit") is not None and record["credit"] not in (0.0, 0.5, 1.0):
            raise ValueError(f"Unsupported course credit: {code}")
        expected_level = (ord(code[3]) - ord("A") + 1) * 100 if code[-1] == "3" else int(code[3]) * 100
        if record.get("course_level") != expected_level:
            raise ValueError(f"Course level does not match code: {code}")


def load_catalog(path: str | Path | None = None) -> list[dict]:
    """Load and validate the offline snapshot; no network calls or mock metadata."""
    payload = Path(path or CATALOG_PATH).read_bytes()
    records = json.loads(payload)
    validate_catalog(records)
    if path is None:
        import hashlib

        manifest = json.loads((REFERENCE_DIR / "catalog_manifest.json").read_text(encoding="utf-8"))
        if not manifest.get("complete") or manifest["course_count"] != len(records):
            raise ValueError("Default catalogue does not have a complete-export manifest")
        if manifest["catalog_sha256"] != hashlib.sha256(payload).hexdigest():
            raise ValueError("Default catalogue does not match its verified manifest")
        coverage = {campus: sum(row["campus"] == campus for row in records) for campus in CAMPUS_RULES}
        if coverage != manifest["campus_coverage"] or set(coverage) != set(CAMPUS_RULES):
            raise ValueError(f"Incomplete default campus coverage: {coverage}")
    return records
