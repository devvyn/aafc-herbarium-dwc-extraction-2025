from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from engines.language_codes import normalize_iso2, normalize_iso3, to_iso2, to_iso3


def test_to_iso2_from_iso3() -> None:
    assert to_iso2("eng") == "en"
    assert to_iso2("FRa") == "fr"


def test_to_iso3_from_iso2() -> None:
    assert to_iso3("en") == "eng"
    assert to_iso3("Fr") == "fra"


def test_normalize_iso2_mixed_codes() -> None:
    assert normalize_iso2(["eng", "FrA", "ESp"]) == ["en", "fr", "es"]


def test_normalize_iso3_handles_mixed_inputs() -> None:
    assert normalize_iso3(["en", "FRA", "spa"]) == ["eng", "fra", "spa"]


def test_to_iso2_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        to_iso2("zzz")


def test_to_iso3_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        to_iso3("zz")
