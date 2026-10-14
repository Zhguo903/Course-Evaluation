"""Build CourseInsight from versioned official catalogue and timetable snapshots."""

from __future__ import annotations

import argparse

from src.warehouse import build_warehouse


def main() -> None:
    quality = build_warehouse()
    print(f"Published official course finder database; {len(quality)} checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    main()
