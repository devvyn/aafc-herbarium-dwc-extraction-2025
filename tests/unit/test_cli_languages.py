from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from cli import _prepare_ocr_languages


def test_prepare_langs_for_tesseract_iso2() -> None:
    langs, primary = _prepare_ocr_languages("tesseract", ["en", "fr"])
    assert langs == ["eng", "fra"]
    assert primary is None


def test_prepare_langs_for_multilingual_iso3() -> None:
    langs, primary = _prepare_ocr_languages("multilingual", ["eng", "spa"])
    assert langs == ["en", "es"]
    assert primary == "en"


def test_prepare_langs_for_other_engine_returns_raw() -> None:
    langs, primary = _prepare_ocr_languages("vision", ["eng", "fra"])
    assert langs == ["eng", "fra"]
    assert primary is None


def test_prepare_langs_raises_on_invalid_code() -> None:
    with pytest.raises(ValueError):
        _prepare_ocr_languages("multilingual", ["zzz"])
