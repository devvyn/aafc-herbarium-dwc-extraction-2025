import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import qc
import cli
from cli import load_config
from qc.gbif import (
    DEFAULT_REVERSE_GEOCODE_ENDPOINT,
    DEFAULT_SPECIES_MATCH_ENDPOINT,
    GbifLookup,
)
from dwc import map_ocr_to_dwc, normalize_vocab
from PIL import Image


def _fake_dispatch(step, **kwargs):
    if step == "image_to_text":
        return "text", [0.9]
    return (
        {"scientificName": "Orig", "decimalLatitude": "1", "decimalLongitude": "2"},
        {"scientificName": 0.9},
    )


def test_detect_duplicates_hash_collision():
    catalog = {}
    sha = "a" * 64
    assert qc.detect_duplicates(catalog, sha, 10) == []
    assert qc.detect_duplicates(catalog, sha, 10) == ["duplicate:sha256"]


def test_detect_duplicates_phash_collision():
    catalog = {}
    sha1 = "0" * 64
    sha2 = "0" * 63 + "1"
    qc.detect_duplicates(catalog, sha1, 10)
    assert qc.detect_duplicates(catalog, sha2, 10) == ["duplicate:phash"]


def test_flag_low_confidence():
    assert qc.flag_low_confidence(0.5, 0.7) == ["low_confidence"]
    assert qc.flag_low_confidence(0.9, 0.7) == []


def test_flag_top_fifth():
    qc.TOP_FIFTH_PCT = 20
    assert qc.flag_top_fifth(80) == ["top_fifth_scan"]
    assert qc.flag_top_fifth(50) == []


def test_gbif_endpoints_default():
    cfg = load_config(None)
    gbif = GbifLookup.from_config(cfg)
    assert gbif.species_match_endpoint == DEFAULT_SPECIES_MATCH_ENDPOINT
    assert gbif.reverse_geocode_endpoint == DEFAULT_REVERSE_GEOCODE_ENDPOINT


def test_gbif_endpoints_override(tmp_path: Path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[qc.gbif]
species_match_endpoint = "https://example.org/species"
reverse_geocode_endpoint = "https://example.org/reverse"
"""
    )
    cfg = load_config(cfg_path)
    gbif = GbifLookup.from_config(cfg)
    assert gbif.species_match_endpoint == "https://example.org/species"
    assert gbif.reverse_geocode_endpoint == "https://example.org/reverse"


def test_map_ocr_to_dwc_rules() -> None:
    record = map_ocr_to_dwc(
        {
            "collector": "Jane Doe",
            "collector number": "42",
            "date collected": "2025-09-01",
            "barcode": "ABC123",
            "basisOfRecord": "herbarium sheet",
            "typeStatus": "Holotype",
        }
    )
    assert record.recordedBy == "Jane Doe"
    assert record.eventDate == "2025-09-01"
    assert record.catalogNumber == "ABC123"
    assert record.recordNumber == "42"
    assert record.basisOfRecord == "PreservedSpecimen"
    assert record.typeStatus == "holotype"


def test_normalize_vocab_field_note() -> None:
    assert normalize_vocab("field note", "basisOfRecord") == "HumanObservation"


def test_process_image_gbif_success(monkeypatch, tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    cfg = {
        "ocr": {
            "enabled_engines": ["test"],
            "preferred_engine": "test",
            "allow_tesseract_on_macos": True,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True},
        "qc": {"gbif": {"enabled": True}},
        "preprocess": {},
    }
    monkeypatch.setattr(cli, "available_engines", lambda step: ["test"])
    monkeypatch.setattr(cli, "preprocess_image", lambda p, c: p)
    monkeypatch.setattr(cli, "compute_sha256", lambda p: "hash")
    monkeypatch.setattr(cli, "dispatch", _fake_dispatch)
    monkeypatch.setattr(cli, "get_fallback_policy", lambda engine: None)
    monkeypatch.setattr(cli.qc, "detect_duplicates", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_low_confidence", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_top_fifth", lambda *a, **k: [])
    monkeypatch.setattr(cli, "insert_specimen", lambda conn, specimen: None)
    monkeypatch.setattr(cli, "fetch_processing_state", lambda conn, sid, mod: None)
    monkeypatch.setattr(cli, "upsert_processing_state", lambda conn, state: None)
    monkeypatch.setattr(
        cli,
        "record_failure",
        lambda *a, **k: cli.ProcessingState(
            specimen_id="1", module="process", status="error", retries=0, error="", confidence=None
        ),
    )

    class DummyGbif:
        def verify_taxonomy(self, record):
            updated = record.copy()
            updated["scientificName"] = "Corrected"
            updated["kingdom"] = "Plantae"
            return updated

        def verify_locality(self, record):
            updated = record.copy()
            updated["country"] = "Canada"
            return updated

    monkeypatch.setattr(cli.qc.GbifLookup, "from_config", lambda cfg: DummyGbif())
    cand_session = cli.init_candidate_db(tmp_path / "candidates.db")
    app_conn = cli.init_app_db(tmp_path / "app.db")
    event, dwc_row, ident_rows = cli.process_image(
        img_path, cfg, "run1", {}, cand_session, app_conn, 3, False
    )
    cand_session.close()
    app_conn.close()
    assert set(event["added_fields"]) == {"kingdom", "country"}
    assert "gbif:scientificName" in event["flags"]
    assert event["dwc"]["scientificName"] == "Corrected"
    assert dwc_row["country"] == "Canada"
    assert "gbif:scientificName" in event["dwc"]["flags"]


def test_process_image_gbif_failure(monkeypatch, tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    cfg = {
        "ocr": {
            "enabled_engines": ["test"],
            "preferred_engine": "test",
            "allow_tesseract_on_macos": True,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True},
        "qc": {"gbif": {"enabled": True}},
        "preprocess": {},
    }
    monkeypatch.setattr(cli, "available_engines", lambda step: ["test"])
    monkeypatch.setattr(cli, "preprocess_image", lambda p, c: p)
    monkeypatch.setattr(cli, "compute_sha256", lambda p: "hash")
    monkeypatch.setattr(cli, "dispatch", _fake_dispatch)
    monkeypatch.setattr(cli, "get_fallback_policy", lambda engine: None)
    monkeypatch.setattr(cli.qc, "detect_duplicates", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_low_confidence", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_top_fifth", lambda *a, **k: [])
    monkeypatch.setattr(cli, "insert_specimen", lambda conn, specimen: None)
    monkeypatch.setattr(cli, "fetch_processing_state", lambda conn, sid, mod: None)
    monkeypatch.setattr(cli, "upsert_processing_state", lambda conn, state: None)
    monkeypatch.setattr(
        cli,
        "record_failure",
        lambda *a, **k: cli.ProcessingState(
            specimen_id="1", module="process", status="error", retries=0, error="", confidence=None
        ),
    )

    class FailingGbif:
        def verify_taxonomy(self, record):
            raise RuntimeError("boom")

        def verify_locality(self, record):  # pragma: no cover - not called
            return record

    monkeypatch.setattr(cli.qc.GbifLookup, "from_config", lambda cfg: FailingGbif())
    cand_session = cli.init_candidate_db(tmp_path / "candidates.db")
    app_conn = cli.init_app_db(tmp_path / "app.db")
    event, dwc_row, ident_rows = cli.process_image(
        img_path, cfg, "run1", {}, cand_session, app_conn, 3, False
    )
    cand_session.close()
    app_conn.close()
    assert "boom" in event["errors"][0]
    assert event["added_fields"] == []
    assert "gbif:scientificName" not in event["flags"]
    assert dwc_row["scientificName"] == "Orig"
