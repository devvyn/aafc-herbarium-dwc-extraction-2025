from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .candidate_models import (
    Candidate as CandidateModel,
    Decision as DecisionModel,
    init_db as models_init_db,
    migrate as models_migrate,
)


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


def init_db(db_path: Path) -> Session:
    """Initialise the candidate database and return a session."""

    return models_init_db(db_path)


def migrate(db_path: Path) -> None:
    """Upgrade an existing candidate database."""

    models_migrate(db_path)


def insert_candidate(
    session: Session,
    run_id: str,
    image: str,
    candidate: Candidate,
) -> None:
    """Persist a candidate record to the database."""

    model = CandidateModel(
        run_id=run_id,
        image=image,
        value=candidate.value,
        engine=candidate.engine,
        confidence=candidate.confidence,
        error=candidate.error,
    )
    session.add(model)
    session.commit()


def fetch_candidates(session: Session, image: str) -> List[Candidate]:
    """Retrieve all candidate values for an image sorted by confidence."""

    stmt = (
        select(CandidateModel)
        .where(CandidateModel.image == image)
        .order_by(CandidateModel.confidence.desc())
    )
    rows = session.execute(stmt).scalars().all()
    return [
        Candidate(
            value=row.value,
            engine=row.engine,
            confidence=row.confidence,
            error=row.error,
        )
        for row in rows
    ]


def fetch_candidates_sqlite(conn, image: str) -> List[Candidate]:
    """Retrieve all candidate values for an image using raw sqlite3 connection."""

    cursor = conn.cursor()
    cursor.execute(
        "SELECT value, engine, confidence, error FROM candidates "
        "WHERE image = ? ORDER BY confidence DESC",
        (image,),
    )
    rows = cursor.fetchall()
    return [
        Candidate(
            value=row[0],
            engine=row[1],
            confidence=row[2],
            error=bool(row[3]),
        )
        for row in rows
    ]


def best_candidate(session: Session, image: str) -> Optional[Candidate]:
    """Return the highest-confidence candidate for an image if available."""

    rows = fetch_candidates(session, image)
    return rows[0] if rows else None


def record_decision(session: Session, image: str, candidate: Candidate) -> Decision:
    """Persist a reviewer decision and return the stored record."""

    stmt = (
        select(CandidateModel.run_id)
        .where(
            (CandidateModel.image == image)
            & (CandidateModel.value == candidate.value)
            & (CandidateModel.engine == candidate.engine)
        )
        .order_by(CandidateModel.confidence.desc())
    )
    run_row = session.execute(stmt).first()
    run_id = run_row[0] if run_row else None
    decided_at = datetime.now(timezone.utc).isoformat()
    model = DecisionModel(
        image=image,
        value=candidate.value,
        engine=candidate.engine,
        run_id=run_id,
        decided_at=decided_at,
    )
    session.add(model)
    session.commit()
    return Decision(
        value=candidate.value,
        engine=candidate.engine,
        run_id=run_id,
        decided_at=decided_at,
    )


def fetch_decision(session: Session, image: str) -> Optional[Decision]:
    """Retrieve the stored decision for an image if present."""

    stmt = (
        select(DecisionModel)
        .where(DecisionModel.image == image)
        .order_by(DecisionModel.decided_at.desc())
    )
    row = session.execute(stmt).scalars().first()
    if not row:
        return None
    return Decision(
        value=row.value,
        engine=row.engine,
        run_id=row.run_id,
        decided_at=row.decided_at,
    )


def import_decisions(dest: Session, src: Session) -> None:
    """Merge decisions from ``src`` into ``dest`` with duplicate checks."""

    rows = src.execute(select(DecisionModel)).scalars().all()
    latest: dict[str, DecisionModel] = {}
    for row in rows:
        current = latest.get(row.image)
        if not current or row.decided_at > current.decided_at:
            latest[row.image] = row

    for row in latest.values():
        exists = dest.execute(select(DecisionModel).where(DecisionModel.image == row.image)).first()
        if exists:
            raise ValueError(f"Decision for {row.image} already exists")
        dest.add(
            DecisionModel(
                run_id=row.run_id,
                image=row.image,
                value=row.value,
                engine=row.engine,
                decided_at=row.decided_at,
            )
        )
    dest.commit()


__all__ = [
    "Candidate",
    "Decision",
    "init_db",
    "migrate",
    "insert_candidate",
    "fetch_candidates",
    "best_candidate",
    "record_decision",
    "fetch_decision",
    "import_decisions",
]
