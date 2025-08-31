from pathlib import Path
from types import SimpleNamespace
import importlib

import pytest

from engines.errors import EngineError

gpt_image_to_text = importlib.import_module("engines.gpt.image_to_text")


def test_dry_run_returns_empty(tmp_path: Path) -> None:
    img = tmp_path / "img.jpg"
    img.write_bytes(b"data")

    text, confidences = gpt_image_to_text.image_to_text(
        img, model="gpt-4", dry_run=True
    )

    assert text == ""
    assert confidences == []


def test_success(monkeypatch, tmp_path: Path) -> None:
    img = tmp_path / "img.jpg"
    img.write_bytes(b"data")

    resp = SimpleNamespace(output_text="hello", confidence=0.7)
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: resp)
    )
    monkeypatch.setattr(gpt_image_to_text, "OpenAI", lambda: fake_client)

    text, confidences = gpt_image_to_text.image_to_text(img, model="gpt-4")

    assert text == "hello"
    assert confidences == [0.7]


def test_api_error(monkeypatch, tmp_path: Path) -> None:
    img = tmp_path / "img.jpg"
    img.write_bytes(b"data")

    def fake_create(**kwargs):
        raise Exception("boom")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(gpt_image_to_text, "OpenAI", lambda: fake_client)

    with pytest.raises(EngineError) as excinfo:
        gpt_image_to_text.image_to_text(img, model="gpt-4")

    assert excinfo.value.code == "API_ERROR"
