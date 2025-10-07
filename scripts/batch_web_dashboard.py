#!/usr/bin/env python
"""
Batch Monitoring Web Dashboard

Launch browser-based monitoring interface with real-time updates.

Usage:
    # Auto-discover and monitor all active batches
    python scripts/batch_web_dashboard.py

    # Custom port
    python scripts/batch_web_dashboard.py --port 8080

    # Custom refresh interval
    python scripts/batch_web_dashboard.py --refresh 60
"""

import argparse
import sys
import webbrowser
from pathlib import Path
from threading import Timer

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from batch_monitor.web import create_app


def open_browser(url: str, delay: float = 1.5):
    """Open browser after a delay to ensure server is ready."""

    def _open():
        webbrowser.open(url)

    Timer(delay, _open).start()


def main():
    parser = argparse.ArgumentParser(
        description="Web dashboard for batch monitoring"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run server on (default: 5000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("batch_monitor_history.jsonl"),
        help="Path to history file",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)",
    )

    args = parser.parse_args()

    # Create Flask app
    app = create_app(history_file=args.history)

    # Open browser automatically
    if not args.no_browser:
        url = f"http://{args.host}:{args.port}/?refresh={args.refresh}"
        print(f"\n🌐 Opening dashboard at {url}\n")
        open_browser(url)
    else:
        print(f"\n🌐 Dashboard running at http://{args.host}:{args.port}\n")

    # Run server
    try:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")


if __name__ == "__main__":
    main()
