#!/usr/bin/env python3
"""
Unified Web Monitor Launcher

Launches Flask web dashboard with unified design matching TUI.

Usage:
    python scripts/web_monitor.py --port 5000
    python scripts/web_monitor.py --port 8080 --host 0.0.0.0  # Network accessible
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction_monitor.web_app import create_app


def main():
    parser = argparse.ArgumentParser(description="Launch unified web monitor")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on (default: 5000)")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    app = create_app()

    print("=" * 70)
    print("🌿 HERBARIUM EXTRACTION WEB MONITOR")
    print("=" * 70)
    print(f"Running on: http://{args.host}:{args.port}")
    print()
    print("Features:")
    print("  • Unified design matching TUI layout")
    print("  • Real-time SSE updates (5-second refresh)")
    print("  • Stats cards + Hero progress + Event stream + Field quality")
    print("  • Auto-detects latest extraction run")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
