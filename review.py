from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import List

from io_utils.candidates import Candidate, Decision, fetch_candidates, record_decision


def review_candidates(db_path: Path, image: str) -> Decision | None:
    """Interactive review of candidate values for an image."""
    conn = sqlite3.connect(db_path)
    candidates: List[Candidate] = fetch_candidates(conn, image)
    # Ensure candidates are ranked by descending confidence
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    if not candidates:
        print(f"No candidates found for {image}")
        conn.close()
        return None
    for idx, cand in enumerate(candidates):
        print(f"[{idx}] {cand.engine} ({cand.confidence:.2f}): {cand.value}")
    choice = input("Select preferred candidate [0]: ").strip()
    sel = int(choice) if choice else 0
    sel = max(0, min(sel, len(candidates) - 1))
    decision = record_decision(conn, image, candidates[sel])
    print(
        f"Selected '{decision.value}' from {decision.engine} at {decision.decided_at}"
    )
    conn.close()
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description="Review OCR candidates")
    parser.add_argument("db", type=Path, help="Path to candidates database")
    parser.add_argument("image", help="Image filename to review")
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Use Textual interface for candidate review",
    )
    args = parser.parse_args()
    if args.tui:
        from review_tui import review_candidates_tui

        review_candidates_tui(args.db, args.image)
    else:
        review_candidates(args.db, args.image)


if __name__ == "__main__":
    main()
