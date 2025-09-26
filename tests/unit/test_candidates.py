from pathlib import Path
import sqlite3

import pytest

from io_utils.candidates import (
    Candidate,
    init_db,
    insert_candidate,
    fetch_candidates,
    fetch_candidates_sqlite,
    best_candidate,
    record_decision,
    fetch_decision,
    import_decisions,
)
from io_utils.candidate_models import Decision as DecisionModel
from sqlalchemy import select
from dwc import configure_mappings, map_ocr_to_dwc


def test_candidate_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "candidates.db"
    session = init_db(db_path)
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hola", engine="tesseract", confidence=0.7, error=True),
    )
    session.close()

    session = init_db(db_path)
    candidates = fetch_candidates(session, "img1.jpg")
    assert [c.engine for c in candidates] == ["vision", "tesseract"]
    assert [c.error for c in candidates] == [False, True]
    best = best_candidate(session, "img1.jpg")
    assert best and best.engine == "vision"
    session.close()


def test_record_and_fetch_decision(tmp_path: Path) -> None:
    db_path = tmp_path / "candidates.db"
    session = init_db(db_path)
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )
    decision = record_decision(
        session, "img1.jpg", Candidate(value="hello", engine="vision", confidence=0.9)
    )
    fetched = fetch_decision(session, "img1.jpg")
    assert fetched is not None, "fetch_decision should return a Decision, not None"
    assert fetched == decision
    assert fetched.run_id == "run1"
    session.close()


def test_import_decisions_deduplicates(tmp_path: Path) -> None:
    src_db = tmp_path / "src.db"
    dest_db = tmp_path / "dest.db"
    src = init_db(src_db)
    dest = init_db(dest_db)
    earlier = "2024-01-01T00:00:00+00:00"
    later = "2024-01-02T00:00:00+00:00"
    src.add(
        DecisionModel(run_id=None, image="img1.jpg", value="old", engine="e1", decided_at=earlier)
    )
    src.add(
        DecisionModel(run_id=None, image="img1.jpg", value="new", engine="e2", decided_at=later)
    )
    src.commit()
    import_decisions(dest, src)
    row = dest.execute(
        select(DecisionModel.value, DecisionModel.engine, DecisionModel.decided_at).where(
            DecisionModel.image == "img1.jpg"
        )
    ).one()
    assert row == ("new", "e2", later)


def test_import_decisions_conflict(tmp_path: Path) -> None:
    src_db = tmp_path / "src.db"
    dest_db = tmp_path / "dest.db"
    src = init_db(src_db)
    dest = init_db(dest_db)
    decided_at = "2024-01-01T00:00:00+00:00"
    src.add(
        DecisionModel(
            run_id=None, image="img1.jpg", value="val", engine="e1", decided_at=decided_at
        )
    )
    src.commit()
    dest.add(
        DecisionModel(
            run_id=None, image="img1.jpg", value="dest", engine="e2", decided_at=decided_at
        )
    )
    dest.commit()
    with pytest.raises(ValueError):
        import_decisions(dest, src)


def test_map_ocr_with_custom_mapping() -> None:
    configure_mappings({"sheet": "catalogNumber"})
    record = map_ocr_to_dwc({"sheet": "99"})
    assert record.catalogNumber == "99"
    configure_mappings({})


def test_fetch_candidates_sqlite_compatibility(tmp_path: Path) -> None:
    """Test that fetch_candidates_sqlite works with raw sqlite3 connections.

    Regression test for SQLAlchemy compatibility issues in web review interface.
    """
    db_path = tmp_path / "candidates.db"

    # Setup data using SQLAlchemy session
    session = init_db(db_path)
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hola", engine="tesseract", confidence=0.7, error=True),
    )
    session.close()

    # Test raw sqlite3 access (as used by review_web.py)
    with sqlite3.connect(db_path) as conn:
        candidates = fetch_candidates_sqlite(conn, "img1.jpg")

    assert len(candidates) == 2
    assert [c.engine for c in candidates] == ["vision", "tesseract"]  # Ordered by confidence desc
    assert [c.confidence for c in candidates] == [0.9, 0.7]
    assert [c.error for c in candidates] == [False, True]
    assert candidates[0].value == "hello"
    assert candidates[1].value == "hola"


def test_fetch_decision_returns_none_when_no_decision(tmp_path: Path) -> None:
    """Test that fetch_decision properly returns None when no decision exists."""
    db_path = tmp_path / "candidates.db"
    session = init_db(db_path)

    # Add a candidate but no decision
    insert_candidate(
        session,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )

    # Should return None since no decision was recorded
    fetched = fetch_decision(session, "img1.jpg")
    assert fetched is None

    # Should also return None for non-existent image
    fetched_nonexistent = fetch_decision(session, "nonexistent.jpg")
    assert fetched_nonexistent is None

    session.close()


def test_best_candidate_returns_none_when_no_candidates(tmp_path: Path) -> None:
    """Test that best_candidate properly returns None when no candidates exist."""
    db_path = tmp_path / "candidates.db"
    session = init_db(db_path)

    # Should return None for non-existent image
    best = best_candidate(session, "nonexistent.jpg")
    assert best is None

    session.close()


def test_best_candidate_returns_highest_confidence(tmp_path: Path) -> None:
    """Test that best_candidate returns the candidate with highest confidence."""
    db_path = tmp_path / "candidates.db"
    session = init_db(db_path)

    # Add candidates with different confidence levels
    candidates = [
        Candidate(value="low", engine="tesseract", confidence=0.60),
        Candidate(value="high", engine="vision", confidence=0.95),
        Candidate(value="medium", engine="gpt", confidence=0.80),
    ]

    for candidate in candidates:
        insert_candidate(session, "run1", "test.jpg", candidate)

    # Should return the highest confidence candidate
    best = best_candidate(session, "test.jpg")
    assert best is not None
    assert best.value == "high"
    assert best.engine == "vision"
    assert best.confidence == 0.95

    session.close()


def test_sqlalchemy_and_sqlite3_equivalence(tmp_path: Path) -> None:
    """Test that SQLAlchemy and sqlite3 functions return equivalent results."""
    db_path = tmp_path / "candidates.db"

    # Setup test data
    session = init_db(db_path)
    candidates = [
        Candidate(value="first", engine="vision", confidence=0.95),
        Candidate(value="second", engine="tesseract", confidence=0.80),
        Candidate(value="third", engine="gpt", confidence=0.60, error=True),
    ]

    for candidate in candidates:
        insert_candidate(session, "run1", "test.jpg", candidate)
    session.close()

    # Compare results from both functions
    session = init_db(db_path)
    sqlalchemy_results = fetch_candidates(session, "test.jpg")
    session.close()

    with sqlite3.connect(db_path) as conn:
        sqlite3_results = fetch_candidates_sqlite(conn, "test.jpg")

    # Results should be identical
    assert len(sqlalchemy_results) == len(sqlite3_results)

    for sa_result, s3_result in zip(sqlalchemy_results, sqlite3_results):
        assert sa_result.value == s3_result.value
        assert sa_result.engine == s3_result.engine
        assert sa_result.confidence == s3_result.confidence
        assert sa_result.error == s3_result.error
