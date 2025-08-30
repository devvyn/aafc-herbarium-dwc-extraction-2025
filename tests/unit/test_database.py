from pathlib import Path

from io_utils.database import (
    FinalValue,
    ProcessingState,
    Specimen,
    fetch_final_value,
    fetch_processing_state,
    fetch_specimen,
    init_db,
    insert_final_value,
    insert_specimen,
    upsert_processing_state,
)


def test_specimen_and_state_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = init_db(db_path)

    specimen = Specimen(specimen_id="s1", image="img1.jpg")
    insert_specimen(conn, specimen)
    assert fetch_specimen(conn, "s1") == specimen

    state = ProcessingState(
        specimen_id="s1", module="ocr", status="done", confidence=0.8
    )
    stored_state = upsert_processing_state(conn, state)
    fetched_state = fetch_processing_state(conn, "s1", "ocr")
    assert fetched_state and fetched_state.status == "done"
    assert fetched_state.updated_at == stored_state.updated_at

    final = FinalValue(
        specimen_id="s1",
        field="scientificName",
        value="Testus plantus",
        module="ocr",
        confidence=0.8,
    )
    stored_final = insert_final_value(conn, final)
    fetched_final = fetch_final_value(conn, "s1", "scientificName")
    assert fetched_final == stored_final
    conn.close()
