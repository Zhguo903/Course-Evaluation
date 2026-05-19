"""Generate synthetic campus course review data for CourseInsight."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    from src.config import DEPARTMENTS, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from src.utils import log_step, write_csv
except ImportError:  # pragma: no cover
    from config import DEPARTMENTS, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from utils import log_step, write_csv


RANDOM_SEED = 42

COURSE_PREFIX = {
    "Statistics": "STA",
    "Computer Science": "CSC",
    "Data Science": "JSC",
    "Economics": "ECO",
    "Mathematics": "MAT",
    "Biology": "BIO",
    "Psychology": "PSY",
    "Business": "MGT",
}

COURSE_TOPICS = {
    "Statistics": ["Regression", "Statistical Learning", "Inference", "Experimental Design"],
    "Computer Science": ["Databases", "Algorithms", "Software Design", "Machine Learning"],
    "Data Science": ["Data Mining", "Analytics", "Visualization", "Applied Machine Learning"],
    "Economics": ["Microeconomics", "Econometrics", "Markets", "Public Policy"],
    "Mathematics": ["Linear Algebra", "Calculus", "Optimization", "Proofs"],
    "Biology": ["Genetics", "Ecology", "Cell Biology", "Bioinformatics"],
    "Psychology": ["Cognition", "Behavior", "Research Methods", "Social Psychology"],
    "Business": ["Strategy", "Marketing", "Finance", "Operations"],
}

GENERAL_COMMENTS = [
    "The professor explained concepts clearly, but assignments were time consuming.",
    "Useful course for data science students. The project was practical.",
    "The exams were difficult and the workload was heavy.",
    "Light workload and fair grading. Good for students who want a manageable course.",
    "Lots of coding practice with Python and SQL.",
    "Very theoretical and math heavy.",
    "The lectures were interesting and the instructor was helpful.",
    "Some topics were confusing, but the tutorials made the material manageable.",
]

DEPARTMENT_COMMENTS = {
    "Computer Science": [
        "Lots of coding practice with Python, SQL, and debugging assignments.",
        "The final project was practical and useful for software and data roles.",
        "Heavy programming workload, but the labs helped me learn implementation.",
    ],
    "Data Science": [
        "Strong focus on data analysis, visualization, machine learning, and projects.",
        "Useful course for data science students with practical Python notebooks.",
        "The project was realistic and helped connect statistics with business questions.",
    ],
    "Statistics": [
        "Very theoretical with formulas, proofs, and challenging exams.",
        "The professor explained inference clearly, but problem sets were heavy.",
        "Useful statistical thinking, especially for data analysis and modeling.",
    ],
    "Mathematics": [
        "Proof heavy course with abstract theory and difficult exams.",
        "The workload was heavy, but the formulas and concepts became clearer over time.",
        "Very theoretical and math heavy, best for students who like rigorous reasoning.",
    ],
    "Business": [
        "Case studies, presentations, and essays were practical for business students.",
        "Fair grading with useful presentation practice and manageable workload.",
        "The group project and case study discussions were interesting.",
    ],
    "Economics": [
        "The course used case studies, essays, and quantitative market analysis.",
        "Econometrics parts were useful, but exams were difficult.",
        "Good mix of theory, policy discussion, and practical data interpretation.",
    ],
    "Biology": [
        "Labs were helpful and the exams focused on detailed concepts.",
        "Interesting examples, but memorization workload was heavy before exams.",
        "The project connected biological systems with data interpretation.",
    ],
    "Psychology": [
        "Interesting lectures with helpful examples and fair exams.",
        "The essay and research methods project were practical.",
        "Some readings were boring, but the professor was clear and helpful.",
    ],
}


def generate_courses(n_courses: int = 200) -> pd.DataFrame:
    """Generate synthetic course dimension data."""
    rows = []
    used_codes: set[str] = set()
    campuses = ["St. George", "Scarborough", "Mississauga"]

    for course_id in range(1, n_courses + 1):
        department = DEPARTMENTS[(course_id - 1) % len(DEPARTMENTS)]
        prefix = COURSE_PREFIX[department]
        level = random.choice([100, 200, 300, 400])
        number = level + random.randint(0, 99)
        course_code = f"{prefix}{number}"
        while course_code in used_codes:
            number = level + random.randint(0, 99)
            course_code = f"{prefix}{number}"
        used_codes.add(course_code)
        topic = random.choice(COURSE_TOPICS[department])
        rows.append(
            {
                "course_id": course_id,
                "course_code": course_code,
                "course_name": f"{topic} {level // 100}",
                "department": department,
                "course_level": level,
                "credit": random.choice([0.5, 1.0]),
                "prerequisite": "" if level == 100 else f"{prefix}{level - 100 + random.randint(0, 49)}",
                "campus": random.choice(campuses),
            }
        )
    return pd.DataFrame(rows)


def generate_instructors(n_instructors: int = 60) -> pd.DataFrame:
    """Generate synthetic instructor data."""
    first_names = [
        "Alex",
        "Jordan",
        "Taylor",
        "Morgan",
        "Riley",
        "Casey",
        "Avery",
        "Jamie",
        "Quinn",
        "Drew",
    ]
    last_names = [
        "Chen",
        "Patel",
        "Smith",
        "Johnson",
        "Brown",
        "Garcia",
        "Wang",
        "Lee",
        "Martin",
        "Kim",
    ]
    rows = []
    for instructor_id in range(1, n_instructors + 1):
        rows.append(
            {
                "instructor_id": instructor_id,
                "instructor_name": f"Dr. {random.choice(first_names)} {random.choice(last_names)}",
                "department": DEPARTMENTS[(instructor_id - 1) % len(DEPARTMENTS)],
            }
        )
    return pd.DataFrame(rows)


def generate_semesters() -> pd.DataFrame:
    """Generate eight synthetic semester records."""
    rows = []
    semester_id = 1
    for year in [2022, 2023, 2024, 2025]:
        for term, start_month, end_month in [("Spring", 1, 4), ("Fall", 9, 12)]:
            start_date = datetime(year, start_month, 8)
            end_date = datetime(year, end_month, 20)
            rows.append(
                {
                    "semester_id": semester_id,
                    "year": year,
                    "term": term,
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat(),
                }
            )
            semester_id += 1
    return pd.DataFrame(rows)


def generate_offerings(
    courses: pd.DataFrame, instructors: pd.DataFrame, semesters: pd.DataFrame, n_offerings: int = 800
) -> pd.DataFrame:
    """Generate synthetic course offering fact data."""
    rows = []
    instructors_by_dept = {
        dept: instructors[instructors["department"] == dept]["instructor_id"].tolist() for dept in DEPARTMENTS
    }
    for offering_id in range(1, n_offerings + 1):
        course = courses.sample(1, random_state=RANDOM_SEED + offering_id).iloc[0]
        department_instructors = instructors_by_dept[course["department"]]
        capacity = random.choice([40, 60, 80, 100, 120, 150, 200])
        enrolled_count = max(5, min(capacity, int(np.random.normal(capacity * 0.78, capacity * 0.15))))
        rows.append(
            {
                "offering_id": offering_id,
                "course_id": int(course["course_id"]),
                "instructor_id": random.choice(department_instructors),
                "semester_id": int(semesters.sample(1, random_state=RANDOM_SEED + offering_id)["semester_id"].iloc[0]),
                "capacity": capacity,
                "enrolled_count": enrolled_count,
                "delivery_mode": random.choice(["In-person", "Online", "Hybrid"]),
            }
        )
    return pd.DataFrame(rows)


def _review_scores(department: str) -> tuple[float, float, float, float]:
    """Generate correlated review scores by department profile."""
    base_rating = {
        "Computer Science": 3.8,
        "Data Science": 4.0,
        "Statistics": 3.6,
        "Mathematics": 3.4,
        "Business": 3.9,
        "Economics": 3.7,
        "Biology": 3.6,
        "Psychology": 3.8,
    }[department]
    workload_base = {
        "Computer Science": 3.8,
        "Data Science": 3.6,
        "Statistics": 3.7,
        "Mathematics": 4.0,
        "Business": 3.0,
        "Economics": 3.4,
        "Biology": 3.5,
        "Psychology": 2.9,
    }[department]
    rating = np.clip(np.random.normal(base_rating, 0.75), 1, 5)
    difficulty = np.clip(np.random.normal(workload_base, 0.7), 1, 5)
    workload = np.clip(np.random.normal(workload_base, 0.75), 1, 5)
    usefulness = np.clip(np.random.normal((rating + 4.0) / 2, 0.55), 1, 5)
    return round(rating, 1), round(difficulty, 1), round(workload, 1), round(usefulness, 1)


def generate_reviews(
    courses: pd.DataFrame,
    offerings: pd.DataFrame,
    semesters: pd.DataFrame,
    n_reviews: int = 12000,
) -> pd.DataFrame:
    """Generate synthetic course reviews with department-aware text."""
    course_lookup = courses.set_index("course_id").to_dict("index")
    semester_lookup = semesters.set_index("semester_id").to_dict("index")
    rows = []
    sampled_offerings = offerings.sample(n=n_reviews, replace=True, random_state=RANDOM_SEED)
    for review_id, (_, offering) in enumerate(sampled_offerings.iterrows(), start=1):
        course = course_lookup[int(offering["course_id"])]
        department = course["department"]
        rating, difficulty, workload, usefulness = _review_scores(department)
        templates = GENERAL_COMMENTS + DEPARTMENT_COMMENTS[department]
        if workload >= 4.2:
            templates += ["The workload was heavy and assignments were time consuming."]
        if rating >= 4.3:
            templates += ["Great instructor, clear lectures, and helpful feedback."]
        if difficulty >= 4.2:
            templates += ["The exams were hard and required consistent preparation."]
        review_text = random.choice(templates)
        semester = semester_lookup[int(offering["semester_id"])]
        start_date = datetime.fromisoformat(str(semester["start_date"]))
        review_date = start_date + timedelta(days=random.randint(20, 110))
        rows.append(
            {
                "review_id": review_id,
                "course_id": int(offering["course_id"]),
                "instructor_id": int(offering["instructor_id"]),
                "semester_id": int(offering["semester_id"]),
                "rating": rating,
                "difficulty": difficulty,
                "workload": workload,
                "usefulness": usefulness,
                "review_text": review_text,
                "review_date": review_date.date().isoformat(),
            }
        )
    return pd.DataFrame(rows)


def generate_all() -> None:
    """Generate and save all raw CSV files."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    ensure_directories()
    log_step("Generating mock courses, instructors, semesters, offerings, and reviews")
    courses = generate_courses()
    instructors = generate_instructors()
    semesters = generate_semesters()
    offerings = generate_offerings(courses, instructors, semesters)
    reviews = generate_reviews(courses, offerings, semesters)

    write_csv(courses, RAW_DATA_DIR / RAW_FILES["courses"])
    write_csv(instructors, RAW_DATA_DIR / RAW_FILES["instructors"])
    write_csv(semesters, RAW_DATA_DIR / RAW_FILES["semesters"])
    write_csv(offerings, RAW_DATA_DIR / RAW_FILES["offerings"])
    write_csv(reviews, RAW_DATA_DIR / RAW_FILES["reviews"])
    log_step(f"Raw data saved to {RAW_DATA_DIR}")


if __name__ == "__main__":
    generate_all()
