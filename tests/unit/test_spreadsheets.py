from pathlib import Path

import pyexcel
import pytest

from io_utils.candidates import Candidate, init_db, insert_candidate
from io_utils.spreadsheets import (
    export_candidates_to_spreadsheet,
    import_review_selections,
)


def test_export_and_import_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "candidates.db"
    conn = init_db(db)
    insert_candidate(
        conn,
        "run1",
        "img1.jpg",
        Candidate(value="foo", engine="vision", confidence=0.9),
    )
    export_path = tmp_path / "review.xlsx"
    export_candidates_to_spreadsheet(conn, "1.0.0", export_path)
    book = pyexcel.get_book(file_name=str(export_path))
    sheet = book["candidates"]
    sheet[1, 6] = "1"
    book.save_as(str(export_path))
    decisions = import_review_selections(export_path, "1.0.0")
    assert decisions == [
        {"run_id": "run1", "image": "img1.jpg", "value": "foo", "engine": "vision"}
    ]


def test_manifest_mismatch(tmp_path: Path) -> None:
    db = tmp_path / "candidates.db"
    conn = init_db(db)
    export_path = tmp_path / "review.xlsx"
    export_candidates_to_spreadsheet(conn, "1.0.0", export_path)
    with pytest.raises(ValueError):
        import_review_selections(export_path, "9.9.9")
