from pathlib import Path
import sqlite3

from io_utils.candidates import (
    Candidate,
    init_db,
    insert_candidate,
    fetch_candidates,
    best_candidate,
    record_decision,
    fetch_decision,
)


def test_candidate_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "candidates.db"
    conn = init_db(db_path)
    insert_candidate(
        conn,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )
    insert_candidate(
        conn,
        "run1",
        "img1.jpg",
        Candidate(value="hola", engine="tesseract", confidence=0.7, error=True),
    )
    conn.close()

    conn = sqlite3.connect(db_path)
    candidates = fetch_candidates(conn, "img1.jpg")
    assert [c.engine for c in candidates] == ["vision", "tesseract"]
    assert [c.error for c in candidates] == [False, True]
    best = best_candidate(conn, "img1.jpg")
    assert best and best.engine == "vision"
    conn.close()


def test_record_and_fetch_decision(tmp_path: Path) -> None:
    db_path = tmp_path / "candidates.db"
    conn = init_db(db_path)
    insert_candidate(
        conn,
        "run1",
        "img1.jpg",
        Candidate(value="hello", engine="vision", confidence=0.9),
    )
    decision = record_decision(
        conn, "img1.jpg", Candidate(value="hello", engine="vision", confidence=0.9)
    )
    fetched = fetch_decision(conn, "img1.jpg")
    assert fetched == decision
    assert fetched.run_id == "run1"
    conn.close()
