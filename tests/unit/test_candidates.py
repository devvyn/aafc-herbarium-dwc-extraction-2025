from pathlib import Path


import pytest

from io_utils.candidates import (
    Candidate,
    init_db,
    insert_candidate,
    fetch_candidates,
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
    src.add(DecisionModel(run_id=None, image="img1.jpg", value="old", engine="e1", decided_at=earlier))
    src.add(DecisionModel(run_id=None, image="img1.jpg", value="new", engine="e2", decided_at=later))
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
    src.add(DecisionModel(run_id=None, image="img1.jpg", value="val", engine="e1", decided_at=decided_at))
    src.commit()
    dest.add(DecisionModel(run_id=None, image="img1.jpg", value="dest", engine="e2", decided_at=decided_at))
    dest.commit()
    with pytest.raises(ValueError):
        import_decisions(dest, src)


def test_map_ocr_with_custom_mapping() -> None:
    configure_mappings({"sheet": "catalogNumber"})
    record = map_ocr_to_dwc({"sheet": "99"})
    assert record.catalogNumber == "99"
    configure_mappings({})
