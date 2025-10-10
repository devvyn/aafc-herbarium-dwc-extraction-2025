import json
from urllib.error import URLError

import qc.gbif as gbif_module
from qc.gbif import LOCALITY_FIELDS, TAXONOMY_FIELDS, GbifLookup


def _mock_response(data: object):
    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(data).encode()

    return MockResponse()


def test_verify_taxonomy_success(monkeypatch):
    gbif = GbifLookup()
    record = {"scientificName": "Puma concolor"}

    data = {
        field: f"value_{field}"
        for field in TAXONOMY_FIELDS
        if field not in {"taxonKey", "acceptedTaxonKey"}
    }
    data["usageKey"] = "value_taxonKey"
    data["acceptedUsageKey"] = "value_acceptedTaxonKey"
    data["confidence"] = 95  # High confidence
    data["matchType"] = "EXACT"

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.verify_taxonomy(record)

    assert result["taxonKey"] == "value_taxonKey"
    assert result["acceptedTaxonKey"] == "value_acceptedTaxonKey"
    for field in set(TAXONOMY_FIELDS) - {"taxonKey", "acceptedTaxonKey"}:
        assert result[field] == data[field]

    # Check metadata
    assert metadata["gbif_taxonomy_verified"] == True
    assert metadata["gbif_match_type"] == "EXACT"
    assert metadata["gbif_confidence"] == 95
    assert len(metadata["gbif_issues"]) == 0


