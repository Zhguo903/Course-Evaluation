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
| reviews_clean.csv | Clean review fact table with normalized text and clipped scores |
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
| ADS | ads_course_profile | Application-ready course profiles and scores |
| ADS | ads_course_recommendation | Sorted recommendation table |
| ADS | ads_data_quality_report | BI-ready quality report |
