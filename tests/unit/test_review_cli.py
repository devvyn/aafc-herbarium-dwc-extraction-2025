from pathlib import Path
import sqlite3

from io_utils.candidates import Candidate, init_db, insert_candidate
from review import review_candidates


def test_review_cli_records_choice(tmp_path: Path, monkeypatch) -> None:
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
        Candidate(value="hola", engine="tesseract", confidence=0.7),
    )
    conn.close()

    monkeypatch.setattr("builtins.input", lambda _: "1")
    review_candidates(db_path, "img1.jpg")
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT value, engine FROM decisions WHERE image = ?", ("img1.jpg",)
    ).fetchone()
    assert row == ("hola", "tesseract")
    rows = conn.execute(
        "SELECT value FROM candidates WHERE image = ?", ("img1.jpg",)
    ).fetchall()
    assert len(rows) == 2
    conn.close()
