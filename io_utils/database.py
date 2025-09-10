from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dataclasses import dataclass

from sqlalchemy import Boolean, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


@dataclass
class Specimen(Base):
    """Represents a herbarium specimen and associated image."""

    __tablename__ = "specimens"

    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    image: Mapped[str] = mapped_column(String)


@dataclass
class FinalValue(Base):
    """Represents the final selected value for a field."""

    __tablename__ = "final_values"

    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    field: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    module: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    error: Mapped[bool] = mapped_column(Boolean, default=False)
    decided_at: Mapped[str | None] = mapped_column(String, nullable=True)


@dataclass
class ProcessingState(Base):
    """Tracks module processing state for a specimen."""

    __tablename__ = "processing_state"

    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    module: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[bool] = mapped_column(Boolean, default=False)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)


@dataclass
class ImportAudit(Base):
    """Audit record for review bundle imports."""

    __tablename__ = "import_audit"

    bundle_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String)
    imported_at: Mapped[str] = mapped_column(String)


def init_db(db_path: Path) -> Session:
    """Initialise the application database and return a session."""

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def insert_specimen(session: Session, specimen: Specimen) -> None:
    session.merge(specimen)
    session.commit()


def fetch_specimen(session: Session, specimen_id: str) -> Optional[Specimen]:
    return session.get(Specimen, specimen_id)


def insert_final_value(session: Session, final: FinalValue) -> FinalValue:
    decided_at = datetime.now(timezone.utc).isoformat()
    final.decided_at = decided_at
    session.merge(final)
    session.commit()
    return final


def fetch_final_value(session: Session, specimen_id: str, field: str) -> Optional[FinalValue]:
    return session.get(FinalValue, (specimen_id, field))


def upsert_processing_state(session: Session, state: ProcessingState) -> ProcessingState:
    updated_at = datetime.now(timezone.utc).isoformat()
    state.updated_at = updated_at
    session.merge(state)
    session.commit()
    return state


def fetch_processing_state(
    session: Session, specimen_id: str, module: str
) -> Optional[ProcessingState]:
    return session.get(ProcessingState, (specimen_id, module))


def record_failure(
    session: Session,
    specimen_id: str,
    module: str,
    error_code: str,
    error_message: str,
) -> ProcessingState:
    existing = fetch_processing_state(session, specimen_id, module)
    retries = existing.retries + 1 if existing else 1
    state = ProcessingState(
        specimen_id=specimen_id,
        module=module,
        status="error",
        error=True,
        retries=retries,
        error_code=error_code,
        error_message=error_message,
    )
    return upsert_processing_state(session, state)


def insert_import_audit(session: Session, user_id: str, bundle_hash: str) -> ImportAudit:
    """Store an import audit entry and return the stored record."""

    imported_at = datetime.now(timezone.utc).isoformat()
    audit = ImportAudit(bundle_hash=bundle_hash, user_id=user_id, imported_at=imported_at)
    session.add(audit)
    session.commit()
    return audit


def fetch_import_audit(session: Session, bundle_hash: str) -> Optional[ImportAudit]:
    """Retrieve an audit entry by bundle hash if present."""

    return session.get(ImportAudit, bundle_hash)


def migrate(db_path: Path) -> None:
    """Run database migrations ensuring all tables exist."""

    session = init_db(db_path)
    session.close()


__all__ = [
    "Specimen",
    "FinalValue",
    "ProcessingState",
    "ImportAudit",
    "init_db",
    "insert_specimen",
    "fetch_specimen",
    "insert_final_value",
    "fetch_final_value",
    "upsert_processing_state",
    "fetch_processing_state",
    "record_failure",
    "insert_import_audit",
    "fetch_import_audit",
    "migrate",
]
