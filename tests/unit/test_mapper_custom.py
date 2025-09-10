from dwc import map_custom_schema


def test_map_custom_schema_default() -> None:
    record = map_custom_schema({"barcode": "ABC123"}, {})
    assert record.catalogNumber == "ABC123"


def test_map_custom_schema_override() -> None:
    record = map_custom_schema({"barcode": "ABC123"}, {"barcode": "otherCatalogNumbers"})
    assert record.otherCatalogNumbers == "ABC123"
