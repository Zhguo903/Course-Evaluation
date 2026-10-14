# Changelog

## v3.0.0 · 2026-10-13

- Pivot to a fast official-data course finder by campus, level, academic subject and campus-specific breadth/distribution category.
- Replace the 200-course sample with all 10,037 courses in the St. George Arts & Science, UTM and UTSC undergraduate calendars, with pagination completeness evidence.
- Integrate 7,093 real official Timetable Builder records; verify combined and per-session totals and distinguish offered, cancelled, not found and unknown states.
- Remove synthetic teachers, reviews, ratings, GPA/workload predictions and all generation/NLP/recommendation code that depended on them.
- Add explicit academic-area fallback labels, uncertain-credit handling, term-specific source links, session-labelled CSV export and official requirement comparison.
- Publish validated snapshots atomically with source hashes, retrieval dates and coverage manifests; preserve the last verified database on build failure.
- Document usable current and historical data sources, and ship course CSV and DuckDB downloads.

The entries below describe historical releases; their simulated features are absent from v3.

## v2.1.0 · 2026-10-13

- Replace randomly named course metadata with 200 verified official UofT course records: 80 St. George Arts & Science, 60 UTM and 60 UTSC.
- Preserve campus-specific BR/Distribution categories, prerequisites, corequisites, exclusions, preparation, enrolment notes, source URLs and retrieval dates.
- Add an offline versioned catalogue, a reproducible official-source updater and a source manifest.
- Keep St. George BR1–5, UTM Distribution and UTSC Breadth systems separate, including multi-category and unlisted-category courses.
- Add campus/classification filtering and an official-requirements panel; retain literal grade, AND/OR, credit, permission and programme restrictions.
- Update project positioning for University of Toronto students. Attribute community discussion themes to the maintainer, and clearly label generated reviews as synthetic rather than original messages or real student ratings.
- Extend validation and regression coverage for official provenance, full course identifiers and metadata preservation: 80 tests and 60 data-quality checks pass.

Upgrade: run `python run_pipeline.py` to rebuild the local warehouse against the supplied official snapshot. Existing CSVs can still be reused with `--skip-generate`; neutral metadata defaults preserve compatibility, but official attribution requires consistent provenance.

## v2.0.0 · 2026-10-13

### Data and warehouse

- Preserve invalid and missing inputs for honest validation instead of silently clipping scores or filling identifiers.
- Add 48 integrity checks covering all source entities, foreign keys, semester dates, review/offering context and enrollment.
- Gate publication on successful validation; rebuild ODS–ADS in one DuckDB transaction with rollback.
- Persist review detail and course tags in a coherent published snapshot.
- Generate reproducible, course-specific synthetic content and score profiles with complete offering coverage.
- Vectorize mixed-date parsing and cache repeated bounded text-rule evaluations.

### Recommendations and analytics

- Add review-count smoothing with a global rating prior and 10 prior reviews.
- Normalize component scores to a comparable 1–5 range and exclude unreviewed courses from rankings.
- Return actual preference scores with explanations that include both bonuses and penalties.
- Use exact tag matching, review mention shares, phrase boundaries and simple negation.
- Handle empty/stopword documents, missing sources and non-default DataFrame indexes safely.
- Share versioned ADS SQL between the warehouse and CSV fallback.

### Product and maintenance

- Add a Chinese-first six-tab dashboard with shared filters, course comparison, CSV downloads and explicit setup states.
- Compute overview means directly from reviews rather than averaging course means.
- Distinguish failed recent validation attempts from the last successfully published data.
- Rewrite Chinese/English project descriptions, metric definitions and operating instructions.
- Add regression tests, Streamlit AppTest, Ruff checks and GitHub Actions for Python 3.11/3.13.

### Upgrade notes

Reinstall dependencies and run `python run_pipeline.py` to regenerate synthetic inputs and the warehouse. v2 intentionally changes mock-data distributions, score formulas and tag thresholds, so rankings are not comparable to v1. To preserve existing raw CSVs, use `python run_pipeline.py --skip-generate` instead. Runtime and development dependencies are now separated.
