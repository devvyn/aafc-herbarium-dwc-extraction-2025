from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Boolean, Float, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base for candidate review tables."""


@dataclass
class Candidate(Base):
    """OCR candidate value for an image."""

    __tablename__ = "candidates"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    image: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, primary_key=True)
    engine: Mapped[str] = mapped_column(String, primary_key=True)
    confidence: Mapped[float] = mapped_column(Float)
    error: Mapped[bool] = mapped_column(Boolean, default=False)


@dataclass
class Decision(Base):
    """Reviewer decision for an image."""

    __tablename__ = "decisions"

    image: Mapped[str] = mapped_column(String, primary_key=True)
    decided_at: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    value: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String)


def init_db(db_path: Path) -> Session:
    """Initialise the candidate database and return a session."""

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def migrate(db_path: Path) -> None:
    """Ensure all candidate tables and columns exist."""

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("candidates")]
    if "error" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN error INTEGER DEFAULT 0"))


__all__ = ["Candidate", "Decision", "init_db", "migrate"]
