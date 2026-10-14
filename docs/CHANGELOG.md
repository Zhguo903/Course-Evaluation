# Changelog

## v3.2.0 · 2026-10-14 · Public course materials expansion

- Expand learning-resource metadata from 21 to 752 entries (748 unique URLs), including 746 exact associations covering 575 current courses across the three campuses.
- Index 672 syllabi, 18 lecture-note links, 16 material pages, 17 course sites, 10 student guides, 4 practice links, 3 practice exams, 8 past exams and 4 shared-support/exam portals; retain source, period and access limitations without mirroring content.
- Add 5,899 Engineering historical reports; 104 reports give 14 previously uncovered current courses evaluations. Totals: 70,453 reports, 54,196 matched to 6,505 courses, 16,257 unmatched. Missing Engineering recommendation items remain NULL.
- Add resource type/title filters, a 20-card display limit, complete per-course CSV export and distinct course coverage by campus.
- Correct Economics Fall/Winter archive term labels using F/S/Y; exclude broken, ambiguous and mismatched historical links.
- Add explicit metadata discovery commands, batch audit reports, hash-checked deduplication and rollback tests for resource publication.


## v3.1.0 · Student feedback and learning resources

- Import 64,554 third-party historical survey reports, of which 54,092 match 6,491 current catalogue courses; retain 10,462 unmatched reports without fuzzy associations.
- Preserve learning-experience, workload and recommendation items on their original 1–5 scales, missing values, source-row provenance and quality flags.
- Add 28 attributed individual recommendation ratings and Chinese paraphrases from one public CS graduate reflection, with self-report limitations and its original 1–10 scale.
- Add 21 verified learning resource links, including 15 specific links for 11 current courses, and explicitly labelled general, historical or authenticated portals.
- Add a feedback/resources page, course-level availability filters, complete per-course historical CSV export and separate source/access registers.
- Extend the atomic database to 10 tables; validate paired feedback snapshots and publish only factual metadata or numeric facts, without mirrored course materials or synthetic reviews.

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
