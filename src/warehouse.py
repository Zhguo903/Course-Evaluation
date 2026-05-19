"""DuckDB warehouse builder for ODS, DWD, DWS, and ADS layers."""

from __future__ import annotations

import duckdb

try:
    from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from src.data_quality import main as run_quality_report
    from src.utils import log_step
except ImportError:  # pragma: no cover
    from config import DUCKDB_PATH, PROCESSED_DATA_DIR, PROCESSED_FILES, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from data_quality import main as run_quality_report
    from utils import log_step


def init_duckdb() -> duckdb.DuckDBPyConnection:
    """Create or connect to the local DuckDB warehouse."""
    ensure_directories()
    return duckdb.connect(str(DUCKDB_PATH))


def _create_table_from_csv(conn: duckdb.DuckDBPyConnection, table_name: str, csv_path) -> None:
    """Replace a DuckDB table with data loaded from a CSV file."""
    conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)", [str(csv_path)])


def build_ods_layer(conn: duckdb.DuckDBPyConnection) -> None:
    """Build ODS tables directly from raw CSV files."""
    log_step("Building ODS layer")
    table_map = {
        "ods_courses_raw": RAW_FILES["courses"],
        "ods_instructors_raw": RAW_FILES["instructors"],
        "ods_semesters_raw": RAW_FILES["semesters"],
        "ods_course_offerings_raw": RAW_FILES["offerings"],
        "ods_reviews_raw": RAW_FILES["reviews"],
    }
    for table_name, filename in table_map.items():
        _create_table_from_csv(conn, table_name, RAW_DATA_DIR / filename)


def build_dwd_layer(conn: duckdb.DuckDBPyConnection) -> None:
    """Build DWD clean tables from processed CSV files."""
    log_step("Building DWD layer")
    table_map = {
        "dwd_courses_clean": PROCESSED_FILES["courses"],
        "dwd_instructors_clean": PROCESSED_FILES["instructors"],
        "dwd_semesters_clean": PROCESSED_FILES["semesters"],
        "dwd_course_offerings_clean": PROCESSED_FILES["offerings"],
        "dwd_reviews_clean": PROCESSED_FILES["reviews"],
    }
    for table_name, filename in table_map.items():
        _create_table_from_csv(conn, table_name, PROCESSED_DATA_DIR / filename)


def build_dws_layer(conn: duckdb.DuckDBPyConnection) -> None:
    """Build DWS subject summary tables for courses, instructors, and departments."""
    log_step("Building DWS layer")
    conn.execute(
        """
        CREATE OR REPLACE TABLE dws_course_summary AS
        SELECT
            c.course_id,
            c.course_code,
            c.course_name,
            c.department,
            c.course_level,
            COUNT(r.review_id) AS review_count,
            ROUND(AVG(r.rating), 3) AS avg_rating,
            ROUND(AVG(r.difficulty), 3) AS avg_difficulty,
            ROUND(AVG(r.workload), 3) AS avg_workload,
            ROUND(AVG(r.usefulness), 3) AS avg_usefulness,
            ROUND(AVG(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END), 3) AS positive_review_ratio,
            ROUND(AVG(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END), 3) AS negative_review_ratio
        FROM dwd_courses_clean c
        LEFT JOIN dwd_reviews_clean r ON c.course_id = r.course_id
        GROUP BY c.course_id, c.course_code, c.course_name, c.department, c.course_level
        """
    )
    conn.execute(
        """
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
        GROUP BY i.instructor_id, i.instructor_name, i.department
        """
    )
    conn.execute(
        """
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
        GROUP BY c.department
        """
    )


def build_ads_layer(conn: duckdb.DuckDBPyConnection) -> None:
    """Build ADS application tables for course profiles, recommendations, and data quality."""
    log_step("Building ADS layer")
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE course_text_features AS
        SELECT
            c.course_id,
            AVG(CASE WHEN lower(r.review_text) LIKE '%python%'
                       OR lower(r.review_text) LIKE '%sql%'
                       OR lower(r.review_text) LIKE '%data%'
                       OR lower(r.review_text) LIKE '%machine learning%'
                       OR lower(r.review_text) LIKE '%visualization%'
                       OR lower(r.review_text) LIKE '%project%' THEN 1 ELSE 0 END) AS data_keyword_ratio,
            AVG(CASE WHEN lower(r.review_text) LIKE '%heavy%'
                       OR lower(r.review_text) LIKE '%workload%'
                       OR lower(r.review_text) LIKE '%time consuming%' THEN 1 ELSE 0 END) AS workload_negative_ratio
        FROM dwd_courses_clean c
        LEFT JOIN dwd_reviews_clean r ON c.course_id = r.course_id
        GROUP BY c.course_id
        """
    )
    conn.execute(
        """
        CREATE OR REPLACE TABLE ads_course_profile AS
        WITH scored AS (
            SELECT
                s.course_id,
                s.course_code,
                s.course_name,
                s.department,
                COALESCE(s.avg_rating, 0) AS avg_rating,
                COALESCE(s.avg_difficulty, 0) AS avg_difficulty,
                COALESCE(s.avg_workload, 0) AS avg_workload,
                COALESCE(s.avg_usefulness, 0) AS avg_usefulness,
                0.4 * COALESCE(s.avg_rating, 0)
                    + 0.3 * (5 - COALESCE(s.avg_difficulty, 0))
                    + 0.3 * (5 - COALESCE(s.avg_workload, 0)) AS gpa_friendly_score,
                COALESCE(s.avg_usefulness, 0) / NULLIF(COALESCE(s.avg_workload, 0), 0) AS course_value_score,
                LEAST(
                    5,
                    CASE WHEN s.department IN ('Data Science', 'Computer Science', 'Statistics') THEN 3.5 ELSE 2.0 END
                    + 2.0 * COALESCE(t.data_keyword_ratio, 0)
                ) AS data_career_relevance_score,
                0.6 * COALESCE(s.avg_workload, 0) + 0.4 * COALESCE(t.workload_negative_ratio, 0) AS workload_risk_score
            FROM dws_course_summary s
            LEFT JOIN course_text_features t ON s.course_id = t.course_id
        )
        SELECT
            *,
            0.25 * avg_rating
                + 0.20 * gpa_friendly_score
                + 0.20 * data_career_relevance_score
                + 0.15 * COALESCE(course_value_score, 0)
                + 0.10 * avg_usefulness
                + 0.10 * (5 - avg_workload) AS recommend_score
        FROM scored
        """
    )
    conn.execute(
        """
        CREATE OR REPLACE TABLE ads_course_recommendation AS
        SELECT *
        FROM ads_course_profile
        ORDER BY recommend_score DESC
        """
    )
    quality_path = PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"]
    if not quality_path.exists():
        run_quality_report()
    _create_table_from_csv(conn, "ads_data_quality_report", quality_path)


def build_warehouse() -> None:
    """Build all warehouse layers in dependency order."""
    conn = init_duckdb()
    try:
        build_ods_layer(conn)
        build_dwd_layer(conn)
        build_dws_layer(conn)
        build_ads_layer(conn)
        log_step(f"DuckDB warehouse saved to {DUCKDB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    build_warehouse()
