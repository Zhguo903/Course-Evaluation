"""Load official course metadata and generate explicitly synthetic demo reviews."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    from src.catalog import load_catalog
    from src.config import DEPARTMENTS, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from src.utils import log_step, write_csv
except ImportError:  # pragma: no cover
    from catalog import load_catalog
    from config import DEPARTMENTS, RAW_DATA_DIR, RAW_FILES, ensure_directories
    from utils import log_step, write_csv


RANDOM_SEED = 42


def generate_courses(n_courses: int = 200) -> pd.DataFrame:
    """Load an offline official UofT three-campus course catalog snapshot.

    The metadata is official; related reviews, instructors, and offerings are
    synthetic examples. A subset is supported without fabricating extra courses.
    """
    records = load_catalog()
    if isinstance(n_courses, bool) or not isinstance(n_courses, int) or not 0 <= n_courses <= len(records):
        raise ValueError(f"n_courses must be an integer between 0 and {len(records)}")
    courses = pd.DataFrame(records).iloc[:n_courses].copy()
    if "course_id" not in courses:
        courses.insert(0, "course_id", range(1, n_courses + 1))
    return courses.reset_index(drop=True)


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
        # Round-robin coverage gives every course offerings before adding repeats.
        course = courses.iloc[(offering_id - 1) % len(courses)]
        department_instructors = instructors_by_dept[course["department"]]
        capacity = random.choice([40, 60, 80, 100, 120, 150, 200])
        enrolled_count = max(5, min(capacity, int(np.random.normal(capacity * 0.78, capacity * 0.15))))
        rows.append(
            {
                "offering_id": offering_id,
                "course_id": int(course["course_id"]),
                "instructor_id": random.choice(department_instructors),
                "semester_id": int(
                    semesters.iloc[
                        ((offering_id - 1) // len(courses) + int(course["course_id"])) % len(semesters)
                    ]["semester_id"]
                ),
                "capacity": capacity,
                "enrolled_count": enrolled_count,
                "delivery_mode": random.choice(["In-person", "Online", "Hybrid"]),
            }
        )
    return pd.DataFrame(rows)


def _course_profile(course: dict) -> tuple[float, float, float, float, bool]:
    """Stable course-specific tendencies independent of individual reviewers."""
    rng = np.random.default_rng(RANDOM_SEED + int(course["course_id"]))
    level_effect = (int(course["course_level"]) - 250) / 250
    practical = bool(
        rng.random() < (0.75 if course["department"] in {"Computer Science", "Biology", "Economics"} else 0.4)
    )
    difficulty = float(np.clip(3.0 + level_effect + rng.normal(0, 0.65), 1.5, 4.7))
    workload = float(np.clip(difficulty * 0.6 + 1.2 + rng.normal(0, 0.6), 1.5, 4.7))
    rating = float(np.clip(3.8 + rng.normal(0, 0.55) - 0.1 * (workload - 3), 2.0, 4.8))
    usefulness = float(np.clip(3.6 + 0.4 * practical + rng.normal(0, 0.5), 2.0, 4.8))
    return rating, difficulty, workload, usefulness, practical


def _review_scores(course: dict) -> tuple[float, float, float, float]:
    """Individual responses fluctuate around a stable course profile."""
    profile = _course_profile(course)
    return tuple(round(float(np.clip(np.random.normal(base, 0.45), 1, 5)), 1) for base in profile[:4])


def _review_text(course: dict, scores: tuple[float, float, float, float]) -> str:
    rating, difficulty, workload, usefulness = scores
    topic = str(course["course_name"])
    practical = _course_profile(course)[4]
    workload_text = (
        "Heavy workload with time consuming assignments"
        if workload >= 3.8
        else "Light workload with manageable assignments"
        if workload <= 2.6
        else "Moderate workload with regular assignments"
    )
    difficulty_text = (
        "Difficult exams required consistent preparation"
        if difficulty >= 3.8
        else "Accessible concepts and fair exams"
        if difficulty <= 2.6
        else "Exams covered the lectures and required practice"
    )
    teaching_text = (
        "Clear lectures and helpful feedback"
        if rating >= 3.8
        else "Some explanations were confusing"
        if rating <= 2.8
        else "The tutorials supported the lectures"
    )
    format_text = (
        "Practical projects and hands-on exercises"
        if practical
        else "Theoretical concepts, readings, and analytical reasoning"
    )
    value_text = (
        "Useful skills for future study and careers"
        if usefulness >= 3.8
        else "More specialized material with limited immediate application"
    )
    # Include the actual subject in every review; unrelated generic coding/math
    # claims no longer leak into courses from other disciplines.
    return f"{topic} focused on {topic.lower()}. {format_text}. {workload_text}. {difficulty_text}. {teaching_text}. {value_text}."


def generate_reviews(
    courses: pd.DataFrame,
    offerings: pd.DataFrame,
    semesters: pd.DataFrame,
    n_reviews: int = 12000,
) -> pd.DataFrame:
    """Generate coherent subject-specific reviews from stable course profiles."""
    course_lookup = courses.set_index("course_id", drop=False).to_dict("index")
    semester_lookup = semesters.set_index("semester_id").to_dict("index")
    rows = []
    sampled_offerings = offerings.sample(n=n_reviews, replace=True, random_state=RANDOM_SEED)
    for review_id, (_, offering) in enumerate(sampled_offerings.iterrows(), start=1):
        course = course_lookup[int(offering["course_id"])]
        rating, difficulty, workload, usefulness = _review_scores(course)
        review_text = _review_text(course, (rating, difficulty, workload, usefulness))
        semester = semester_lookup[int(offering["semester_id"])]
        start_date = datetime.fromisoformat(str(semester["start_date"]))
        end_date = datetime.fromisoformat(str(semester["end_date"]))
        review_date = start_date + timedelta(days=random.randint(20, (end_date - start_date).days))
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
                "data_source": "synthetic_community_inspired",
                "source_note": "Synthetic examples inspired by maintainer-described community discussion themes; no original group messages or real review records are ingested.",
            }
        )
    return pd.DataFrame(rows)


def generate_all() -> None:
    """Generate and save all raw CSV files."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    ensure_directories()
    log_step(
        "Loading official UofT course metadata; generating synthetic instructors, offerings, and reviews"
    )
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
