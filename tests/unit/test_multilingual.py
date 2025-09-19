import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import load_config
from engines import dispatch


def test_image_to_text_tries_languages(monkeypatch, tmp_path: Path) -> None:
    calls = []

    class FakePaddleOCR:
        def __init__(self, lang, use_angle_cls):
            self.lang = lang
            calls.append(lang)

        def ocr(self, image_path, cls):
            if self.lang == "fr":
                return []
            return [[(None, ("bonjour", 0.8))]]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    from engines.multilingual import image_to_text

    text, conf = image_to_text(tmp_path / "img.png", ["fr", "en"])
    assert calls == ["fr", "en"]
    assert text == "bonjour"
    assert conf == [0.8]


def test_image_to_text_normalizes_iso3(monkeypatch, tmp_path: Path) -> None:
    languages = []

    class FakePaddleOCR:
        def __init__(self, lang, use_angle_cls):
            languages.append(lang)

        def ocr(self, image_path, cls):
            return [[(None, ("salve", 0.7))]]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    from engines.multilingual import image_to_text

    text, conf = image_to_text(tmp_path / "img.png", ["eng", "lat"])
    assert languages == ["en", "la"]
    assert text == "salve"
    assert conf == [0.7]


def test_dispatch_uses_multilingual_engine(monkeypatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[ocr]
preferred_engine = "multilingual"
langs = ["fr","en"]
""",
    )
    cfg = load_config(cfg_path)

    import engines.multilingual as multilingual

    called = {}

    def fake_image_to_text(image, langs, model_paths=None):
        called["args"] = (image, langs, model_paths)
        return "hi", [0.9]

    monkeypatch.setattr(multilingual, "image_to_text", fake_image_to_text)

    text, conf = dispatch(
        "image_to_text",
        image=Path("img.png"),
        engine=cfg["ocr"]["preferred_engine"],
        langs=cfg["ocr"]["langs"],
    )

    assert called["args"] == (Path("img.png"), ["fr", "en"], None)
    assert text == "hi"
    assert conf == [0.9]
