-- Reviewed courses ranked by a 1–5 heuristic; smoothed ratings use a 10-review prior.
SELECT course_code, course_name, department, course_level, review_count,
       avg_rating, smoothed_rating, confidence, avg_workload, recommend_score
FROM ads_course_recommendation
ORDER BY recommend_score DESC, course_code ASC
LIMIT 10;

-- Department-level course experience metrics, weighted by review count.
SELECT department, course_count, review_count, avg_rating, avg_difficulty, avg_workload
FROM dws_department_summary
ORDER BY avg_rating DESC NULLS LAST, department ASC;

-- Potential GPA-friendly courses with observed difficulty and smoothed rating.
SELECT course_code, course_name, department, review_count, gpa_friendly_score,
       avg_rating, smoothed_rating, avg_difficulty, avg_workload
FROM ads_course_profile
WHERE review_count > 0 AND smoothed_rating >= 4 AND avg_difficulty < 3.5
ORDER BY gpa_friendly_score DESC, course_code ASC;
