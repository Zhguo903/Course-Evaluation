# Data dictionary · v3

## Catalogue and finder

`dwd_catalog_courses` contains the verified catalogue; `ads_course_finder` adds offering annotations. Each row represents one campus/course code. JSON arrays/maps are stored as JSON strings in DuckDB and CSV.

| Field | Meaning |
| --- | --- |
| `course_code`, `course_name` | Official course identifier and title |
| `campus` | Source calendar affiliation: St. George, Mississauga or Scarborough |
| `course_level` | 0 / 100 / 200 / 300 / 400; UTSC A–D mapped to 100–400 |
| `department` | First matched official academic-area label, or explicitly labelled course-prefix fallback; multiple areas are not concatenated here |
| `subject_areas` | JSON array of all matched official academic-area labels; empty for course-prefix fallback |
| `department_source` | `official_calendar_section` or `course_prefix` |
| `department_source_url` | Section URL for the first matched academic-area label; empty for fallback |
| `credit` | Standard H/Y credit, explicit non-credit zero, or NULL when uncertain |
| `credit_basis`, `credit_note` | Basis (`course_code_HY`, `explicit_calendar_description` or `not_listed_nonstandard_course`) and qualification for the recorded credit |
| `requirement_system` | `artsci_breadth`, `utm_distribution`, `utsc_breadth` |
| `requirement_categories` | JSON array of official category names |
| `breadth_categories` | St. George BR integers as a JSON array; empty for other systems |
| `breadth_requirements`, `distribution_requirements` | Original official category field text |
| `prerequisite`, `prerequisite_status` | Official prerequisite text and `listed` / `not_listed` status |
| `corequisite`, `exclusion` | Official co-requisite and exclusion conditions |
| `recommended_preparation` | Official recommended preparation |
| `enrolment_requirements`, `requirement_notes` | Explicit restrictions and complete original condition sentences, with short dependent context; labelled NOTE blocks and explicit calendar note fields retain their original wording |
| `description` | Reserved empty field; read the complete description at `source_url` |
| `source_url`, `source_retrieved_at` | Official course page and catalogue retrieval date |
| `metadata_source` | `official_calendar` |
| `offering_status` | `offered`, `cancelled`, `not_found` or `unknown`, across covered sessions |
| `offering_status_by_session` | JSON map from published session code to independent status |
| `offered_sessions` | JSON array of sessions with uncancelled offerings; full-year includes constituent terms |
| `offering_sessions` | JSON array with offering session, label, term, state and official source link |
| `checked_sessions` | JSON array of published source sessions |
| `timetable_source_url` | Official timetable source link for the course, when available |
| `timetable_checked_at`, `timetable_retrieved_at` | Retrieval timestamp; second field is an alias for UI compatibility |
| `match_reason` | Added to a filtered result/export; explains matched user conditions |
| `selected_session`, `selected_session_label` | Export context: selected session code (or `all_published`) and UI label |
| `category_summary` | Compact category display in UI/export; original full labels remain in requirement fields |

Empty requirements mean not listed, not confirmed absence. Missing credit is not zero. Catalogue affiliation does not guarantee physical delivery location. Status definitions are in [data sources](data_sources.md).

## Official offerings

`dwd_timetable_offerings` retains official timetable records, including codes that are not found in the current catalogue.

| Field | Meaning |
| --- | --- |
| `timetable_id` | Unique official source offering identity |
| `course_code`, `title`, `campus` | Source course metadata |
| `division` | `ARTSC`, `ERIN` or `SCAR` |
| `session_code`, `sessions`, `term_code` | Published session, constituent session array and F/S/Y term |
| `status` | Normalized course offering state: `offered` or `cancelled` |
| `sections` | JSON array of actual section status and delivery modes; no real-time seat counts |
| `source_url`, `timetable_url` | Official individual record and public timetable website |
| `source_retrieved_at` | Timestamp at snapshot retrieval |
| `source_created_at`, `source_modified_at` | Source timestamps when supplied |

## Coverage, manifests and quality

`ads_timetable_coverage` stores campus, division, session, human-readable label, complete flag, source totals, expected totals and retrieval timestamp. Only verified complete coverage supports `not_found`; missing coverage yields `unknown`.

`ads_source_manifests` holds source name and its JSON manifest, including hashes, source URLs, retrieval dates and completeness evidence. The checked-in reference files use the same manifests.

`ads_data_quality_report` contains `check_name`, `status`, `detail` and `check_time`. Publication is blocked if any required check fails. Timetable integrity is checked by its strict snapshot loader before database publication.
