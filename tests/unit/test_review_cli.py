from pathlib import Path
from io_utils.candidates import Candidate, init_db, insert_candidate
from io_utils.candidate_models import Candidate as CandidateModel, Decision as DecisionModel
from review import review_candidates
from sqlalchemy import select


def test_review_cli_records_choice(tmp_path: Path, monkeypatch) -> None:
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
        Candidate(value="hola", engine="tesseract", confidence=0.7),
    )
    session.close()

    monkeypatch.setattr("builtins.input", lambda _: "1")
    decision = review_candidates(db_path, "img1.jpg")
    assert decision and decision.engine == "tesseract"
    assert decision.run_id == "run1"
    session = init_db(db_path)
    row = session.execute(
        select(DecisionModel.value, DecisionModel.engine, DecisionModel.run_id).where(
            DecisionModel.image == "img1.jpg"
        )
    ).one()
    assert row == ("hola", "tesseract", "run1")
    count = session.execute(
        select(CandidateModel.value).where(CandidateModel.image == "img1.jpg")
    ).all()
    assert len(count) == 2
    session.close()
