#!/usr/bin/env python3
"""Validate curated reviews/resources and historical evaluation snapshots offline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluations import load_evaluation_snapshot
from src.support import load_support_snapshot, write_support_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="Explicitly renew curated metadata hashes after source verification and edits",
    )
    args = parser.parse_args()
    try:
        if args.refresh_manifest:
            write_support_manifest()
        support, _ = load_support_snapshot()
        evaluations, manifest = load_evaluation_snapshot()
    except (OSError, ValueError, KeyError) as error:
        print(f"Support validation failed: {error}", file=sys.stderr)
        return 1
    print("Verified " + ", ".join(f"{key}: {len(rows)}" for key, rows in support.items()))
    print(
        f"Historical evaluations: {len(evaluations):,}; matched current courses: "
        f"{manifest.get('matched_current_course_count', 0):,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
