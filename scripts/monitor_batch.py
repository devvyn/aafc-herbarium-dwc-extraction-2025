#!/usr/bin/env python
"""
Monitor OpenAI Batch API Job

Monitors batch job progress and auto-downloads results when complete.

Usage:
    python scripts/monitor_batch.py --batch-id batch_abc123

    # Auto-monitor from saved batch ID file:
    python scripts/monitor_batch.py --batch-id-file full_dataset_processing/gpt4omini_batch/batch_id.txt

    # One-time status check (no polling):
    python scripts/monitor_batch.py --batch-id batch_abc123 --no-poll
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI SDK not installed")
    print("Install with: uv add openai")
    sys.exit(1)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    else:
        return f"{seconds/3600:.1f}h"


def print_status(batch: dict):
    """Print batch status in formatted table."""
    print("\n" + "=" * 70)
    print(f"BATCH STATUS: {batch.status.upper()}")
    print("=" * 70)

    print(f"\n📋 Batch ID: {batch.id}")
    print(f"📊 Status: {batch.status}")

    if batch.request_counts:
        total = batch.request_counts.total
        completed = batch.request_counts.completed
        failed = batch.request_counts.failed

        progress_pct = (completed / total * 100) if total > 0 else 0

        print(f"\n📈 Progress:")
        print(f"   Total:     {total:,}")
        print(f"   Completed: {completed:,} ({progress_pct:.1f}%)")
        print(f"   Failed:    {failed:,}")

        # Progress bar
        bar_width = 50
        filled = int(bar_width * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"   [{bar}] {progress_pct:.1f}%")

    # Timestamps
    print(f"\n⏱️  Timing:")
    if batch.created_at:
        created = datetime.fromtimestamp(batch.created_at)
        print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")

    if batch.in_progress_at:
        started = datetime.fromtimestamp(batch.in_progress_at)
        print(f"   Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")

        elapsed = datetime.now() - started
        print(f"   Elapsed: {format_duration(elapsed.total_seconds())}")

    if batch.expires_at:
        expires = datetime.fromtimestamp(batch.expires_at)
        print(f"   Expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")

        time_left = expires - datetime.now()
        if time_left.total_seconds() > 0:
            print(f"   Time remaining: {format_duration(time_left.total_seconds())}")

    if batch.completed_at:
        completed_time = datetime.fromtimestamp(batch.completed_at)
        print(f"   Completed: {completed_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Output files
    if batch.output_file_id:
        print(f"\n📄 Output file ID: {batch.output_file_id}")

    if batch.error_file_id:
        print(f"⚠️  Error file ID: {batch.error_file_id}")

    print("=" * 70)


def download_results(batch: dict, output_dir: Path):
    """Download batch results when complete.

    Args:
        batch: Batch object dict
        output_dir: Directory to save results
    """
    if batch.status != "completed":
        print(f"⚠️  Batch not complete yet (status: {batch.status})")
        return

    if not batch.output_file_id:
        print(f"⚠️  No output file available")
        return

    client = OpenAI()

    print(f"\n📥 Downloading results...")
    output_path = output_dir / "batch_output.jsonl"

    try:
        # Download output file
        content = client.files.content(batch.output_file_id)

        with open(output_path, "wb") as f:
            f.write(content.read())

        print(f"✅ Results downloaded:")
        print(f"   {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

        # Count lines
        with open(output_path, "r") as f:
            line_count = sum(1 for _ in f)

        print(f"   Responses: {line_count:,}")

        # Download error file if present
        if batch.error_file_id:
            error_path = output_dir / "batch_errors.jsonl"
            error_content = client.files.content(batch.error_file_id)

            with open(error_path, "wb") as f:
                f.write(error_content.read())

            print(f"\n⚠️  Errors downloaded:")
            print(f"   {error_path}")

        # Next steps
        print(f"\n📍 Next step:")
        print(f"   python scripts/process_batch_results.py --batch-id {batch.id}")

    except Exception as e:
        print(f"\n❌ Error downloading results: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor OpenAI Batch API job progress"
    )

    # Either batch ID directly or from file
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument(
        "--batch-id",
        type=str,
        help="Batch job ID"
    )
    id_group.add_argument(
        "--batch-id-file",
        type=Path,
        help="File containing batch ID"
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=300,
        help="Polling interval in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--no-poll",
        action="store_true",
        help="Check status once without polling"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for results (default: same as batch-id-file)"
    )

    args = parser.parse_args()

    # Get batch ID
    if args.batch_id_file:
        if not args.batch_id_file.exists():
            print(f"Error: Batch ID file not found: {args.batch_id_file}")
            sys.exit(1)

        batch_id = args.batch_id_file.read_text().strip()
        output_dir = args.output_dir or args.batch_id_file.parent
    else:
        batch_id = args.batch_id
        output_dir = args.output_dir or Path(".")

    client = OpenAI()

    print("=" * 70)
    print("OPENAI BATCH MONITORING")
    print("=" * 70)

    try:
        if args.no_poll:
            # Single status check
            batch = client.batches.retrieve(batch_id)
            print_status(batch)

            if batch.status == "completed":
                download_results(batch, output_dir)

        else:
            # Poll until complete
            print(f"📡 Monitoring batch: {batch_id}")
            print(f"⏱️  Poll interval: {args.poll_interval}s ({args.poll_interval/60:.0f} minutes)")
            print(f"\nPress Ctrl+C to stop monitoring\n")

            while True:
                batch = client.batches.retrieve(batch_id)
                print_status(batch)

                # Check if complete
                if batch.status in ["completed", "failed", "expired", "cancelled"]:
                    if batch.status == "completed":
                        download_results(batch, output_dir)
                        print(f"\n✅ Batch completed successfully!")
                    else:
                        print(f"\n❌ Batch ended with status: {batch.status}")

                    break

                # Wait before next check
                print(f"\n💤 Next check in {args.poll_interval}s...")
                time.sleep(args.poll_interval)

    except KeyboardInterrupt:
        print(f"\n\n⏸️  Monitoring stopped by user")
        print(f"📋 Batch ID: {batch_id}")
        print(f"\nResume monitoring with:")
        print(f"   python scripts/monitor_batch.py --batch-id {batch_id}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
