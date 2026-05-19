-- ODS layer: raw source-aligned tables loaded from CSV files.
CREATE OR REPLACE TABLE ods_courses_raw AS SELECT * FROM read_csv_auto('data/raw/courses_raw.csv');
CREATE OR REPLACE TABLE ods_instructors_raw AS SELECT * FROM read_csv_auto('data/raw/instructors_raw.csv');
CREATE OR REPLACE TABLE ods_semesters_raw AS SELECT * FROM read_csv_auto('data/raw/semesters_raw.csv');
CREATE OR REPLACE TABLE ods_course_offerings_raw AS SELECT * FROM read_csv_auto('data/raw/course_offerings_raw.csv');
CREATE OR REPLACE TABLE ods_reviews_raw AS SELECT * FROM read_csv_auto('data/raw/reviews_raw.csv');
