# CourseInsight: Campus Course Review Data Warehouse & Recommendation System

中文名：校园课程评价数据仓库与智能选课推荐系统

CourseInsight is a local, resume-ready data engineering and analytics engineering project. It generates synthetic campus course review data, cleans it through an ETL pipeline, builds an ODS-DWD-DWS-ADS warehouse in DuckDB, creates NLP-based course tags, recommends courses from user preferences, checks data quality, and serves results in a Streamlit dashboard.

No real student data is used. All records are fictional.

## Project Overview

This project demonstrates how raw course review data can become reliable analytics and recommendation products:

1. Generate synthetic raw CSV files.
2. Clean and standardize data with pandas.
3. Build a layered local data warehouse with DuckDB.
4. Calculate SQL metrics for courses, instructors, and departments.
5. Extract NLP keywords and rule-based course tags.
6. Recommend courses based on user preferences.
7. Validate data quality with automated checks.
8. Present results in a Streamlit + Plotly dashboard.

## Why This Project Matters

Course reviews are messy, subjective, and text-heavy. A realistic data product must combine ETL, dimensional thinking, SQL metrics, NLP, quality checks, and user-facing analytics. CourseInsight packages those skills into a compact project that can run locally and be reviewed easily on GitHub.

## Big Tech Data Skills Demonstrated

| Skill | How It Is Demonstrated |
| --- | --- |
| ETL | pandas pipeline cleans raw CSVs into processed tables |
| SQL | DuckDB SQL creates DWS summaries and ADS scoring tables |
| Data Warehouse | ODS-DWD-DWS-ADS layered architecture |
| Dimensional Modeling | Course, instructor, semester dimensions plus offering/review facts |
| Data Quality | Automated uniqueness, null, range, format, and consistency checks |
| NLP | TF-IDF keyword extraction and rule-based sentiment/tags |
| Recommendation System | Preference-based scoring and TF-IDF cosine similarity |
| BI Dashboard | Streamlit and Plotly dashboard for metrics and recommendations |
| Automation | `run_pipeline.py` runs the full local pipeline |
| Scalable Extension | README documents PySpark, Airflow, and validation platform upgrades |

## Architecture

```text
Raw CSV Data
    -> pandas ETL
Processed CSV Data
    -> DuckDB Warehouse
ODS -> DWD -> DWS -> ADS
    -> NLP Tags + Recommendation Tables
    -> Streamlit Dashboard
```

## Data Warehouse Design

| Layer | Purpose | Example Tables |
| --- | --- | --- |
| ODS | Preserve raw source data | ods_courses_raw, ods_reviews_raw |
| DWD | Clean row-level detail data | dwd_courses_clean, dwd_reviews_clean |
| DWS | Reusable subject summaries | dws_course_summary, dws_department_summary |
| ADS | Application-ready outputs | ads_course_profile, ads_course_recommendation |

## Metrics Definition

Key metrics include `avg_rating`, `avg_difficulty`, `avg_workload`, `avg_usefulness`, `gpa_friendly_score`, `course_value_score`, `data_career_relevance_score`, `workload_risk_score`, and `recommend_score`.

See `docs/metrics_definition.md` for formulas.

## NLP Tagging Logic

Course comments are cleaned and grouped by course. TF-IDF extracts top keywords, and rule-based logic generates tags such as:

- GPA Friendly
- Heavy Workload
- Project Based
- Coding Heavy
- Math Heavy
- Exam Heavy
- Data Science Friendly
- Theory Heavy
- Practical
- Good Instructor

## Recommendation Logic

`src/recommender.py` supports:

- Preference-based Top N recommendations
- Recommendation explanations
- Similar-course search using TF-IDF and cosine similarity over tags, keywords, department, and course title

Example preferences:

```python
{
    "prefer_low_workload": True,
    "prefer_high_rating": True,
    "prefer_project_based": True,
    "prefer_data_science": True,
    "prefer_gpa_friendly": False,
    "avoid_exam_heavy": True,
}
```

## Data Quality Checks

The data quality module validates:

1. `course_id` uniqueness
2. `review_id` uniqueness
3. Non-null `course_code`
4. Non-empty `review_text`
5. `rating` between 1 and 5
6. `difficulty` between 1 and 5
7. `workload` between 1 and 5
8. Course code format like `STA303`
9. `enrolled_count <= capacity`
10. Each table has more than 0 rows

## How to Run

Create and activate a Python 3.10+ environment, then run:

```bash
pip install -r requirements.txt
python run_pipeline.py
streamlit run app/streamlit_app.py
```

Or run steps individually:

```bash
python src/generate_mock_data.py
python src/etl.py
python src/nlp_tags.py
python src/warehouse.py
python src/data_quality.py
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```

## Project Structure

```text
course-insight/
├── app/
├── data/
│   ├── raw/
│   ├── processed/
│   └── warehouse/
├── docs/
├── notebooks/
├── sql/
├── src/
├── tests/
├── README.md
├── requirements.txt
└── run_pipeline.py
```

## Dashboard Preview

Dashboard screenshots can be added after running the Streamlit app locally. Suggested screenshots:

- Overview metrics and department charts
- Course profile tab
- Recommendation results
- Similar courses tab
- Data quality report

## Future Improvements

- Replace pandas with PySpark for large-scale review data
- Add Airflow DAG for scheduled ETL
- Add Great Expectations for enterprise-level data validation
- Add PostgreSQL or Snowflake as warehouse backend
- Add Superset dashboard
- Add user login and personalized recommendation history

## Resume Bullet Points

- Built an end-to-end campus course review analytics platform with synthetic data generation, ETL, DuckDB warehouse modeling, NLP tagging, recommendation logic, data quality checks, and Streamlit BI dashboard.
- Designed ODS-DWD-DWS-ADS warehouse layers and implemented SQL metrics for course, instructor, and department analytics.
- Implemented TF-IDF keyword extraction and rule-based course tags to support explainable course recommendations.
- Created automated data quality checks covering uniqueness, nulls, score ranges, code format, enrollment capacity, and table row counts.
