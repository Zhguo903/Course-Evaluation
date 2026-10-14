-- Run against data/warehouse/course_insight.duckdb after: python run_pipeline.py

SELECT campus, COUNT(*) AS courses
FROM dwd_catalog_courses
GROUP BY campus
ORDER BY campus;

-- St. George 100-level BR 5 courses with a published offering.
SELECT course_code, course_name, department, prerequisite, source_url,
       offering_status, timetable_source_url
FROM ads_course_finder
WHERE campus = 'St. George'
  AND course_level = 100
  AND json_contains(breadth_categories, '5')
  AND offering_status = 'offered'
ORDER BY course_code;

-- Winter 2027 status, including full-year courses that span winter.
SELECT course_code, course_name,
       json_extract_string(offering_status_by_session, '$."20271"') AS winter_status
FROM ads_course_finder
WHERE campus = 'Scarborough'
ORDER BY course_code;

-- Offering counts have a different grain from catalogue course counts.
SELECT campus, session_code, status, COUNT(*) AS offering_records
FROM dwd_timetable_offerings
GROUP BY campus, session_code, status
ORDER BY campus, session_code, status;

SELECT * FROM ads_timetable_coverage;
SELECT source, manifest FROM ads_source_manifests;
SELECT * FROM ads_data_quality_report;

-- Historical reports: keep campus, period, question meanings and provenance.
SELECT year, term, teaching_section, overall_score, workload_score,
       recommendation_score, response_count, invited_count, source_url,
       source_row_number, quality_flags
FROM dwd_course_evaluations
WHERE campus = 'St. George' AND course_code = 'CSC110Y1'
ORDER BY year DESC, term;

-- Individual opinions retain their own scale; do not blend with survey means.
SELECT course_code, reviewer_label, academic_period, rating,
       rating_scale_min, rating_scale_max, rating_dimension, summary, source_url
FROM dwd_student_reviews
WHERE course_code = 'CSC110Y1';

-- Resource links are metadata, not redistributed course documents.
SELECT title, resource_type, academic_period, access_requirement, url
FROM dwd_course_resources
WHERE campus IN ('St. George', 'All')
  AND (course_code = 'CSC110Y1' OR course_code = '');

-- Count reports, not unique respondents; preserve unassigned historical records.
SELECT campus, match_status, COUNT(*) AS report_count
FROM dwd_course_evaluations
GROUP BY campus, match_status;
