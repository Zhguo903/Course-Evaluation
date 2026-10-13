"""DuckDB warehouse builder for ODS, DWD, DWS, and ADS layers."""

from __future__ import annotations

import duckdb
import pandas as pd

try:
    from src.config import (
        DUCKDB_PATH,
        PROCESSED_DATA_DIR,
        PROCESSED_FILES,
        RAW_DATA_DIR,
        RAW_FILES,
        SQL_DIR,
        ensure_directories,
    )
    from src.data_quality import assert_quality, main as run_quality_report
    from src.nlp_tags import DATA_KEYWORDS, WORKLOAD_KEYWORDS, mention_ratio
    from src.utils import log_step
except ImportError:  # pragma: no cover
    from config import (
        DUCKDB_PATH,
        PROCESSED_DATA_DIR,
        PROCESSED_FILES,
        RAW_DATA_DIR,
        RAW_FILES,
        SQL_DIR,
        ensure_directories,
    )
    from data_quality import assert_quality, main as run_quality_report
    from nlp_tags import DATA_KEYWORDS, WORKLOAD_KEYWORDS, mention_ratio
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
            ROUND(AVG(CASE WHEN r.review_id IS NULL THEN NULL WHEN r.rating >= 4 THEN 1 ELSE 0 END), 3) AS positive_review_ratio,
            ROUND(AVG(CASE WHEN r.review_id IS NULL THEN NULL WHEN r.rating <= 2 THEN 1 ELSE 0 END), 3) AS negative_review_ratio
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


def _text_features(reviews: pd.DataFrame) -> pd.DataFrame:
    """Review mention proportions shared by the SQL warehouse and CSV fallback."""
    rows = []
    for course_id, group in reviews.groupby("course_id"):
        texts = group["review_text"].tolist()
        rows.append(
            {
                "course_id": course_id,
                "data_keyword_ratio": mention_ratio(texts, DATA_KEYWORDS),
                "workload_negative_ratio": mention_ratio(texts, WORKLOAD_KEYWORDS),
            }
        )
    result = pd.DataFrame(rows, columns=["course_id", "data_keyword_ratio", "workload_negative_ratio"])
    if result.empty:
        # Keep the join key compatible with integer course ids for an empty review table.
        result = result.astype(
            {
                "course_id": reviews["course_id"].dtype,
                "data_keyword_ratio": "float64",
                "workload_negative_ratio": "float64",
            }
        )
    return result


def _ads_statements() -> list[str]:
    """Use the versioned SQL as the single definition of application metrics."""
    return (SQL_DIR / "04_create_ads_tables.sql").read_text().split(";")


def build_course_profile(summary: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """Apply the exact warehouse scoring SQL to a CSV-derived course summary."""
    with duckdb.connect(":memory:") as conn:
        conn.register("dws_course_summary", summary)
        conn.register("dwd_reviews_clean", reviews)
        conn.register("dws_course_text_features", _text_features(reviews))
        conn.execute(_ads_statements()[0])
        return conn.execute("SELECT * FROM ads_course_profile ORDER BY course_code").df()


def build_ads_layer(conn: duckdb.DuckDBPyConnection) -> None:
    """Build course profiles with volume-aware ratings and bounded 1–5 scores."""
    log_step("Building ADS layer")
    reviews = conn.execute("SELECT course_id, review_text FROM dwd_reviews_clean").df()
    conn.register("_course_text_features", _text_features(reviews))
    try:
        conn.execute(
            "CREATE OR REPLACE TABLE dws_course_text_features AS SELECT * FROM _course_text_features"
        )
    finally:
        conn.unregister("_course_text_features")
    _create_table_from_csv(conn, "dws_course_tags", PROCESSED_DATA_DIR / PROCESSED_FILES["course_tags"])
    statements = _ads_statements()
    conn.execute(statements[0])
    conn.execute(statements[1])
    quality_path = PROCESSED_DATA_DIR / PROCESSED_FILES["data_quality"]
    if not quality_path.exists():
        run_quality_report()
    _create_table_from_csv(conn, "ads_data_quality_report", quality_path)


def build_warehouse() -> None:
    """Validate before opening the DB and publish all tables in one transaction."""
    assert_quality(run_quality_report())
    conn = init_duckdb()
    try:
        conn.execute("BEGIN TRANSACTION")
        build_ods_layer(conn)
        build_dwd_layer(conn)
        build_dws_layer(conn)
        build_ads_layer(conn)
        conn.execute("COMMIT")
        log_step(f"DuckDB warehouse saved to {DUCKDB_PATH}")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    build_warehouse()
