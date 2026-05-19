"""One-command local pipeline runner for CourseInsight."""

from src.data_quality import main as run_data_quality
from src.etl import run_etl
from src.generate_mock_data import generate_all
from src.nlp_tags import generate_course_tags
from src.utils import log_step
from src.warehouse import build_warehouse


def main() -> None:
    """Run the complete local CourseInsight data pipeline."""
    log_step("Starting CourseInsight pipeline")
    generate_all()
    run_etl()
    generate_course_tags()
    run_data_quality()
    build_warehouse()
    log_step("Pipeline completed successfully")


if __name__ == "__main__":
    main()
