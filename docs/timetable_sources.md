# Official timetable offering data

Course catalogue entries and scheduled offerings serve different purposes. The
academic calendars remain the source for course descriptions, breadth/distribution
requirements and prerequisites. Offering annotations use only U of T's public
[Timetable Builder](https://ttb.utoronto.ca/).

The official web client inspected on October 13, 2026 uses
`https://api.easi.utoronto.ca/ttb`. The public request shapes were verified from
the JavaScript served by that official website, then confirmed against live API
responses. No third-party mirror, student messages, generated ratings or private
ACORN session is used in this dataset.

| Endpoint | Role |
| --- | --- |
| `GET /reference-data` | Discover published sessions and official division identifiers |
| `POST /getCourses` | Retrieve every offering for an unfiltered division/session query |
| `POST /getPageableCourses` | Independently verify combined and per-session totals |
| `GET /findById?id=…` | Inspect the source record linked by an individual offering |

The three included divisions are `ARTSC` (St. George Faculty of Arts and Science),
`ERIN` (Mississauga), and `SCAR` (Scarborough). St. George's other faculties are
outside this catalogue scope. The checked-in snapshot contains **7,093 offering
records for 6,093 distinct campus/course pairs**: 3,772 Arts & Science records,
1,692 UTM records and 1,629 UTSC records. Each division's complete response count
matches the official pageable total; all nine division/session counts also match.
The manifest records the exact source retrieval time, counts and SHA-256 digest.

The official API published Fall 2026 (`20269`), Winter 2027 (`20271`) and full-year
Fall–Winter 2026–2027 (`20269-20271`) when this snapshot was retrieved. These are
discovered from the source at refresh time, never inferred from today's date.
The API's individual term search excludes full-year records, so the application
explicitly includes a full-year course in both its constituent term filters.

Offering labels mean:

- **offered**: a published offering exists and the course/primary sections are
  not cancelled. Full or closed enrolment still counts as offered.
- **cancelled**: the source marks the course cancelled, or all its primary
  teaching sections are cancelled. Individual section statuses are preserved.
- **not_found**: the course is absent from all relevant, completely retrieved
  published sessions. This does not predict future delivery.
- **unknown**: a session/campus is unpublished, unavailable or incompletely
  retrieved. Missing information never becomes “not offered”.

This is a dated public snapshot, not real-time seat availability or a registration
eligibility decision. The timetable may change after retrieval. Enrolment and
individual eligibility must be confirmed in the university's official services.
The university's publicly accessible API is not claimed to be a versioned,
supported developer product or an openly licensed dataset; review the official
site's applicable terms before further redistribution or high-volume use.

Refresh explicitly with:

```bash
python scripts/update_timetable.py
```

Requests use bounded timeouts, limited retries and throttling. Any download,
validation or count mismatch aborts before replacement, preserving the previous
verified snapshot. Ordinary application starts do not call the university API.
