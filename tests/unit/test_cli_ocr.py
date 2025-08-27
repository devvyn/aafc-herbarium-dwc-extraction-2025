from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import pytest

import cli


def _setup(monkeypatch, tmp_path, cfg, dispatch):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    monkeypatch.setattr(cli, "load_config", lambda p: cfg)
    monkeypatch.setattr(cli, "dispatch", dispatch)
    import engines
    monkeypatch.setattr(engines, "dispatch", dispatch)
    monkeypatch.setattr(cli, "preprocess_image", lambda p, c: p)
    monkeypatch.setattr(cli, "setup_logging", lambda o: None)
    monkeypatch.setattr(cli, "write_jsonl", lambda *a, **k: None)
    monkeypatch.setattr(cli, "write_dwc_csv", lambda *a, **k: None)
    monkeypatch.setattr(cli, "write_manifest", lambda *a, **k: None)
    monkeypatch.setattr(cli.qc, "detect_duplicates", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_low_confidence", lambda *a, **k: [])
    monkeypatch.setattr(cli.qc, "flag_top_fifth", lambda *a, **k: [])
    return out_dir


def test_process_cli_uses_preferred_engine(monkeypatch, tmp_path):
    calls = []

    def fake_dispatch(task, *args, engine="gpt", **kwargs):
        if task == "image_to_text" and engine == "vision":
            calls.append(engine)
            return "vision text", [0.9]
        if task == "image_to_text" and engine == "gpt":
            calls.append(engine)
            return "gpt text", [0.95]
        if task == "text_to_dwc":
            return {}, 0.9
        raise AssertionError

    cfg = {
        "ocr": {
            "preferred_engine": "vision",
            "allow_tesseract_on_macos": True,
            "allow_gpt": True,
            "confidence_threshold": 0.7,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True, "fallback_threshold": 0.85},
    }
    out_dir = _setup(monkeypatch, tmp_path, cfg, fake_dispatch)
    cli.process_cli(tmp_path, out_dir, None)
    assert calls == ["vision"]


def test_process_cli_falls_back_to_gpt_on_low_confidence(monkeypatch, tmp_path):
    calls = []

    def fake_dispatch(task, *args, engine="gpt", **kwargs):
        if task == "image_to_text" and engine == "vision":
            calls.append(engine)
            return "vision text", [0.5]
        if task == "image_to_text" and engine == "gpt":
            calls.append(engine)
            return "gpt text", [0.95]
        if task == "text_to_dwc":
            return {}, 0.9
        raise AssertionError

    cfg = {
        "ocr": {
            "preferred_engine": "vision",
            "allow_tesseract_on_macos": True,
            "allow_gpt": True,
            "confidence_threshold": 0.7,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True, "fallback_threshold": 0.85},
    }
    out_dir = _setup(monkeypatch, tmp_path, cfg, fake_dispatch)
    cli.process_cli(tmp_path, out_dir, None)
    assert calls == ["vision", "gpt"]


def test_process_cli_avoids_tesseract_on_macos(monkeypatch, tmp_path):
    calls = []

    def fake_dispatch(task, *args, engine="gpt", **kwargs):
        if task == "image_to_text":
            calls.append(engine)
            return "text", [0.9]
        if task == "text_to_dwc":
            return {}, 0.9
        raise AssertionError

    cfg = {
        "ocr": {
            "preferred_engine": "tesseract",
            "allow_tesseract_on_macos": False,
            "allow_gpt": True,
            "confidence_threshold": 0.7,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True, "fallback_threshold": 0.85},
    }
    monkeypatch.setattr(cli.sys, "platform", "darwin")
    out_dir = _setup(monkeypatch, tmp_path, cfg, fake_dispatch)
    cli.process_cli(tmp_path, out_dir, None)
    assert calls == ["gpt"]


def test_process_cli_errors_when_preferred_missing(monkeypatch, tmp_path):
    def fake_dispatch(task, *args, engine="gpt", **kwargs):
        if task == "text_to_dwc":
            return {}, 0.9
        raise AssertionError

    cfg = {
        "ocr": {
            "preferred_engine": "gpt",
            "allow_tesseract_on_macos": True,
            "allow_gpt": True,
            "confidence_threshold": 0.7,
        },
        "gpt": {"model": "gpt-4.1-mini", "dry_run": True, "fallback_threshold": 0.85},
    }
    monkeypatch.setattr(cli, "available_engines", lambda task: ["vision"])
    out_dir = _setup(monkeypatch, tmp_path, cfg, fake_dispatch)
    with pytest.raises(ValueError):
        cli.process_cli(tmp_path, out_dir, None)
