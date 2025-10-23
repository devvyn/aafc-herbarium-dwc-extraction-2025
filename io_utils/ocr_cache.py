"""Run-agnostic OCR result caching system.

This module implements global deduplication of OCR results, separating data
(OCR extractions) from metadata (processing runs). Results are cached by
(specimen_id, engine, engine_version) and reused across runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from sqlalchemy import Float, String, Text, Boolean, JSON, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base for OCR cache tables."""


@dataclass
class OCRResult(Base):
    """Cached OCR result for a specimen."""

    __tablename__ = "ocr_results"

    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    engine: Mapped[str] = mapped_column(String, primary_key=True)
    engine_version: Mapped[str | None] = mapped_column(String, primary_key=True, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    error: Mapped[bool] = mapped_column(Boolean, default=False)
    ocr_timestamp: Mapped[str] = mapped_column(String)


@dataclass
class ProcessingRun(Base):
    """Metadata for a processing run."""

    __tablename__ = "processing_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    config_snapshot: Mapped[dict] = mapped_column(JSON)
    git_commit: Mapped[str | None] = mapped_column(String, nullable=True)
    operator: Mapped[str | None] = mapped_column(String, nullable=True)


@dataclass
class RunLineage(Base):
    """Tracks which specimens were processed in each run."""

    __tablename__ = "run_lineage"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    specimen_id: Mapped[str] = mapped_column(String, primary_key=True)
    processing_status: Mapped[str] = mapped_column(
        String
    )  # "completed", "failed", "skipped", "cached"
    processed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)


def init_db(db_path: Path) -> Session:
    """Initialize the OCR cache database and return a session."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def get_cached_ocr(
    session: Session,
    specimen_id: str,
    engine: str,
    engine_version: str | None = None,
) -> Optional[OCRResult]:
    """Retrieve cached OCR result if available.

    Parameters
    ----------
    session:
        Database session
    specimen_id:
        SHA256 hash of the image
    engine:
        OCR engine name (e.g., "vision", "tesseract")
    engine_version:
        Optional engine version (e.g., "gpt-4-vision-20240101")

    Returns
    -------
    OCRResult or None
        Cached result if found, None otherwise
    """
    stmt = select(OCRResult).where(
        (OCRResult.specimen_id == specimen_id)
        & (OCRResult.engine == engine)
        & (OCRResult.engine_version == engine_version)
    )
    return session.execute(stmt).scalars().first()


def cache_ocr_result(
    session: Session,
    specimen_id: str,
    engine: str,
    extracted_text: str,
    confidence: float,
    engine_version: str | None = None,
    error: bool = False,
) -> OCRResult:
    """Store OCR result in cache.

    Parameters
    ----------
    session:
        Database session
    specimen_id:
        SHA256 hash of the image
    engine:
        OCR engine name
    extracted_text:
        OCR-extracted text
    confidence:
        Confidence score (0.0-1.0)
    engine_version:
        Optional engine version
    error:
        Whether extraction failed

    Returns
    -------
    OCRResult
        The cached result
    """
    result = OCRResult(
        specimen_id=specimen_id,
        engine=engine,
        engine_version=engine_version,
        extracted_text=extracted_text,
        confidence=confidence,
        error=error,
        ocr_timestamp=datetime.now(timezone.utc).isoformat(),
    )
    session.merge(result)  # Use merge to handle duplicates
    session.commit()
    return result


def record_run(
    session: Session,
    run_id: str,
    config: Dict[str, Any],
    git_commit: str | None = None,
    operator: str | None = None,
) -> ProcessingRun:
    """Record a processing run."""
    run = ProcessingRun(
        run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=None,
        config_snapshot=config,
        git_commit=git_commit,
        operator=operator,
    )
    session.add(run)
    session.commit()
    return run


def complete_run(session: Session, run_id: str) -> None:
    """Mark a run as completed."""
    stmt = select(ProcessingRun).where(ProcessingRun.run_id == run_id)
    run = session.execute(stmt).scalars().first()
    if run:
        run.completed_at = datetime.now(timezone.utc).isoformat()
        session.commit()


def record_lineage(
    session: Session,
    run_id: str,
    specimen_id: str,
    status: str,
    cache_hit: bool = False,
) -> RunLineage:
    """Record that a specimen was processed in a run."""
    lineage = RunLineage(
        run_id=run_id,
        specimen_id=specimen_id,
        processing_status=status,
        processed_at=datetime.now(timezone.utc).isoformat(),
        cache_hit=cache_hit,
    )
    session.merge(lineage)
    session.commit()
    return lineage


def get_cache_stats(session: Session, run_id: str) -> Dict[str, int]:
    """Get cache hit statistics for a run."""
    stmt = select(RunLineage).where(RunLineage.run_id == run_id)
    lineages = session.execute(stmt).scalars().all()

    stats = {
        "total": len(lineages),
        "cache_hits": sum(1 for lineage in lineages if lineage.cache_hit),
        "new_ocr": sum(
            1
            for lineage in lineages
            if not lineage.cache_hit and lineage.processing_status == "completed"
        ),
        "failed": sum(1 for lineage in lineages if lineage.processing_status == "failed"),
        "skipped": sum(1 for lineage in lineages if lineage.processing_status == "skipped"),
    }
    stats["cache_hit_rate"] = stats["cache_hits"] / stats["total"] if stats["total"] > 0 else 0.0
    return stats


__all__ = [
    "OCRResult",
    "ProcessingRun",
    "RunLineage",
    "init_db",
    "get_cached_ocr",
    "cache_ocr_result",
    "record_run",
    "complete_run",
    "record_lineage",
    "get_cache_stats",
]
