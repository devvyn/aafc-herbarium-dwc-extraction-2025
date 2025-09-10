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

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result = gbif.verify_taxonomy(record)

    assert result["taxonKey"] == "value_taxonKey"
    assert result["acceptedTaxonKey"] == "value_acceptedTaxonKey"
    for field in set(TAXONOMY_FIELDS) - {"taxonKey", "acceptedTaxonKey"}:
        assert result[field] == data[field]


def test_verify_taxonomy_error(monkeypatch):
    gbif = GbifLookup()
    record = {"scientificName": "Puma concolor"}

    def raise_error(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise URLError("failure")

    monkeypatch.setattr(gbif_module, "urlopen", raise_error)
    result = gbif.verify_taxonomy(record)
    assert result == record
    assert result is not record


def test_verify_taxonomy_missing_fields(monkeypatch):
    gbif = GbifLookup()
    record: dict = {}

    def raise_if_called(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(gbif_module, "urlopen", raise_if_called)
    result = gbif.verify_taxonomy(record)

    assert result == record
    assert result is not record


def test_verify_locality_success(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    data = [{field: f"value_{field}" for field in LOCALITY_FIELDS}]

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response(data))

    result = gbif.verify_locality(record)
    for field in LOCALITY_FIELDS:
        assert result[field] == data[0][field]


def test_verify_locality_error(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    def raise_error(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise URLError("failure")

    monkeypatch.setattr(gbif_module, "urlopen", raise_error)
    result = gbif.verify_locality(record)
    assert result == record
    assert result is not record


def test_verify_locality_missing_coords(monkeypatch):
    gbif = GbifLookup()
    record: dict = {}

    def raise_if_called(url, timeout=None):  # pragma: no cover - executed via monkeypatch
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(gbif_module, "urlopen", raise_if_called)
    result = gbif.verify_locality(record)

    assert result == record
    assert result is not record


def test_verify_locality_empty_response(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}

    monkeypatch.setattr(gbif_module, "urlopen", lambda url, timeout=None: _mock_response([]))
    result = gbif.verify_locality(record)
    assert result == record and result is not record

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

    monkeypatch.setattr(
        gbif_module, "urlopen", lambda url, timeout=None: _bad_json_response()
    )
    result = gbif.verify_taxonomy(record)
    assert result == record and result is not record


def test_verify_locality_invalid_json(monkeypatch):
    gbif = GbifLookup()
    record = {"decimalLatitude": 45.0, "decimalLongitude": -75.0}
    monkeypatch.setattr(
        gbif_module, "urlopen", lambda url, timeout=None: _bad_json_response()
    )
    result = gbif.verify_locality(record)
    assert result == record and result is not record
