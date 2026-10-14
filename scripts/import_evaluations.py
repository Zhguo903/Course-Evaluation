#!/usr/bin/env python3
"""Import explicit public historical evaluation CSVs; default runs stay offline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.catalog import load_catalog
from src.evaluations import REFERENCE_DIR, fetch_evaluation_sources, import_evaluation_sources, write_evaluation_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-dir", type=Path, help="Directory containing the three public source CSV files")
    source.add_argument("--fetch", action="store_true", help="Explicitly download the three public CSVs to temporary storage")
    parser.add_argument("--output-dir", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    try:
        catalogue = load_catalog()
        if args.fetch:
            with TemporaryDirectory(prefix="course-evaluations-") as directory:
                fetch_evaluation_sources(directory, timeout=args.timeout)
                records, manifest = import_evaluation_sources(directory, catalogue)
        else:
            records, manifest = import_evaluation_sources(args.source_dir, catalogue)
        write_evaluation_snapshot(records, manifest, args.output_dir)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Evaluation import failed; previous snapshots retained: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {len(records):,} historical numeric reports: {manifest['matched_record_count']:,} matched records, "
          f"{manifest['matched_current_course_count']:,} current courses, {manifest['unmatched_record_count']:,} unmatched records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
