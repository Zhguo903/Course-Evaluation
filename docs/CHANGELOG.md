# Changelog

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
