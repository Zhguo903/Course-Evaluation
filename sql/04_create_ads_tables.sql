-- Text proportions are produced by nlp_tags.mention_ratio with phrase boundaries
-- and simple negation. Run python run_pipeline.py to prepare dws_course_text_features.
-- confidence is the weight on observed ratings, not a statistical confidence interval.
CREATE OR REPLACE TABLE ads_course_profile AS
WITH prior AS (
    SELECT COALESCE(AVG(rating), 3.0) AS global_rating FROM dwd_reviews_clean
), evidence AS (
    SELECT s.*, s.review_count / (s.review_count + 10.0) AS confidence,
           (s.review_count * COALESCE(s.avg_rating, global_rating) + 10 * global_rating)
               / (s.review_count + 10.0) AS smoothed_rating,
           COALESCE(t.data_keyword_ratio, 0) AS data_keyword_ratio,
           COALESCE(t.workload_negative_ratio, 0) AS workload_negative_ratio
    FROM dws_course_summary s
    CROSS JOIN prior
    LEFT JOIN dws_course_text_features t ON s.course_id = t.course_id
), scored AS (
    SELECT *,
        CASE WHEN review_count > 0 THEN
            0.4 * smoothed_rating + 0.3 * (6 - avg_difficulty) + 0.3 * (6 - avg_workload)
        END AS gpa_friendly_score,
        CASE WHEN review_count > 0 THEN
            0.6 * avg_usefulness + 0.4 * (6 - avg_workload)
        END AS course_value_score,
        LEAST(5.0,
            CASE WHEN department IN ('Data Science', 'Computer Science', 'Statistics')
                 THEN 3.5 ELSE 2.0 END + 2.0 * data_keyword_ratio
        ) AS data_career_relevance_score,
        CASE WHEN review_count > 0 THEN
            0.6 * avg_workload + 0.4 * (1 + 4 * workload_negative_ratio)
        END AS workload_risk_score
    FROM evidence
)
SELECT *,
       CASE WHEN review_count > 0 THEN
           0.25 * smoothed_rating + 0.20 * gpa_friendly_score
           + 0.20 * data_career_relevance_score + 0.15 * course_value_score
           + 0.10 * avg_usefulness + 0.10 * (6 - avg_workload)
       END AS recommend_score
FROM scored;

CREATE OR REPLACE TABLE ads_course_recommendation AS
SELECT * FROM ads_course_profile
WHERE review_count > 0 AND recommend_score IS NOT NULL
ORDER BY recommend_score DESC, course_code ASC;

CREATE OR REPLACE TABLE ads_data_quality_report AS
SELECT * FROM read_csv_auto('data/processed/data_quality_report.csv');
