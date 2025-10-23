from PIL import Image

import cli


def test_setup_run_applies_engines_and_qc(monkeypatch, tmp_path):
    cfg = {"ocr": {}, "qc": {"top_fifth_scan_pct": 42}}
    monkeypatch.setattr(cli, "load_config", lambda p: cfg)
    monkeypatch.setattr(cli, "setup_logging", lambda o: None)
    cli.qc.TOP_FIFTH_PCT = 0
    result = cli.setup_run(tmp_path, None, ["a"])
    assert result["ocr"]["enabled_engines"] == ["a"]
    assert cli.qc.TOP_FIFTH_PCT == 42


def test_process_image_returns_event(monkeypatch, tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    cfg = {
        "ocr": {
            "enabled_engines": ["test"],
            "preferred_engine": "test",
            "allow_tesseract_on_macos": True,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True},
        "qc": {},
        "preprocess": {},
    }
    monkeypatch.setattr(cli, "available_engines", lambda task: ["test"])
    monkeypatch.setattr(cli, "preprocess_image", lambda p, c: p)
    monkeypatch.setattr(cli, "compute_sha256", lambda p: "hash")
    monkeypatch.setattr(
        cli,
        "dispatch",
        lambda task, *args, **kwargs: (
            ("text", [0.9])
            if task == "image_to_text"
            else ({"occurrenceID": "1"}, {"occurrenceID": 0.9})
        ),
    )
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
            specimen_id="1",
            module="process",
            status="error",
            retries=0,
            error="",
            confidence=None,
        ),
    )
    cand_session = cli.init_candidate_db(tmp_path / "candidates.db")
    cache_session = cli.init_ocr_cache_db(tmp_path / "ocr_cache.db")
    app_conn = cli.init_app_db(tmp_path / "app.db")
    event, dwc_row, ident_rows = cli.process_image(
        img_path, cfg, "run1", {}, cand_session, cache_session, app_conn, 3, False
    )
    cand_session.close()
    cache_session.close()
    app_conn.close()
    assert event["image"] == "img.png"
    assert dwc_row == {"occurrenceID": "1"}
    assert ident_rows == []


def test_write_outputs_calls_writers(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(cli, "write_jsonl", lambda *a, **k: calls.append("jsonl"))
    monkeypatch.setattr(cli, "write_dwc_csv", lambda *a, **k: calls.append("dwc"))
    monkeypatch.setattr(
        cli, "write_identification_history_csv", lambda *a, **k: calls.append("hist")
    )
    monkeypatch.setattr(cli, "write_manifest", lambda *a, **k: calls.append("manifest"))
    cli.write_outputs(tmp_path, [{}], [{}], [{}], {"meta": 1}, False)
    assert calls == ["jsonl", "dwc", "hist", "manifest"]
