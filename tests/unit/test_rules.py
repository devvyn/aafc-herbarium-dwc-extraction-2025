from dwc import map_ocr_to_dwc, normalize_vocab


def test_mapping_rules_and_vocab_normalization() -> None:
    ocr_output = {
        "collector": "A. Botanist",
        "collection date": "2024-05-01",
        "basisOfRecord": "herbarium sheet",
    }
    record = map_ocr_to_dwc(ocr_output)
    assert record.recordedBy == "A. Botanist"
    assert record.eventDate == "2024-05-01"
    assert record.basisOfRecord == "PreservedSpecimen"


def test_sex_vocab_normalization() -> None:
    assert normalize_vocab("f", "sex") == "female"
