import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engines import dispatch


def test_image_to_text_runs_all_langs(monkeypatch, tmp_path: Path) -> None:
    called: list[str] = []

    class FakePaddleOCR:
        def __init__(self, lang, use_angle_cls):
            called.append(lang)

        def ocr(self, image_path, cls):
            return [[(None, (f"{called[-1]}-text", 0.9))]]

    fake_module = types.SimpleNamespace(PaddleOCR=FakePaddleOCR)
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    from engines.multilingual import image_to_text

    text, conf = image_to_text(tmp_path / "img.png", ["fr", "en"])
    assert called == ["fr", "en"]
    assert text == "fr-text en-text"
    assert conf == [0.9, 0.9]


def test_dispatch_uses_multilingual_engine(monkeypatch) -> None:
    import engines.multilingual as multilingual

    called: dict[str, tuple] = {}

    def fake_image_to_text(image, langs):
        called["args"] = (image, langs)
        return "hi", [0.8]

    monkeypatch.setattr(multilingual, "image_to_text", fake_image_to_text)

    text, conf = dispatch(
        "image_to_text",
        image=Path("img.png"),
        engine="multilingual",
        langs=["fr", "en"],
    )

    assert called["args"] == (Path("img.png"), ["fr", "en"])
    assert text == "hi"
    assert conf == [0.8]

