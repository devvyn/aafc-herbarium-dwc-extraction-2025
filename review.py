from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import List

from io_utils.candidates import Candidate, fetch_candidates, record_decision


def review_candidates(db_path: Path, image: str) -> None:
    """Interactive review of candidate values for an image."""
    conn = sqlite3.connect(db_path)
    candidates: List[Candidate] = fetch_candidates(conn, image)
    if not candidates:
        print(f"No candidates found for {image}")
        conn.close()
        return
    for idx, cand in enumerate(candidates):
        print(f"[{idx}] {cand.engine} ({cand.confidence:.2f}): {cand.value}")
    choice = input("Select preferred candidate [0]: ").strip()
    sel = int(choice) if choice else 0
    sel = max(0, min(sel, len(candidates) - 1))
    record_decision(conn, image, candidates[sel])
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Review OCR candidates")
    parser.add_argument("db", type=Path, help="Path to candidates database")
    parser.add_argument("image", help="Image filename to review")
    args = parser.parse_args()
    review_candidates(args.db, args.image)


if __name__ == "__main__":
    main()
