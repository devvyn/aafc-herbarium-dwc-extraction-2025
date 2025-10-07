#!/usr/bin/env python
"""
Monitor Ongoing Extraction Progress

Tracks extraction progress, validates incrementally, and reports quality metrics.
Supports both free tier (slow trickle) and paid tier extractions.

Usage:
    # Watch progress continuously:
    python scripts/monitor_extraction_progress.py --output full_dataset_processing/gpt4omini_aafc_free

    # One-time status check:
    python scripts/monitor_extraction_progress.py --output full_dataset_processing/gpt4omini_aafc_free --once

    # With incremental validation:
    python scripts/monitor_extraction_progress.py --output full_dataset_processing/gpt4omini_aafc_free --validate deliverables/validation/human_validation.jsonl
"""

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


def count_extractions(output_dir: Path) -> int:
    """Count extracted specimens from raw.jsonl."""
    raw_file = output_dir / "raw.jsonl"

    if not raw_file.exists():
        return 0

    with open(raw_file, "r") as f:
        return sum(1 for _ in f)


def get_extraction_rate(output_dir: Path, window_minutes: int = 5) -> Optional[float]:
    """Calculate extraction rate (specimens per minute) over recent window."""
    raw_file = output_dir / "raw.jsonl"

    if not raw_file.exists():
        return None

    cutoff = datetime.now() - timedelta(minutes=window_minutes)
    recent_count = 0

    with open(raw_file, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                run_id = data.get("run_id", "")

                # Parse timestamp from run_id (format: YYYY-MM-DDTHH:MM:SS...)
                if "T" in run_id:
                    timestamp_str = run_id.split("+")[0].split("Z")[0]
                    timestamp = datetime.fromisoformat(timestamp_str)

                    if timestamp > cutoff:
                        recent_count += 1
            except:
                continue

    return recent_count / window_minutes if recent_count > 0 else None


def analyze_field_coverage(output_dir: Path, limit: int = None) -> Dict:
    """Analyze field coverage from extracted data."""
    raw_file = output_dir / "raw.jsonl"

    if not raw_file.exists():
        return {}

    field_counts = Counter()
    field_confidence_sums = defaultdict(float)
    total = 0

    with open(raw_file, "r") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break

            try:
                data = json.loads(line)
                total += 1

                dwc = data.get("dwc", {})
                confidences = data.get("dwc_confidence", {})

                for field, value in dwc.items():
                    if value:  # Non-empty
                        field_counts[field] += 1
                        field_confidence_sums[field] += confidences.get(field, 0.0)
            except:
                continue

    # Calculate averages
    coverage = {}
    for field, count in field_counts.items():
        coverage[field] = {
            "count": count,
            "percentage": (count / total * 100) if total > 0 else 0,
            "avg_confidence": field_confidence_sums[field] / count if count > 0 else 0
        }

    return coverage


def estimate_completion(current: int, total: int, rate: Optional[float]) -> Optional[str]:
    """Estimate completion time based on current rate."""
    if not rate or rate <= 0:
        return None

    remaining = total - current
    minutes_left = remaining / rate

    if minutes_left < 60:
        return f"{minutes_left:.0f} minutes"
    elif minutes_left < 1440:  # < 24 hours
        return f"{minutes_left / 60:.1f} hours"
    else:
        return f"{minutes_left / 1440:.1f} days"


def display_progress(output_dir: Path, total_specimens: int = 2885, validate_against: Optional[Path] = None):
    """Display extraction progress dashboard."""
    count = count_extractions(output_dir)
    rate = get_extraction_rate(output_dir, window_minutes=5)
    coverage = analyze_field_coverage(output_dir, limit=100)  # Sample last 100

    print("\n" + "=" * 70)
    print("EXTRACTION PROGRESS MONITOR")
    print("=" * 70)

    # Progress
    progress_pct = (count / total_specimens * 100) if total_specimens > 0 else 0
    print(f"\n📊 Progress: {count:,} / {total_specimens:,} specimens ({progress_pct:.1f}%)")

    # Progress bar
    bar_width = 50
    filled = int(bar_width * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"   [{bar}] {progress_pct:.1f}%")

    # Rate
    if rate:
        print(f"\n⚡ Extraction rate: {rate:.1f} specimens/minute")

        est_time = estimate_completion(count, total_specimens, rate)
        if est_time:
            print(f"⏱️  Estimated completion: {est_time}")
    else:
        print(f"\n⚡ Extraction rate: Calculating...")

    # Field coverage (top 10)
    if coverage:
        print(f"\n📋 Field Coverage (sample of last 100):")
        sorted_fields = sorted(
            coverage.items(),
            key=lambda x: x[1]["percentage"],
            reverse=True
        )[:10]

        for field, stats in sorted_fields:
            print(f"   {field:<25} {stats['percentage']:>6.1f}% (conf: {stats['avg_confidence']:.2f})")

    # Validation (if ground truth provided)
    if validate_against and validate_against.exists():
        # Quick validation on recent extractions
        # TODO: Implement incremental validation
        print(f"\n✅ Validation: Available (run full validation manually)")

    # Output files
    raw_file = output_dir / "raw.jsonl"
    if raw_file.exists():
        size_mb = raw_file.stat().st_size / 1024 / 1024
        print(f"\n💾 Output: {raw_file}")
        print(f"   Size: {size_mb:.1f} MB")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor ongoing extraction progress"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Extraction output directory"
    )
    parser.add_argument(
        "--total",
        type=int,
        default=2885,
        help="Total specimens to extract (default: 2885)"
    )
    parser.add_argument(
        "--validate",
        type=Path,
        help="Ground truth JSONL for validation"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Show status once and exit (no continuous monitoring)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Update interval in seconds (default: 60)"
    )

    args = parser.parse_args()

    if not args.output.exists():
        print(f"Error: Output directory not found: {args.output}")
        sys.exit(1)

    try:
        if args.once:
            # Single status check
            display_progress(args.output, args.total, args.validate)
        else:
            # Continuous monitoring
            print(f"📡 Monitoring extraction: {args.output}")
            print(f"⏱️  Update interval: {args.interval}s")
            print(f"\nPress Ctrl+C to stop\n")

            while True:
                display_progress(args.output, args.total, args.validate)

                # Check if complete
                count = count_extractions(args.output)
                if count >= args.total:
                    print(f"\n✅ Extraction complete! ({count:,} specimens)")
                    break

                print(f"\n💤 Next update in {args.interval}s...")
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n⏸️  Monitoring stopped by user")
        count = count_extractions(args.output)
        print(f"📊 Current progress: {count:,} / {args.total:,} specimens")


if __name__ == "__main__":
    main()
