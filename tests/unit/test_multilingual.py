import sys
import types
from pathlib import Path
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engines import dispatch


def test_image_to_text_cycles_languages(monkeypatch, tmp_path: Path) -> None:
    called = []

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            called.append(kwargs)

        def ocr(self, image_path, cls):
            # Only the second language returns text
            if called[-1]["lang"] == "fr":
                return []
            return [[(None, ("hello", 0.9))]]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    from engines.multilingual import image_to_text

    text, conf = image_to_text(
        tmp_path / "img.png", ["fr", "en"], {"en": "/models/en"}
    )
    assert called[0]["lang"] == "fr"
    assert "ocr_model_dir" not in called[0]
    assert called[1]["lang"] == "en"
    assert called[1]["ocr_model_dir"].endswith("en")
    assert text == "hello"
    assert conf == [0.9]


def test_dispatch_uses_multilingual_engine(monkeypatch, tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[ocr]
preferred_engine = "multilingual"
langs = ["fr", "en"]
[multilingual]
langs = ["fr", "en"]
model_paths = {en = "/models/en"}
""",
    )
    cfg = tomllib.loads(cfg_path.read_text())

    import engines.multilingual as multilingual

    called = {}

    def fake_image_to_text(image, langs, model_paths=None):
        called["args"] = (image, langs, model_paths)
        return "hi", [0.8]

    monkeypatch.setattr(multilingual, "image_to_text", fake_image_to_text)

    text, conf = dispatch(
        "image_to_text",
        image=Path("img.png"),
        engine=cfg["ocr"]["preferred_engine"],
        langs=cfg["multilingual"]["langs"],
        model_paths=cfg["multilingual"]["model_paths"],
    )

    assert called["args"] == (
        Path("img.png"),
        ["fr", "en"],
        {"en": "/models/en"},
    )
    assert text == "hi"
    assert conf == [0.8]
