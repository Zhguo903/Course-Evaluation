# Warehouse Design · v2

CourseInsight uses a local DuckDB database and a layered ODS–DWD–DWS–ADS model. Source CSVs and intermediate CSVs are reproducible working files; the database is the published analytics snapshot.

## Layers

| Layer | Tables | Purpose |
| --- | --- | --- |
| ODS | `ods_courses_raw`, `ods_instructors_raw`, `ods_semesters_raw`, `ods_course_offerings_raw`, `ods_reviews_raw` | Preserve source records for traceability |
| DWD | `dwd_courses_clean`, `dwd_instructors_clean`, `dwd_semesters_clean`, `dwd_course_offerings_clean`, `dwd_reviews_clean` | Standardized entity and fact detail |
| DWS | `dws_course_summary`, `dws_instructor_summary`, `dws_department_summary` | SQL aggregation at course, instructor and department grain |
| DWS | `dws_course_text_features`, `dws_course_tags` | Review mention proportions and generated course tags/keywords |
| ADS | `ads_course_profile`, `ads_course_recommendation`, `ads_data_quality_report` | Derived scores, default ranking and successful publication quality checks |

## Grain and relationships

- Course, instructor and semester dimensions have unique positive integer IDs.
- Each offering references one course, instructor and semester and includes seat capacity and enrollment.
- Each review references the same three dimensions; the triplet must match an actual offering. A review date must be within its semester bounds.
- Review facts aggregate to one row per course in the course summary. Courses without reviews remain visible, with zero review count and NULL averages.
- Tags and profiles are course-level features. Review-count smoothing uses the global review-weighted rating prior.

## Validation and publication

The ETL standardizes types, identifiers and text, and deterministically keeps the first record for a repeated non-null primary key. Missing and invalid values remain visible to validation. The quality report checks required values, uniqueness, ranges, formats, dates, foreign keys and review/offering context.

A failing report is saved to `data/processed/data_quality_report.csv` and raises `DataQualityError` before publication. Building the warehouse directly also runs validation. All warehouse layers are then rebuilt in one DuckDB transaction; a build failure rolls the transaction back. The prior published snapshot remains available after validation or build failures.

The dashboard reads course profiles, review detail and tags from the same database snapshot. It can display the latest CSV quality report, including failed attempts, separately from the successful report persisted in ADS. This prevents invalid intermediate review files from silently changing the published analytics.

`python run_pipeline.py` loads the versioned three-campus official course snapshot and recreates synthetic teachers, offerings and reviews. `python run_pipeline.py --skip-generate` reuses the five source CSVs and applies the same quality gate. CSV and database scoring paths share `sql/04_create_ads_tables.sql`.

## Operating scope

This is a single-user local batch prototype. It does not include a scheduler, incremental change capture or multi-user write coordination. Default course metadata comes from official UofT Calendars; teachers, offerings and review records remain synthetic. A production adaptation would require real-source contracts, privacy controls, ranking evaluation and infrastructure appropriate to its data volume.

The course-level summary retains all standardized course columns, including campus, classification system, JSON category lists, exact prerequisites and source provenance. ADS SQL carries these columns through unchanged, so scoring cannot silently discard enrolment requirements.
