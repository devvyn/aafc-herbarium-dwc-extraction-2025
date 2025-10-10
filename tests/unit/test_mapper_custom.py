import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:  # pragma: no cover
    import tomli  # type: ignore

from dwc import configure_mappings, map_custom_schema


def test_map_custom_schema_default() -> None:
    record = map_custom_schema({"barcode": "ABC123"})
    assert record.catalogNumber == "ABC123"


def test_map_custom_schema_override() -> None:
    record = map_custom_schema({"barcode": "ABC123"}, {"barcode": "otherCatalogNumbers"})
    assert record.otherCatalogNumbers == "ABC123"


def test_map_custom_schema_from_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("""
[dwc.custom]
barcode = "catalogNumber"
""")
    with cfg_path.open("rb") as f:
        cfg = tomli.load(f)
    configure_mappings(cfg["dwc"]["custom"])
    record = map_custom_schema({"barcode": "Z"})
    assert record.catalogNumber == "Z"
    configure_mappings({})
