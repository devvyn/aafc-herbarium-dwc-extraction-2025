from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import List, Optional

from pydantic import BaseModel


class Candidate(BaseModel):
    """Represents a candidate value produced by an OCR engine."""

    value: str
    engine: str
    confidence: float


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialise the candidate SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            run_id TEXT,
            image TEXT,
            value TEXT,
            engine TEXT,
            confidence REAL
        )
        """
    )
    return conn


def insert_candidate(
    conn: sqlite3.Connection,
    run_id: str,
    image: str,
    candidate: Candidate,
) -> None:
    """Persist a candidate record to the database."""
    conn.execute(
        "INSERT INTO candidates (run_id, image, value, engine, confidence) VALUES (?, ?, ?, ?, ?)",
        (run_id, image, candidate.value, candidate.engine, candidate.confidence),
    )
    conn.commit()


def fetch_candidates(conn: sqlite3.Connection, image: str) -> List[Candidate]:
    """Retrieve all candidate values for an image sorted by confidence."""
    rows = conn.execute(
        "SELECT value, engine, confidence FROM candidates WHERE image = ? ORDER BY confidence DESC",
        (image,),
    ).fetchall()
    return [Candidate(value=row[0], engine=row[1], confidence=row[2]) for row in rows]


def best_candidate(conn: sqlite3.Connection, image: str) -> Optional[Candidate]:
    """Return the highest-confidence candidate for an image if available."""
    rows = fetch_candidates(conn, image)
    return rows[0] if rows else None


__all__ = [
    "Candidate",
    "init_db",
    "insert_candidate",
    "fetch_candidates",
    "best_candidate",
]
