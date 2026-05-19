-- ADS layer: application-ready course profile and recommendation tables.
CREATE OR REPLACE TABLE ads_course_profile AS
WITH course_text_features AS (
    SELECT
        c.course_id,
        AVG(CASE WHEN lower(r.review_text) LIKE '%python%'
                   OR lower(r.review_text) LIKE '%sql%'
                   OR lower(r.review_text) LIKE '%data%'
                   OR lower(r.review_text) LIKE '%machine learning%'
                   OR lower(r.review_text) LIKE '%visualization%'
                   OR lower(r.review_text) LIKE '%project%' THEN 1 ELSE 0 END) AS data_keyword_ratio,
        AVG(CASE WHEN lower(r.review_text) LIKE '%heavy%'
                   OR lower(r.review_text) LIKE '%workload%'
                   OR lower(r.review_text) LIKE '%time consuming%' THEN 1 ELSE 0 END) AS workload_negative_ratio
    FROM dwd_courses_clean c
    LEFT JOIN dwd_reviews_clean r ON c.course_id = r.course_id
    GROUP BY c.course_id
),
scored AS (
    SELECT
        s.course_id,
        s.course_code,
        s.course_name,
        s.department,
        COALESCE(s.avg_rating, 0) AS avg_rating,
        COALESCE(s.avg_difficulty, 0) AS avg_difficulty,
        COALESCE(s.avg_workload, 0) AS avg_workload,
        COALESCE(s.avg_usefulness, 0) AS avg_usefulness,
        0.4 * COALESCE(s.avg_rating, 0)
            + 0.3 * (5 - COALESCE(s.avg_difficulty, 0))
            + 0.3 * (5 - COALESCE(s.avg_workload, 0)) AS gpa_friendly_score,
        COALESCE(s.avg_usefulness, 0) / NULLIF(COALESCE(s.avg_workload, 0), 0) AS course_value_score,
        LEAST(
            5,
            CASE WHEN s.department IN ('Data Science', 'Computer Science', 'Statistics') THEN 3.5 ELSE 2.0 END
            + 2.0 * COALESCE(t.data_keyword_ratio, 0)
        ) AS data_career_relevance_score,
        0.6 * COALESCE(s.avg_workload, 0) + 0.4 * COALESCE(t.workload_negative_ratio, 0) AS workload_risk_score
    FROM dws_course_summary s
    LEFT JOIN course_text_features t ON s.course_id = t.course_id
)
SELECT
    *,
    0.25 * avg_rating
        + 0.20 * gpa_friendly_score
        + 0.20 * data_career_relevance_score
        + 0.15 * COALESCE(course_value_score, 0)
        + 0.10 * avg_usefulness
        + 0.10 * (5 - avg_workload) AS recommend_score
FROM scored;

CREATE OR REPLACE TABLE ads_course_recommendation AS
SELECT *
FROM ads_course_profile
ORDER BY recommend_score DESC;

CREATE OR REPLACE TABLE ads_data_quality_report AS
SELECT * FROM read_csv_auto('data/processed/data_quality_report.csv');
