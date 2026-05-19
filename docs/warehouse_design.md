# Warehouse Design

CourseInsight uses a local DuckDB database to model a compact but realistic ODS-DWD-DWS-ADS data warehouse.

## ODS: Operational Data Store

ODS tables preserve the raw CSV shape with minimal transformation. They are useful for lineage, debugging, and comparing source data against cleaned tables.

Tables:
- ods_courses_raw
- ods_instructors_raw
- ods_semesters_raw
- ods_course_offerings_raw
- ods_reviews_raw

## DWD: Data Warehouse Detail

DWD tables contain cleaned, standardized, row-level detail data. Examples include normalized course codes, numeric score fields, clipped rating ranges, and cleaned review text.

Tables:
- dwd_courses_clean
- dwd_instructors_clean
- dwd_semesters_clean
- dwd_course_offerings_clean
- dwd_reviews_clean

## DWS: Data Warehouse Summary

DWS tables aggregate reusable business metrics by subject area.

Tables:
- dws_course_summary: course-level review count, average scores, positive and negative review ratios
- dws_instructor_summary: instructor-level review count and average score metrics
- dws_department_summary: department-level course count, review count, and average experience metrics

## ADS: Application Data Service

ADS tables are shaped for dashboards and recommendation use cases. They combine DWS metrics with derived scoring logic.

Tables:
- ads_course_profile: course profile with GPA-friendly, value, data-career relevance, workload risk, and recommendation scores
- ads_course_recommendation: sorted course profile table for recommendation consumption
- ads_data_quality_report: data quality report loaded into the warehouse for monitoring

## Design Notes

This MVP uses DuckDB for local analytics and reproducibility. In a production environment, the same layered model could be migrated to Snowflake, BigQuery, PostgreSQL, or Spark-based lakehouse tables.
