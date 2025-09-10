import sys
import csv
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from io_utils.write import (
    write_manifest,
    write_dwc_csv,
    write_jsonl,
    write_identification_history_csv,
    DWC_COLUMNS,
    IDENT_HISTORY_COLUMNS,
)


def test_write_manifest(tmp_path: Path) -> None:
    meta = {"foo": "bar"}
    write_manifest(tmp_path, meta)
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text()) == meta


def test_write_dwc_csv(tmp_path: Path) -> None:
    rows = [{"catalogNumber": "1", "scientificName": "Test"}]
    write_dwc_csv(tmp_path, rows)
    csv_path = tmp_path / "occurrence.csv"
    assert csv_path.exists()
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        data = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames == DWC_COLUMNS
    assert data[0]["catalogNumber"] == "1"
    assert data[0]["scientificName"] == "Test"
    assert data[0]["collectionCode"] == ""


def test_write_identification_history_csv(tmp_path: Path) -> None:
    rows = [
        {"occurrenceID": "1", "identificationID": "a", "scientificName": "A", "isCurrent": "TRUE"},
        {"occurrenceID": "1", "identificationID": "b", "scientificName": "B", "isCurrent": "FALSE"},
    ]
    write_identification_history_csv(tmp_path, rows)
    csv_path = tmp_path / "identification_history.csv"
    assert csv_path.exists()
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        data = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames == IDENT_HISTORY_COLUMNS
    assert len(data) == 2
    assert data[0]["scientificName"] == "A"


def test_write_jsonl(tmp_path: Path) -> None:
    events = [{"id": 1}, {"id": 2}]
    write_jsonl(tmp_path, events)
    jsonl_path = tmp_path / "raw.jsonl"
    assert jsonl_path.exists()
    lines = jsonl_path.read_text().splitlines()
    assert [json.loads(line) for line in lines] == events


def test_write_jsonl_appends(tmp_path: Path) -> None:
    events = [{"id": 1}]
    write_jsonl(tmp_path, events)
    write_jsonl(tmp_path, [{"id": 2}], append=True)
    jsonl_path = tmp_path / "raw.jsonl"
    lines = jsonl_path.read_text().splitlines()
    assert [json.loads(line) for line in lines] == [{"id": 1}, {"id": 2}]


def test_write_dwc_csv_appends(tmp_path: Path) -> None:
    rows = [{"catalogNumber": "1"}]
    write_dwc_csv(tmp_path, rows)
    write_dwc_csv(tmp_path, [{"catalogNumber": "2"}], append=True)
    csv_path = tmp_path / "occurrence.csv"
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        data = list(reader)
    assert [row["catalogNumber"] for row in data] == ["1", "2"]


def test_write_identification_history_csv_appends(tmp_path: Path) -> None:
    rows = [
        {"occurrenceID": "1", "identificationID": "a", "scientificName": "A", "isCurrent": "TRUE"}
    ]
    write_identification_history_csv(tmp_path, rows)
    write_identification_history_csv(
        tmp_path,
        [
            {
                "occurrenceID": "2",
                "identificationID": "b",
                "scientificName": "B",
                "isCurrent": "FALSE",
            }
        ],
        append=True,
    )
    csv_path = tmp_path / "identification_history.csv"
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        data = list(reader)
    assert [row["identificationID"] for row in data] == ["a", "b"]
