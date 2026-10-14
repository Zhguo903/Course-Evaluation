-- DWS layer: reusable subject-level summary tables.
CREATE OR REPLACE TABLE dws_course_summary AS
        WITH review_metrics AS (
            SELECT
                course_id,
                COUNT(review_id) AS review_count,
                ROUND(AVG(rating), 3) AS avg_rating,
                ROUND(AVG(difficulty), 3) AS avg_difficulty,
                ROUND(AVG(workload), 3) AS avg_workload,
                ROUND(AVG(usefulness), 3) AS avg_usefulness,
                ROUND(AVG(CASE WHEN rating >= 4 THEN 1 ELSE 0 END), 3) AS positive_review_ratio,
                ROUND(AVG(CASE WHEN rating <= 2 THEN 1 ELSE 0 END), 3) AS negative_review_ratio
            FROM dwd_reviews_clean
            GROUP BY course_id
        )
        SELECT c.*, COALESCE(m.review_count, 0) AS review_count,
               m.avg_rating, m.avg_difficulty, m.avg_workload, m.avg_usefulness,
               m.positive_review_ratio, m.negative_review_ratio
        FROM dwd_courses_clean c
        LEFT JOIN review_metrics m ON c.course_id = m.course_id;

CREATE OR REPLACE TABLE dws_instructor_summary AS
SELECT
    i.instructor_id,
    i.instructor_name,
    i.department,
    COUNT(r.review_id) AS review_count,
    ROUND(AVG(r.rating), 3) AS avg_rating,
    ROUND(AVG(r.difficulty), 3) AS avg_difficulty,
    ROUND(AVG(r.workload), 3) AS avg_workload
FROM dwd_instructors_clean i
LEFT JOIN dwd_reviews_clean r ON i.instructor_id = r.instructor_id
GROUP BY i.instructor_id, i.instructor_name, i.department;

CREATE OR REPLACE TABLE dws_department_summary AS
SELECT
    c.department,
    COUNT(DISTINCT c.course_id) AS course_count,
    COUNT(r.review_id) AS review_count,
    ROUND(AVG(r.rating), 3) AS avg_rating,
    ROUND(AVG(r.difficulty), 3) AS avg_difficulty,
    ROUND(AVG(r.workload), 3) AS avg_workload,
    ROUND(AVG(r.usefulness), 3) AS avg_usefulness
FROM dwd_courses_clean c
LEFT JOIN dwd_reviews_clean r ON c.course_id = r.course_id
GROUP BY c.department;
