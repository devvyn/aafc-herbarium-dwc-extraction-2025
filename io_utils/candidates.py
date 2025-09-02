from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import List, Optional

from pydantic import BaseModel


class Candidate(BaseModel):
    """Represents a candidate value produced by an OCR engine."""

    value: str
    engine: str
    confidence: float
    error: bool = False


class Decision(BaseModel):
    """Represents a reviewer-selected value."""

    value: str
    engine: str
    run_id: str | None
    decided_at: str


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
            confidence REAL,
            error INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            run_id TEXT,
            image TEXT,
            value TEXT,
            engine TEXT,
            decided_at TEXT
        )
        """
    )
    try:
        conn.execute("ALTER TABLE candidates ADD COLUMN error INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    return conn


def insert_candidate(
    conn: sqlite3.Connection,
    run_id: str,
    image: str,
    candidate: Candidate,
) -> None:
    """Persist a candidate record to the database."""
    conn.execute(
        "INSERT INTO candidates (run_id, image, value, engine, confidence, error) VALUES (?, ?, ?, ?, ?, ?)",
        (
            run_id,
            image,
            candidate.value,
            candidate.engine,
            candidate.confidence,
            int(candidate.error),
        ),
    )
    conn.commit()


def fetch_candidates(conn: sqlite3.Connection, image: str) -> List[Candidate]:
    """Retrieve all candidate values for an image sorted by confidence."""
    rows = conn.execute(
        "SELECT value, engine, confidence, error FROM candidates WHERE image = ? ORDER BY confidence DESC",
        (image,),
    ).fetchall()
    return [
        Candidate(value=row[0], engine=row[1], confidence=row[2], error=bool(row[3]))
        for row in rows
    ]


def best_candidate(conn: sqlite3.Connection, image: str) -> Optional[Candidate]:
    """Return the highest-confidence candidate for an image if available."""
    rows = fetch_candidates(conn, image)
    return rows[0] if rows else None


def record_decision(
    conn: sqlite3.Connection, image: str, candidate: Candidate
) -> Decision:
    """Persist a reviewer decision and return the stored record."""
    run_row = conn.execute(
        "SELECT run_id FROM candidates WHERE image = ? AND value = ? AND engine = ? ORDER BY confidence DESC LIMIT 1",
        (image, candidate.value, candidate.engine),
    ).fetchone()
    run_id = run_row[0] if run_row else None
    decided_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO decisions (run_id, image, value, engine, decided_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, image, candidate.value, candidate.engine, decided_at),
    )
    conn.commit()
    return Decision(
        value=candidate.value,
        engine=candidate.engine,
        run_id=run_id,
        decided_at=decided_at,
    )


def fetch_decision(conn: sqlite3.Connection, image: str) -> Optional[Decision]:
    """Retrieve the stored decision for an image if present."""
    row = conn.execute(
        "SELECT value, engine, run_id, decided_at FROM decisions WHERE image = ? ORDER BY decided_at DESC LIMIT 1",
        (image,),
    ).fetchone()
    if not row:
        return None
    return Decision(value=row[0], engine=row[1], run_id=row[2], decided_at=row[3])


def import_decisions(
    dest: sqlite3.Connection, src: sqlite3.Connection
) -> None:
    """Merge decisions from ``src`` into ``dest`` with duplicate checks."""
    rows = src.execute(
        "SELECT run_id, image, value, engine, decided_at FROM decisions",
    ).fetchall()
    latest: dict[str, tuple[str | None, str, str, str, str]] = {}
    for run_id, image, value, engine, decided_at in rows:
        current = latest.get(image)
        if not current or decided_at > current[4]:
            latest[image] = (run_id, image, value, engine, decided_at)

    for run_id, image, value, engine, decided_at in latest.values():
        exists = dest.execute(
            "SELECT 1 FROM decisions WHERE image = ?",
            (image,),
        ).fetchone()
        if exists:
            raise ValueError(f"Decision for {image} already exists")
        dest.execute(
            "INSERT INTO decisions (run_id, image, value, engine, decided_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, image, value, engine, decided_at),
        )
    dest.commit()


__all__ = [
    "Candidate",
    "init_db",
    "insert_candidate",
    "fetch_candidates",
    "best_candidate",
    "record_decision",
    "fetch_decision",
    "import_decisions",
    "Decision",
]
