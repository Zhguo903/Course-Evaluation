# Course finder database · v3

The database is generated from two verified official snapshots. No synthetic teachers, reviews, scores or inferred quality features are present.

| Table | Grain and role |
| --- | --- |
| `dwd_catalog_courses` | One row per official campus/course code; catalogue metadata and functional requirements |
| `dwd_timetable_offerings` | One row per official offering identity; course, campus, published session and section status |
| `ads_course_finder` | One row per catalogue course; metadata, aggregate offering state and a per-session status map |
| `ads_timetable_coverage` | One row per campus/published session; source totals, completeness and retrieval time |
| `ads_data_quality_report` | One row per catalogue publication check, with status, detail and UTC check time |
| `ads_source_manifests` | One row per source snapshot, containing its JSON manifest |

Catalogue rows join to offerings using campus and course code. Some official timetable codes are absent from the current calendar and remain in the offering table rather than being silently invented as catalogue rows. Offering counts and distinct course counts have different grains.

Nested arrays and objects are stored as JSON strings in DuckDB for portable CSV export and query access. The finder reads its tables within one transaction. The UI cache key includes database file metadata, so replacement invalidates cached results.

## Validation and publication

The catalogue loader checks schema, official source hosts, code formats, classification systems, uniqueness, campus coverage, manifest count and SHA-256. Its refresh additionally checks official full exports against search pagination totals and first/last sequences.

The timetable loader checks paired source files, SHA-256, unique official identifiers, source hosts, valid divisions/statuses/sessions, all coverage pairs and per-session totals. Both missing files yield unknown coverage; a partial or corrupt pair raises an error. Refresh cross-checks unfiltered results with independent pageable totals before publishing.

The pipeline runs quality checks, creates a fresh temporary DuckDB and atomically replaces the previous database only after success. This also removes obsolete v2 tables. Failed builds preserve the published database and clean temporary files. Offline builds never fetch the network or generate fallback data.

See [data dictionary](data_dictionary.md), [matching rules](matching_rules.md), [timetable provenance](timetable_sources.md) and [query examples](../sql/course_finder_queries.sql).

## Feedback and learning resources · v3.2

Four additional tables extend the database to ten:

- `dwd_course_evaluations`: one historical source report per row; unmatched reports remain unassigned and accessible for audit.
- `dwd_student_reviews`: one attributed individual opinion per course/source entry, retaining its original dimension and scale.
- `dwd_course_resources`: one verified course or general-resource link with original access conditions.
- `ads_feedback_sources`: one feedback provider/dataset with its actual import and access status.

The finder receives availability counts and historical year bounds, not averaged ratings. Student-reported recommendations (1–10) remain separate from historical institutional-question means (1–5). Multiple reports from a single class can share respondents, so survey response counts are not summed as distinct students.

Support metadata is checked against its manifest hashes, exact catalogue associations, source register, rating scales, dates and HTTPS URLs. Historical evaluation loading checks paired files, hashes, source rows, counts, campus and scales; the warehouse also rejects stale current-course associations. Unmatched historical identifiers remain unassigned. Invalid support data aborts publication before replacement, preserving the previous database.

The public-copy source is explicitly attributed and is not represented as a current official evaluation API. Instructor surnames and source course-title columns are excluded. Resource records contain links only; restricted exams or course materials are not mirrored.
