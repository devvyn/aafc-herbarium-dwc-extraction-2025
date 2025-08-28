from __future__ import annotations

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import load_config
from engines import dispatch


def test_load_config_tesseract_overrides(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[ocr]
preferred_engine = "tesseract"
[tesseract]
oem = 2
psm = 7
langs = ["eng","spa"]
extra_args = ["--foo","bar"]
"""
    )
    cfg = load_config(cfg_path)
    t_cfg = cfg["tesseract"]
    assert cfg["ocr"]["preferred_engine"] == "tesseract"
    assert t_cfg["oem"] == 2
    assert t_cfg["psm"] == 7
    assert t_cfg["langs"] == ["eng", "spa"]
    assert t_cfg["extra_args"] == ["--foo", "bar"]


def test_image_to_text_parses_output(monkeypatch, tmp_path: Path) -> None:
    fake_module = types.SimpleNamespace()

    def fake_image_to_data(image, lang, config, output_type):
        assert lang == "eng+spa"
        assert config == "--oem 2 --psm 7 --foo bar"
        return {
            "text": ["hello", "", "world"],
            "conf": ["90", "-1", "80"],
        }

    fake_module.image_to_data = fake_image_to_data
    fake_module.Output = types.SimpleNamespace(DICT="dict")
    monkeypatch.setitem(sys.modules, "pytesseract", fake_module)

    from engines.tesseract import image_to_text

    text, conf = image_to_text(tmp_path / "img.png", 2, 7, ["eng", "spa"], ["--foo", "bar"])
    assert text == "hello world"
    assert conf == [0.9, 0.8]


def test_dispatch_uses_tesseract_engine(monkeypatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[ocr]
preferred_engine = "tesseract"
[tesseract]
oem = 2
psm = 7
langs = ["eng","spa"]
extra_args = ["--foo","bar"]
"""
    )
    cfg = load_config(cfg_path)

    import engines.tesseract as tesseract

    called = {}

    def fake_image_to_text(image, oem, psm, langs, extra_args):
        called["args"] = (image, oem, psm, langs, extra_args)
        return "hi", [0.9]

    monkeypatch.setattr(tesseract, "image_to_text", fake_image_to_text)

    text, conf = dispatch(
        "image_to_text",
        image=Path("img.png"),
        engine=cfg["ocr"]["preferred_engine"],
        oem=cfg["tesseract"]["oem"],
        psm=cfg["tesseract"]["psm"],
        langs=cfg["tesseract"]["langs"],
        extra_args=cfg["tesseract"]["extra_args"],
    )

    assert called["args"] == (
        Path("img.png"), 2, 7, ["eng", "spa"], ["--foo", "bar"]
    )
    assert text == "hi"
    assert conf == [0.9]
