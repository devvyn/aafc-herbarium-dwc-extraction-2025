import sys
from importlib import resources
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:  # pragma: no cover
    import tomli  # type: ignore


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dwc import configure_mappings, map_custom_schema, map_ocr_to_dwc, normalize_vocab


def load_config(config_path: Path | None) -> dict:
    cfg_path = resources.files("config").joinpath("config.default.toml")
    with cfg_path.open("rb") as f:
        config = tomli.load(f)
    if config_path:
        with config_path.open("rb") as f:
            user_cfg = tomli.load(f)
        _deep_update(config, user_cfg)
    return config


def _deep_update(d: dict, u: dict) -> dict:
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            _deep_update(d[k], v)
        else:
            d[k] = v
    return d


def test_load_config_merge(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("""
[ocr]
preferred_engine = "tesseract"
[gpt]
model = "gpt-test"
""")
    cfg = load_config(cfg_path)
    assert cfg["ocr"]["preferred_engine"] == "tesseract"
    assert cfg["gpt"]["model"] == "gpt-test"
    # default from base config remains
    assert cfg["ocr"]["allow_gpt"] is True


def test_normalize_vocab_rules() -> None:
    assert normalize_vocab("herbarium sheet", "basisOfRecord") == "PreservedSpecimen"
    assert normalize_vocab("Holotype", "typeStatus") == "holotype"
    assert normalize_vocab("specimen voucher", "basisOfRecord") == "PreservedSpecimen"
    assert normalize_vocab("Syntype", "typeStatus") == "syntype"
    assert normalize_vocab("Marsh", "habitat") == "wetland"
    assert normalize_vocab("1 km", "coordinatePrecision") == "0.01"


def test_custom_mappings_from_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("""
[dwc.custom]
barcode = "catalogNumber"
""")
    cfg = load_config(cfg_path)
    configure_mappings(cfg["dwc"]["custom"])
    record = map_ocr_to_dwc({"barcode": "X"})
    assert record.catalogNumber == "X"
    custom = map_custom_schema({"barcode": "Y"})
    assert custom.catalogNumber == "Y"
    configure_mappings({})
