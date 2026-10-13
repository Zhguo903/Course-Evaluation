# Data Dictionary

## Raw Tables

### courses_raw.csv
| Field | Description |
| --- | --- |
| course_id | Synthetic unique course identifier |
| course_code | Campus-style course code, such as STA303 |
| course_name | Synthetic course title |
| department | Academic department |
| course_level | Course level, such as 100, 200, 300, or 400 |
| credit | Course credit value |
| prerequisite | Synthetic prerequisite course code |
| campus | Campus where the course is offered |

### instructors_raw.csv
| Field | Description |
| --- | --- |
| instructor_id | Synthetic unique instructor identifier |
| instructor_name | Fictional instructor name |
| department | Instructor department |

### semesters_raw.csv
| Field | Description |
| --- | --- |
| semester_id | Synthetic unique semester identifier |
| year | Academic year |
| term | Spring or Fall |
| start_date | Semester start date |
| end_date | Semester end date |

### course_offerings_raw.csv
| Field | Description |
| --- | --- |
| offering_id | Synthetic unique offering identifier |
| course_id | Course identifier |
| instructor_id | Instructor identifier |
| semester_id | Semester identifier |
| capacity | Seat capacity |
| enrolled_count | Number of enrolled students |
| delivery_mode | In-person, Online, or Hybrid |

### reviews_raw.csv
| Field | Description |
| --- | --- |
| review_id | Synthetic unique review identifier |
| course_id | Course identifier |
| instructor_id | Instructor identifier |
| semester_id | Semester identifier |
| rating | Overall rating from 1 to 5 |
| difficulty | Difficulty score from 1 to 5 |
| workload | Workload score from 1 to 5 |
| usefulness | Usefulness score from 1 to 5 |
| review_text | Synthetic English review text |
| review_date | Review date |

## Processed Tables

Processed tables mirror the raw entities after cleaning:

| Table | Purpose |
| --- | --- |
| courses_clean.csv | Standardized course dimension |
| instructors_clean.csv | Clean instructor dimension |
| semesters_clean.csv | Clean semester dimension |
| course_offerings_clean.csv | Clean offering fact table |
| reviews_clean.csv | Clean review facts with normalized text; invalid scores remain visible to validation |
| course_tags.csv | Course-level NLP keywords and generated tags |
| data_quality_report.csv | Rule-level quality check results |

## Warehouse Tables

| Layer | Table | Purpose |
| --- | --- | --- |
| ODS | ods_*_raw | Raw source-aligned tables |
| DWD | dwd_*_clean | Clean detail tables |
| DWS | dws_course_summary | Course-level metrics |
| DWS | dws_instructor_summary | Instructor-level metrics |
| DWS | dws_department_summary | Department-level metrics |
| DWS | dws_course_text_features | Non-negated review mention proportions |
| DWS | dws_course_tags | Published course keyword/tag snapshot |
| ADS | ads_course_profile | Application-ready course profiles, review counts and smoothed scores |
| ADS | ads_course_recommendation | Sorted recommendation table |
| ADS | ads_data_quality_report | BI-ready quality report |

## v2 Profile and Recommendation Fields

| Field | Meaning |
| --- | --- |
| review_count | Number of valid reviews; known zero-review courses are excluded from rankings |
| confidence | n / (n + 10), the weight of a course mean in rating smoothing, not an accuracy probability |
| smoothed_rating | Review-count weighted blend of the course rating and global review mean |
| recommend_score | Default 1–5 weighted course-profile ranking score |
| preference_score | Actual ranking score after explicit preference adjustments; may exceed 5 |
| recommendation_reason | Explanation aligned with the applied preference contributions |
| similarity_score | TF-IDF cosine similarity of course content, between 0 and 1 |

## Data Quality Report

`check_name`, `table_name`, `status`, `failed_count`, `total_count`, `failure_rate`, and UTC `check_time` describe each check. Empty tables have a failing presence check and zero record counts; this avoids inventing a failing record. A row can fail multiple checks, so summed failed_count is a count of rule violations rather than distinct bad records.

Required source columns must be present as shown above. Optional course prerequisites may be empty. Text analytics currently supports English comments; the interface is Chinese-first. Numeric scores must lie within 1–5. Dates must parse successfully, semester start must not exceed end, and reviews must fall inside the referenced semester.
