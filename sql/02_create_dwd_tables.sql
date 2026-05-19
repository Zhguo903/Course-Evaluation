-- DWD layer: cleaned detail tables loaded from processed CSV files.
CREATE OR REPLACE TABLE dwd_courses_clean AS SELECT * FROM read_csv_auto('data/processed/courses_clean.csv');
CREATE OR REPLACE TABLE dwd_instructors_clean AS SELECT * FROM read_csv_auto('data/processed/instructors_clean.csv');
CREATE OR REPLACE TABLE dwd_semesters_clean AS SELECT * FROM read_csv_auto('data/processed/semesters_clean.csv');
CREATE OR REPLACE TABLE dwd_course_offerings_clean AS SELECT * FROM read_csv_auto('data/processed/course_offerings_clean.csv');
CREATE OR REPLACE TABLE dwd_reviews_clean AS SELECT * FROM read_csv_auto('data/processed/reviews_clean.csv');
