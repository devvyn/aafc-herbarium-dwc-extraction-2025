import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import load_config
from engines import dispatch


def test_image_to_text_passes_lang(monkeypatch, tmp_path: Path) -> None:
    fake_called = {}

    class FakePaddleOCR:
        def __init__(self, lang, use_angle_cls):
            fake_called["lang"] = lang

        def ocr(self, image_path, cls):
            fake_called["image"] = image_path
            return [[(None, ("hello", 0.9))]]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    from engines.paddleocr import image_to_text

    text, conf = image_to_text(tmp_path / "img.png", lang="fr")
    assert fake_called["lang"] == "fr"
    assert fake_called["image"].endswith("img.png")
    assert text == "hello"
    assert conf == [0.9]


def test_dispatch_uses_paddleocr_engine(monkeypatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[ocr]
preferred_engine = "paddleocr"
langs = ["fr", "en"]
[paddleocr]
lang = "fr"
""",
    )
    cfg = load_config(cfg_path)

    import engines.paddleocr as paddleocr

    called = {}

    def fake_image_to_text(image, lang=None, langs=None):
        called["args"] = (image, lang, langs)
        return "hi", [0.8]

    monkeypatch.setattr(paddleocr, "image_to_text", fake_image_to_text)

    text, conf = dispatch(
        "image_to_text",
        image=Path("img.png"),
        engine=cfg["ocr"]["preferred_engine"],
        lang=cfg["paddleocr"]["lang"],
        langs=cfg["ocr"]["langs"],
    )

    assert called["args"] == (Path("img.png"), "fr", ["fr", "en"])
    assert text == "hi"
    assert conf == [0.8]
