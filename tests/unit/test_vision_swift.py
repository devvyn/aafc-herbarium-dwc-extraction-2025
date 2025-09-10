import sys
import json
import importlib
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import load_config
from engines import dispatch
import engines.vision_swift as vision_swift
from engines.vision_swift import run as vision_run

run_module = importlib.import_module("engines.vision_swift.run")


def test_run_parses_output(monkeypatch):
    fake_output = [
        {"text": "foo", "boundingBox": [0, 0, 1, 1], "confidence": 0.9},
        {"text": "bar", "boundingBox": [1, 1, 2, 2], "confidence": 0.8},
    ]

    def fake_subprocess_run(cmd, capture_output, text, check):
        return SimpleNamespace(stdout=json.dumps(fake_output))

    monkeypatch.setattr(run_module.subprocess, "run", fake_subprocess_run)

    tokens, boxes, confidences = vision_run("image.png")
    assert tokens == ["foo", "bar"]
    assert boxes == [[0, 0, 1, 1], [1, 1, 2, 2]]
    assert confidences == [0.9, 0.8]


def test_image_to_text_concatenates_tokens(monkeypatch):
    def fake_run(image_path: str, langs=None):
        return ["hello", "world"], [], [0.5, 0.7]

    monkeypatch.setattr(vision_swift, "run", fake_run)
    text, confidences = vision_swift.image_to_text(Path("image.png"))
    assert text == "hello world"
    assert confidences == [0.5, 0.7]


def test_dispatch_uses_vision_engine(monkeypatch):
    cfg = load_config(None)
    called = {}

    def fake_image_to_text(image: Path):
        called["used"] = True
        return "hi", [0.9]

    monkeypatch.setattr(vision_swift, "image_to_text", fake_image_to_text)
    text, confidences = dispatch(
        "image_to_text", image=Path("img.png"), engine=cfg["ocr"]["preferred_engine"]
    )

    assert called["used"] is True
    assert text == "hi"
    assert confidences == [0.9]
