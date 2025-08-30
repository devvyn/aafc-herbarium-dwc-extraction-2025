from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

from pydantic import BaseModel

from .candidates import init_db as init_candidate_db


class Specimen(BaseModel):
    """Represents a herbarium specimen and associated image."""

    specimen_id: str
    image: str


class FinalValue(BaseModel):
    """Represents the final selected value for a field."""

    specimen_id: str
    field: str
    value: str
    module: str
    confidence: float
    error: bool = False
    decided_at: str | None = None


class ProcessingState(BaseModel):
    """Tracks module processing state for a specimen."""

    specimen_id: str
    module: str
    status: str
    confidence: float | None = None
    error: bool = False
    updated_at: str | None = None


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialise the application database with all required tables."""
    conn = init_candidate_db(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS specimens (
            specimen_id TEXT PRIMARY KEY,
            image TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS final_values (
            specimen_id TEXT,
            field TEXT,
            value TEXT,
            module TEXT,
            confidence REAL,
            error INTEGER DEFAULT 0,
            decided_at TEXT,
            PRIMARY KEY (specimen_id, field)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processing_state (
            specimen_id TEXT,
            module TEXT,
            status TEXT,
            confidence REAL,
            error INTEGER DEFAULT 0,
            updated_at TEXT,
            PRIMARY KEY (specimen_id, module)
        )
        """
    )
    conn.commit()
    return conn


def insert_specimen(conn: sqlite3.Connection, specimen: Specimen) -> None:
    """Insert or replace a specimen record."""
    conn.execute(
        "INSERT OR REPLACE INTO specimens (specimen_id, image) VALUES (?, ?)",
        (specimen.specimen_id, specimen.image),
    )
    conn.commit()


def fetch_specimen(conn: sqlite3.Connection, specimen_id: str) -> Optional[Specimen]:
    """Fetch a specimen by identifier."""
    row = conn.execute(
        "SELECT specimen_id, image FROM specimens WHERE specimen_id = ?",
        (specimen_id,),
    ).fetchone()
    if not row:
        return None
    return Specimen(specimen_id=row[0], image=row[1])


def insert_final_value(conn: sqlite3.Connection, final: FinalValue) -> FinalValue:
    """Persist a final value selection and return the stored record."""
    decided_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO final_values (specimen_id, field, value, module, confidence, error, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            final.specimen_id,
            final.field,
            final.value,
            final.module,
            final.confidence,
            int(final.error),
            decided_at,
        ),
    )
    conn.commit()
    return final.model_copy(update={"decided_at": decided_at})


def fetch_final_value(
    conn: sqlite3.Connection, specimen_id: str, field: str
) -> Optional[FinalValue]:
    """Retrieve a final value for the given specimen and field."""
    row = conn.execute(
        """
        SELECT specimen_id, field, value, module, confidence, error, decided_at
        FROM final_values
        WHERE specimen_id = ? AND field = ?
        """,
        (specimen_id, field),
    ).fetchone()
    if not row:
        return None
    return FinalValue(
        specimen_id=row[0],
        field=row[1],
        value=row[2],
        module=row[3],
        confidence=row[4],
        error=bool(row[5]),
        decided_at=row[6],
    )


def upsert_processing_state(
    conn: sqlite3.Connection, state: ProcessingState
) -> ProcessingState:
    """Insert or update processing state for a module."""
    updated_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO processing_state
            (specimen_id, module, status, confidence, error, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            state.specimen_id,
            state.module,
            state.status,
            state.confidence,
            int(state.error),
            updated_at,
        ),
    )
    conn.commit()
    return state.model_copy(update={"updated_at": updated_at})


def fetch_processing_state(
    conn: sqlite3.Connection, specimen_id: str, module: str
) -> Optional[ProcessingState]:
    """Fetch processing state for a specimen/module pair."""
    row = conn.execute(
        """
        SELECT specimen_id, module, status, confidence, error, updated_at
        FROM processing_state
        WHERE specimen_id = ? AND module = ?
        """,
        (specimen_id, module),
    ).fetchone()
    if not row:
        return None
    return ProcessingState(
        specimen_id=row[0],
        module=row[1],
        status=row[2],
        confidence=row[3],
        error=bool(row[4]),
        updated_at=row[5],
    )


def migrate(db_path: Path) -> None:
    """Run database migrations ensuring all tables and columns exist."""
    conn = init_db(db_path)
    conn.close()


__all__ = [
    "Specimen",
    "FinalValue",
    "ProcessingState",
    "init_db",
    "insert_specimen",
    "fetch_specimen",
    "insert_final_value",
    "fetch_final_value",
    "upsert_processing_state",
    "fetch_processing_state",
    "migrate",
]
