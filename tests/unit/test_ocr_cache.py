"""Tests for OCR cache system (run-agnostic deduplication)."""

from pathlib import Path

from io_utils.ocr_cache import (
    ProcessingRun,
    RunLineage,
    cache_ocr_result,
    complete_run,
    get_cache_stats,
    get_cached_ocr,
    init_db,
    record_lineage,
    record_run,
)


def test_cache_init(tmp_path: Path) -> None:
    """Test database initialization."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)
    assert session is not None
    assert db_path.exists()
    session.close()


def test_cache_ocr_result_roundtrip(tmp_path: Path) -> None:
    """Test caching and retrieving OCR results."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    # Cache a result
    result = cache_ocr_result(
        session,
        specimen_id="abc123",
        engine="vision",
        extracted_text="Test specimen label",
        confidence=0.95,
        engine_version=None,
        error=False,
    )

    assert result.specimen_id == "abc123"
    assert result.engine == "vision"
    assert result.extracted_text == "Test specimen label"
    assert result.confidence == 0.95

    # Retrieve it
    cached = get_cached_ocr(session, "abc123", "vision", None)
    assert cached is not None
    assert cached.extracted_text == "Test specimen label"
    assert cached.confidence == 0.95
    assert cached.error is False

    session.close()


def test_cache_deduplication(tmp_path: Path) -> None:
    """Test that same specimen+engine only stores one result."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    # Cache same specimen twice with different text (should update)
    # Note: engine_version must be non-NULL for merge to work properly
    cache_ocr_result(session, "abc123", "vision", "First text", 0.8, engine_version="v1")
    cache_ocr_result(session, "abc123", "vision", "Second text", 0.9, engine_version="v1")

    # Should only have one result (merged/updated)
    cached = get_cached_ocr(session, "abc123", "vision", "v1")
    assert cached is not None
    assert cached.extracted_text == "Second text"
    assert cached.confidence == 0.9

    session.close()


def test_cache_engine_versioning(tmp_path: Path) -> None:
    """Test that different engine versions are cached separately."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    # Cache with different engine versions
    cache_ocr_result(session, "abc123", "gpt", "GPT-4 result", 0.95, engine_version="gpt-4")
    cache_ocr_result(session, "abc123", "gpt", "GPT-4o result", 0.97, engine_version="gpt-4o")

    # Should retrieve version-specific results
    gpt4 = get_cached_ocr(session, "abc123", "gpt", "gpt-4")
    gpt4o = get_cached_ocr(session, "abc123", "gpt", "gpt-4o")

    assert gpt4 is not None
    assert gpt4.extracted_text == "GPT-4 result"
    assert gpt4o is not None
    assert gpt4o.extracted_text == "GPT-4o result"

    session.close()


def test_cache_miss(tmp_path: Path) -> None:
    """Test cache miss returns None."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    cached = get_cached_ocr(session, "nonexistent", "vision")
    assert cached is None

    session.close()


def test_processing_run_tracking(tmp_path: Path) -> None:
    """Test processing run metadata tracking."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    config = {"ocr": {"preferred_engine": "vision"}, "dwc": {"preferred_engine": "rules"}}
    run = record_run(session, "run_001", config, git_commit="abc123", operator="test_user")

    assert run.run_id == "run_001"
    assert run.config_snapshot == config
    assert run.git_commit == "abc123"
    assert run.operator == "test_user"
    assert run.started_at is not None
    assert run.completed_at is None

    # Complete the run
    complete_run(session, "run_001")

    # Re-fetch to verify completion
    from sqlalchemy import select

    stmt = select(ProcessingRun).where(ProcessingRun.run_id == "run_001")
    completed_run = session.execute(stmt).scalars().first()
    assert completed_run is not None
    assert completed_run.completed_at is not None

    session.close()


def test_run_lineage_tracking(tmp_path: Path) -> None:
    """Test lineage tracking for specimens in runs."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    record_run(session, "run_001", {})

    # Record some lineage
    record_lineage(session, "run_001", "specimen_1", "completed", cache_hit=False)
    record_lineage(session, "run_001", "specimen_2", "cached", cache_hit=True)
    record_lineage(session, "run_001", "specimen_3", "failed", cache_hit=False)

    # Check lineage
    from sqlalchemy import select

    stmt = select(RunLineage).where(RunLineage.run_id == "run_001")
    lineages = session.execute(stmt).scalars().all()

    assert len(lineages) == 3
    assert lineages[0].processing_status == "completed"
    assert lineages[0].cache_hit is False
    assert lineages[1].processing_status == "cached"
    assert lineages[1].cache_hit is True

    session.close()


def test_cache_stats(tmp_path: Path) -> None:
    """Test cache statistics calculation."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    record_run(session, "run_001", {})

    # Simulate processing: 5 new OCR, 3 cache hits, 1 failed, 1 skipped
    record_lineage(session, "run_001", "s1", "completed", cache_hit=False)
    record_lineage(session, "run_001", "s2", "completed", cache_hit=False)
    record_lineage(session, "run_001", "s3", "completed", cache_hit=False)
    record_lineage(session, "run_001", "s4", "completed", cache_hit=False)
    record_lineage(session, "run_001", "s5", "completed", cache_hit=False)
    record_lineage(session, "run_001", "s6", "cached", cache_hit=True)
    record_lineage(session, "run_001", "s7", "cached", cache_hit=True)
    record_lineage(session, "run_001", "s8", "cached", cache_hit=True)
    record_lineage(session, "run_001", "s9", "failed", cache_hit=False)
    record_lineage(session, "run_001", "s10", "skipped", cache_hit=False)

    stats = get_cache_stats(session, "run_001")

    assert stats["total"] == 10
    assert stats["cache_hits"] == 3
    assert stats["new_ocr"] == 5
    assert stats["failed"] == 1
    assert stats["skipped"] == 1
    assert stats["cache_hit_rate"] == 0.3  # 3/10

    session.close()


def test_cache_stats_empty_run(tmp_path: Path) -> None:
    """Test cache stats for run with no specimens."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    record_run(session, "run_empty", {})
    stats = get_cache_stats(session, "run_empty")

    assert stats["total"] == 0
    assert stats["cache_hits"] == 0
    assert stats["cache_hit_rate"] == 0.0

    session.close()


def test_error_caching(tmp_path: Path) -> None:
    """Test that errors are cached and not reused."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    # Cache an error result
    cache_ocr_result(
        session,
        "bad_image",
        "vision",
        "",
        0.0,
        error=True,
    )

    # Retrieve it
    cached = get_cached_ocr(session, "bad_image", "vision")
    assert cached is not None
    assert cached.error is True
    assert cached.extracted_text == ""

    session.close()


def test_multiple_engines_same_specimen(tmp_path: Path) -> None:
    """Test that different engines cache separately for same specimen."""
    db_path = tmp_path / "ocr_cache.db"
    session = init_db(db_path)

    # Cache with different engines
    cache_ocr_result(session, "spec_1", "vision", "Vision result", 0.9)
    cache_ocr_result(session, "spec_1", "tesseract", "Tesseract result", 0.7)
    cache_ocr_result(session, "spec_1", "gpt", "GPT result", 0.95)

    # Should retrieve engine-specific results
    vision = get_cached_ocr(session, "spec_1", "vision")
    tesseract = get_cached_ocr(session, "spec_1", "tesseract")
    gpt = get_cached_ocr(session, "spec_1", "gpt")

    assert vision is not None and vision.extracted_text == "Vision result"
    assert tesseract is not None and tesseract.extracted_text == "Tesseract result"
    assert gpt is not None and gpt.extracted_text == "GPT result"

    session.close()
