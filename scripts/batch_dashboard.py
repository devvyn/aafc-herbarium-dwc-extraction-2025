#!/usr/bin/env python
"""
Batch Monitoring Dashboard (Terminal UI)

Live monitoring of OpenAI Batch API jobs with auto-updating display.

Usage:
    # Auto-discover and monitor all active batches
    python scripts/batch_dashboard.py

    # Monitor specific batches
    python scripts/batch_dashboard.py --batch-id batch_123 --batch-id batch_456

    # Custom refresh interval
    python scripts/batch_dashboard.py --refresh 60
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from batch_monitor import BatchMonitorEngine
from batch_monitor.terminal import BatchDashboard


def main():
    parser = argparse.ArgumentParser(description="Live terminal dashboard for batch monitoring")
    parser.add_argument(
        "--batch-id",
        action="append",
        dest="batch_ids",
        help="Batch ID to monitor (can specify multiple)",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("batch_monitor_history.jsonl"),
        help="Path to history file",
    )
    parser.add_argument(
        "--no-auto-exit",
        action="store_true",
        help="Continue monitoring after all batches complete",
    )

    args = parser.parse_args()

    try:
        # Initialize engine
        engine = BatchMonitorEngine(history_file=args.history)

        # Initialize dashboard
        dashboard = BatchDashboard(engine)

        # Monitor batches
        if args.batch_ids:
            print(f"Monitoring {len(args.batch_ids)} specified batches...")
            dashboard.monitor(
                args.batch_ids,
                refresh_interval=args.refresh,
                auto_exit=not args.no_auto_exit,
            )
        else:
            # Auto-discover active batches
            dashboard.monitor_auto(refresh_interval=args.refresh)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
