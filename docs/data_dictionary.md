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

## Student feedback and resources · v3.1

`dwd_course_evaluations` contains **historical aggregate reports**, including records that cannot be assigned to the current catalogue. It does not contain individual student answers or free-text survey comments.

| Field | Meaning |
| --- | --- |
| `evaluation_id` | Stable identifier from source-file hash and CSV row number |
| `source_course_code` | Original source identifier, including malformed values for audit |
| `course_code`, `campus` | Exact current-code/campus association, or empty code when unmatched |
| `match_status`, `match_basis` | Matched/unmatched and exact-code basis; no title/prefix fuzzy matching |
| `year`, `term`, `teaching_section` | Historical teaching period and section when identified |
| `cohort_id` | Source class/year/term identity hash; multiple reports can share a respondent cohort |
| `overall_score` | Historical overall learning-experience mean on the original 1–5 scale |
| `workload_score` | Historical relative-workload mean on 1–5; higher means heavier, not harder |
| `recommendation_score` | Historical willingness-to-recommend mean on 1–5 |
| `response_count`, `invited_count` | Report-level survey counts; not per-item responses or a unique-student total |
| `quality_flags` | JSON array retaining source anomalies and possible shared cohorts |
| `source_id`, `source_row_number`, `source_url`, `source_retrieved_at` | Original public file, row, link and retrieval time |
| `source_kind` | `third_party_historical_official_evaluations`; not a live official feed |

Missing scores/counts remain NULL. The three measures must not be blended into a universal rating. Full source provenance, scales and irregularities are documented in [feedback sources](feedback_data_sources.md).

`dwd_student_reviews` stores `review_id`, exact `course_code`/`campus`, original `source_course_code`, reviewer/source labels, academic period, publication date when known, retrieval date, original `rating`/`rating_scale_min`/`rating_scale_max`/`rating_dimension`, Chinese `summary`, `code_mapping`, `verification_level` and `limitations`. Current entries are public self-reports from one author, with individual recommendation values on 1–10. No student identity or enrolment status was verified, and no cross-review average is calculated.

`dwd_course_resources` stores `resource_id`, `course_code`, `campus`, `title`, `resource_type`, `url`, `provider`, `source_kind`, `academic_period`, `access_requirement`, `rights_note`, `verified_at`, `source_url` and `limitations`. Empty course code means a general or unassigned historical portal; campus `All` means a shared portal. This never turns into one resource record per catalogue course. Files contain metadata and links, not mirrored teaching materials.

`ads_feedback_sources` stores `source_id`, `title`, `source_type`, `status`, `access`, `covered_period`, `source_url` and `limitations`. An external link or a login/licence requirement does not count as imported feedback.

`ads_course_finder` adds `student_review_count`, `historical_evaluation_count`, `resource_count`, `evaluation_year_min` and `evaluation_year_max`. Counts include only exact campus/course associations; resource counts exclude unassigned/global portals. They describe availability, not quality or confidence. Source manifests now include the support and historical-evaluation snapshots.
