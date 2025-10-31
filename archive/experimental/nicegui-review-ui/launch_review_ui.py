#!/usr/bin/env python3
"""
Simple launcher for NiceGUI review interface.
Avoids Typer/CLI conflicts by being a standalone script.
"""

from pathlib import Path
from nicegui import ui
import sys
import logging

# Configure logging to show INFO and above messages
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from review.nicegui_app import SpecimenReviewUI  # noqa: E402

# Configuration - edit these defaults as needed
EXTRACTION_DIR = Path("deliverables/v1.0_vision_baseline")
PORT = 5003
HOST = "127.0.0.1"
ENABLE_GBIF = False

# Default filter settings (edit to your preference)
# Status options: None (all), 'PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED'
# Priority options: None (all), 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'
DEFAULT_STATUS_FILTER = "PENDING"  # Show only pending by default
DEFAULT_PRIORITY_FILTER = None  # Show all priorities
DEFAULT_FLAGGED_ONLY = False  # Don't filter by flagged

if __name__ == "__main__":
    print("=" * 70)
    print("SPECIMEN REVIEW INTERFACE (NiceGUI)")
    print("=" * 70)
    print(f"Extraction directory: {EXTRACTION_DIR}")
    print(f"GBIF validation: {'enabled' if ENABLE_GBIF else 'disabled'}")
    print(f"Server: http://{HOST}:{PORT}")
    print()

    # Verify raw.jsonl exists
    if not (EXTRACTION_DIR / "raw.jsonl").exists():
        print(f"❌ No raw.jsonl found in {EXTRACTION_DIR}")
        sys.exit(1)

    # Create and launch UI with default filters
    from review.engine import ReviewStatus, ReviewPriority

    # Convert string filter values to enums
    initial_status = None
    if DEFAULT_STATUS_FILTER:
        try:
            initial_status = ReviewStatus[DEFAULT_STATUS_FILTER]
        except KeyError:
            print(f"⚠️  Invalid status filter: {DEFAULT_STATUS_FILTER}")

    initial_priority = None
    if DEFAULT_PRIORITY_FILTER:
        try:
            initial_priority = ReviewPriority[DEFAULT_PRIORITY_FILTER]
        except KeyError:
            print(f"⚠️  Invalid priority filter: {DEFAULT_PRIORITY_FILTER}")

    review_ui = SpecimenReviewUI(
        EXTRACTION_DIR,
        enable_gbif=ENABLE_GBIF,
        initial_status=initial_status,
        initial_priority=initial_priority,
        initial_flagged=DEFAULT_FLAGGED_ONLY,
    )
    review_ui.build_ui()

    print("✅ Review system ready")
    print(f"🌐 Open: http://{HOST}:{PORT}")
    print("⌨️  Keyboard shortcuts:")
    print("   j/k (next/prev), a (approve), x (reject), f (flag)")
    print("   r/l (rotate right/left), 0 (reset rotation)")
    print()

    ui.run(host=HOST, port=PORT, title="Specimen Review - AAFC Herbarium", reload=False, show=False)
