-- Top recommended courses.
SELECT course_code, course_name, department, avg_rating, avg_workload, recommend_score
FROM ads_course_recommendation
ORDER BY recommend_score DESC
LIMIT 10;

-- Department-level course experience metrics.
SELECT department, course_count, review_count, avg_rating, avg_difficulty, avg_workload
FROM dws_department_summary
ORDER BY avg_rating DESC;

-- Potential GPA-friendly courses.
SELECT course_code, course_name, department, gpa_friendly_score, avg_rating, avg_difficulty, avg_workload
FROM ads_course_profile
WHERE avg_rating >= 4 AND avg_difficulty < 3.5
ORDER BY gpa_friendly_score DESC;
