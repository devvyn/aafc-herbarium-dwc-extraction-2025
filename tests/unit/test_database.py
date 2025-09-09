from pathlib import Path

from io_utils.database import (
    FinalValue,
    ProcessingState,
    Specimen,
    fetch_final_value,
    fetch_import_audit,
    fetch_processing_state,
    fetch_specimen,
    init_db,
    insert_final_value,
    insert_import_audit,
    insert_specimen,
    upsert_processing_state,
    record_failure,
)


def test_specimen_and_state_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = init_db(db_path)

    specimen = Specimen(specimen_id="s1", image="img1.jpg")
    insert_specimen(conn, specimen)
    fetched_specimen = fetch_specimen(conn, "s1")
    assert fetched_specimen and fetched_specimen.image == specimen.image

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
    assert fetched_final and fetched_final.value == stored_final.value

    fail_state = record_failure(conn, "s1", "ocr", "ERR", "boom")
    assert fail_state.retries == 1 and fail_state.error
    fail_state = record_failure(conn, "s1", "ocr", "ERR", "boom")
    assert fail_state.retries == 2
    fetched_fail = fetch_processing_state(conn, "s1", "ocr")
    assert fetched_fail and fetched_fail.retries == 2
    conn.close()


def test_import_audit_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = init_db(db_path)

    stored = insert_import_audit(conn, "alice", "hash123")
    fetched = fetch_import_audit(conn, "hash123")
    assert fetched and fetched.user_id == "alice"
    assert fetched.imported_at == stored.imported_at
    conn.close()
