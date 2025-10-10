#!/usr/bin/env python
"""
Batch Monitor with Desktop Notifications

Monitors batches and sends desktop notifications on completion.

Usage:
    # Monitor specific batches until complete
    python scripts/batch_notify.py --batch-id batch_123

    # Auto-discover and monitor all active batches
    python scripts/batch_notify.py

    # Custom check interval
    python scripts/batch_notify.py --interval 60

    # Disable notifications (polling only)
    python scripts/batch_notify.py --no-notify
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from batch_monitor import BatchMonitorEngine
from batch_monitor.notifications import NotificationManager


def main():
    parser = argparse.ArgumentParser(description="Monitor batches with desktop notifications")
    parser.add_argument(
        "--batch-id",
        action="append",
        dest="batch_ids",
        help="Batch ID to monitor (can specify multiple)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable desktop notifications",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("batch_monitor_history.jsonl"),
        help="Path to history file",
    )
    parser.add_argument(
        "--progress-notify",
        action="store_true",
        help="Notify at progress milestones (50%%, 75%%)",
    )

    args = parser.parse_args()

    # Initialize
    engine = BatchMonitorEngine(history_file=args.history)
    notifier = NotificationManager(enabled=not args.no_notify)

    # Get batch IDs
    if args.batch_ids:
        batch_ids = args.batch_ids
        print(f"🔔 Monitoring {len(batch_ids)} specified batches...")
    else:
        batch_ids = engine.get_active_batches()
        if not batch_ids:
            print("❌ No active batches found")
            return
        print(f"🔔 Monitoring {len(batch_ids)} auto-discovered batches...")

    # Track notification state
    progress_notified = {bid: None for bid in batch_ids}
    completed_batches = set()

    try:
        while True:
            # Fetch statuses
            statuses = engine.fetch_multiple(batch_ids)

            # Check each batch
            for status in statuses:
                if status.batch_id in completed_batches:
                    continue

                # Check for completion
                if status.is_complete:
                    print(f"\n{status.status_emoji} {status.batch_id[:24]} - {status.status}")
                    notifier.notify_completion(status)
                    completed_batches.add(status.batch_id)
                else:
                    # Progress notification
                    if args.progress_notify:
                        for threshold in [0.5, 0.75]:
                            progress_notified[status.batch_id] = notifier.notify_progress(
                                status, threshold, progress_notified[status.batch_id]
                            )

                    # Print current status
                    print(
                        f"{status.status_emoji} {status.batch_id[:24]} - "
                        f"{status.progress.completed}/{status.progress.total} "
                        f"({status.progress.completion_percentage:.0f}%) - "
                        f"{status.timing.elapsed_minutes:.1f} min"
                    )

            # Check if all complete
            if len(completed_batches) == len(batch_ids):
                print("\n✅ All batches complete!")
                break

            # Wait before next check
            print(f"\n⏳ Next check in {args.interval} seconds...\n")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n⚠️ Monitoring stopped by user")


if __name__ == "__main__":
    main()