def test_verify_taxonomy_error(monkeypatch):
    gbif = GbifLookup()
    record = {"scientificName": "Puma concolor"}

    def raise_error(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise URLError("failure")

    monkeypatch.setattr(gbif_module, "urlopen", raise_error)
    result, metadata = gbif.verify_taxonomy(record)
    assert result == record
    assert result is not record
    assert metadata["gbif_taxonomy_verified"] == False
    assert "api_error" in metadata["gbif_issues"]


def test_verify_taxonomy_missing_fields(monkeypatch):
    gbif = GbifLookup()
    record: dict = {}

    def raise_if_called(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(gbif_module, "urlopen", raise_if_called)
    result, metadata = gbif.verify_taxonomy(record)

    assert result == record
    assert result is not record
    assert metadata["gbif_taxonomy_verified"] == False
    assert "no_taxonomy_fields" in metadata["gbif_issues"]


def test_verify_locality_success(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    data = [{field: f"value_{field}" for field in LOCALITY_FIELDS}]
    data[0]["decimalLatitude"] = 45.1  # Slightly different for distance calculation
    data[0]["decimalLongitude"] = -75.1

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.verify_locality(record)
    for field in LOCALITY_FIELDS:
        assert result[field] == data[0][field]

    # Check metadata
    assert metadata["gbif_locality_verified"] == True
    assert metadata["gbif_coordinate_valid"] == True
    assert metadata["gbif_distance_km"] is not None
    assert metadata["gbif_distance_km"] < 20  # Should be a small distance


def test_verify_locality_error(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    def raise_error(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise URLError("failure")

    monkeypatch.setattr(gbif_module, "urlopen", raise_error)
    result, metadata = gbif.verify_locality(record)
    assert result == record
    assert result is not record
    assert metadata["gbif_locality_verified"] == False
    assert "api_error" in metadata["gbif_issues"]


def test_verify_locality_missing_coords(monkeypatch):
    gbif = GbifLookup()
    record: dict = {}

    def raise_if_called(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(gbif_module, "urlopen", raise_if_called)
    result, metadata = gbif.verify_locality(record)

    assert result == record
    assert result is not record
    assert metadata["gbif_locality_verified"] == False
    assert "no_coordinates" in metadata["gbif_issues"]


def test_verify_locality_empty_response(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response([]))
    result, metadata = gbif.verify_locality(record)
    assert result == record and result is not record
    assert metadata["gbif_locality_verified"] == False
    assert "api_error" in metadata["gbif_issues"]


def _bad_json_response():
    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):  # pragma: no cover - executed via json.load
            return b"{"  # invalid JSON

    return MockResponse()


def test_verify_taxonomy_invalid_json(monkeypatch):
    gbif = GbifLookup()
    record = {"scientificName": "Puma concolor"}

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _bad_json_response())
    result, metadata = gbif.verify_taxonomy(record)
    assert result == record and result is not record
    assert metadata["gbif_taxonomy_verified"] == False
    assert "api_error" in metadata["gbif_issues"]


def test_verify_locality_invalid_json(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}
    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _bad_json_response())
    result, metadata = gbif.verify_locality(record)
    assert result == record and result is not record
    assert metadata["gbif_locality_verified"] == False
    assert "api_error" in metadata["gbif_issues"]


def test_verify_locality_invalid_coordinates():
    gbif = GbifLookup()

    # Test invalid latitude
    record = {"decimalLatitude": 95.0, "decimalLongitude": -75.0}  # Invalid lat > 90
    result, metadata = gbif.verify_locality(record)
    assert metadata["gbif_locality_verified"] == False
    assert "invalid_latitude" in metadata["gbif_issues"]

    # Test invalid longitude
    record = {"decimalLatitude": 45.0, "decimalLongitude": 185.0}  # Invalid lng > 180
    result, metadata = gbif.verify_locality(record)
    assert metadata["gbif_locality_verified"] == False
    assert "invalid_longitude" in metadata["gbif_issues"]

    # Test invalid format
    record = {"decimalLatitude": "not_a_number", "decimalLongitude": -75.0}
    result, metadata = gbif.verify_locality(record)
    assert metadata["gbif_locality_verified"] == False
    assert "invalid_latitude_format" in metadata["gbif_issues"]


def test_validate_occurrence_success(monkeypatch):
    gbif = GbifLookup(enable_occurrence_validation=True)
    record = {"scientificName": "Puma concolor", "decimalLatitude": 45.0, "decimalLongitude": -75.0}

    data = {
        "results": [
            {"key": 123, "scientificName": "Puma concolor"},
            {"key": 456, "scientificName": "Puma concolor"},
        ]
    }

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.validate_occurrence(record)
    assert metadata["gbif_occurrence_validated"] == True
    assert metadata["gbif_similar_occurrences"] == 2
    assert result["gbif_similar_occurrence_count"] == 2


def test_validate_occurrence_disabled():
    gbif = GbifLookup(enable_occurrence_validation=False)
    record = {"scientificName": "Puma concolor"}

    result, metadata = gbif.validate_occurrence(record)
    assert metadata["gbif_occurrence_validation"] == "disabled"


def test_validate_occurrence_no_results(monkeypatch):
    gbif = GbifLookup(enable_occurrence_validation=True)
    record = {"scientificName": "Nonexistent species"}

    data = {"results": []}

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.validate_occurrence(record)
    assert metadata["gbif_occurrence_validated"] == False
    assert metadata["gbif_similar_occurrences"] == 0
    assert "no_similar_occurrences" in metadata["gbif_occurrence_issues"]


def test_low_confidence_taxonomy(monkeypatch):
    gbif = GbifLookup(min_confidence_score=0.9)  # High threshold
    record = {"scientificName": "Puma concolor"}

    data = {
        "scientificName": "Puma concolor",
        "confidence": 70,  # Below threshold (90)
        "matchType": "FUZZY",
    }

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.verify_taxonomy(record)
    assert metadata["gbif_taxonomy_verified"] == False
    assert "low_confidence_70" in metadata["gbif_issues"]
    assert metadata["gbif_match_type"] == "FUZZY"


def test_fuzzy_matching_disabled(monkeypatch):
    gbif = GbifLookup(enable_fuzzy_matching=False)
    record = {"scientificName": "Puma concolor"}

    data = {
        "scientificName": "Puma concolor",
        "confidence": 95,
        "matchType": "HIGHERRANK",  # This should be rejected when fuzzy matching is disabled
    }

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result, metadata = gbif.verify_taxonomy(record)
    assert "poor_match_higherrank" in metadata["gbif_issues"]


def test_distance_calculation():
    gbif = GbifLookup()

    # Test distance calculation between Ottawa and Montreal (approx 160 km)
    distance = gbif._calculate_distance(45.4215, -75.6972, 45.5017, -73.5673)
    assert 150 < distance < 170  # Approximate distance


def test_configuration_from_config():
    cfg = {
        "qc": {
            "gbif": {
                "species_match_endpoint": "https://example.org/species",
                "reverse_geocode_endpoint": "https://example.org/reverse",
                "occurrence_search_endpoint": "https://example.org/occurrence",
                "suggest_endpoint": "https://example.org/suggest",
                "timeout": 15.0,
                "retry_attempts": 5,
                "backoff_factor": 2.0,
                "cache_size": 500,
                "enable_fuzzy_matching": False,
                "min_confidence_score": 0.95,
                "enable_occurrence_validation": True,
            }
        }
    }

    gbif = GbifLookup.from_config(cfg)
    assert gbif.species_match_endpoint == "https://example.org/species"
    assert gbif.reverse_geocode_endpoint == "https://example.org/reverse"
    assert gbif.occurrence_search_endpoint == "https://example.org/occurrence"
    assert gbif.suggest_endpoint == "https://example.org/suggest"
    assert gbif.timeout == 15.0
    assert gbif.retry_attempts == 5
    assert gbif.backoff_factor == 2.0
    assert gbif.cache_size == 500
    assert gbif.enable_fuzzy_matching == False
    assert gbif.min_confidence_score == 0.95
    assert gbif.enable_occurrence_validation == True
