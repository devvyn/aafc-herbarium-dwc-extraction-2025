import sys
import json
import importlib
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
