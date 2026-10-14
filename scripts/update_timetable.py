#!/usr/bin/env python3
"""Refresh the public three-campus timetable snapshot, retaining it on failure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.timetable import REFERENCE_DIR, fetch_timetable_snapshot, write_timetable_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--throttle", type=float, default=0.35)
    args = parser.parse_args()
    if args.timeout <= 0 or args.throttle < 0:
        parser.error("timeout must be positive and throttle must be non-negative")
    try:
        offerings, manifest = fetch_timetable_snapshot(timeout=args.timeout, throttle=args.throttle)
        write_timetable_snapshot(offerings, manifest, args.output_dir)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"Timetable refresh failed; previous snapshots retained: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {len(offerings):,} verified offerings for {len(manifest['coverage'])} campus/session pairs")
    for row in manifest["division_totals"]:
        print(f"  {row['campus']}: {row['official_total']:,} offerings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
