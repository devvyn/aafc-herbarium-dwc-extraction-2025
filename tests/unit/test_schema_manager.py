"""Tests for schema management functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from dwc.schema_manager import SchemaManager
from dwc.schema import SchemaInfo, SchemaType


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provide a temporary cache directory for testing."""
    return tmp_path / "test_cache"


@pytest.fixture
def mock_schema_info():
    """Provide a mock SchemaInfo object."""
    return SchemaInfo(
        name="test_schema",
        version="1.0",
        namespace="http://test.org/terms/",
        terms=["term1", "term2", "term3"],
        schema_type=SchemaType.DWC,
        source_url="http://test.org/schema.xsd",
        last_updated=datetime.now(),
    )


def test_schema_manager_init(temp_cache_dir):
    """Test SchemaManager initialization."""
    manager = SchemaManager(
        cache_dir=temp_cache_dir,
        update_interval_days=7,
        preferred_schemas=["dwc_simple"],
    )

    assert manager.cache_dir == temp_cache_dir
    assert manager.update_interval == timedelta(days=7)
    assert manager.preferred_schemas == ["dwc_simple"]
    assert temp_cache_dir.exists()


def test_schema_manager_default_init():
    """Test SchemaManager with default parameters."""
    manager = SchemaManager()

    assert manager.cache_dir == Path("config/schemas/cache")
    assert manager.update_interval == timedelta(days=30)
    assert manager.preferred_schemas == ["dwc_simple", "abcd_206"]


@patch("dwc.schema_manager.fetch_official_schemas")
def test_get_schemas_force_update(mock_fetch, temp_cache_dir, mock_schema_info):
    """Test forcing schema update."""
    mock_fetch.return_value = {"test_schema": mock_schema_info}

    manager = SchemaManager(cache_dir=temp_cache_dir)
    schemas = manager.get_schemas(force_update=True)

    assert "test_schema" in schemas
    assert schemas["test_schema"] == mock_schema_info
    mock_fetch.assert_called_once()


def test_get_schema_info(temp_cache_dir, mock_schema_info, monkeypatch):
    """Test getting specific schema information."""
    manager = SchemaManager(cache_dir=temp_cache_dir)

    # Mock get_schemas to return test data
    monkeypatch.setattr(manager, "get_schemas", lambda: {"test_schema": mock_schema_info})

    info = manager.get_schema_info("test_schema")
    assert info == mock_schema_info

    info = manager.get_schema_info("nonexistent")
    assert info is None


def test_list_available_schemas(temp_cache_dir, mock_schema_info, monkeypatch):
    """Test listing available schemas."""
    manager = SchemaManager(cache_dir=temp_cache_dir)

    # Mock get_schemas to return test data
    monkeypatch.setattr(
        manager, "get_schemas", lambda: {"schema1": mock_schema_info, "schema2": mock_schema_info}
    )

    schemas = manager.list_available_schemas()
    assert set(schemas) == {"schema1", "schema2"}


@patch("dwc.schema_manager.load_schema_terms_from_official_sources")
def test_get_schema_terms(mock_load_terms, temp_cache_dir):
    """Test getting schema terms."""
    mock_load_terms.return_value = ["term1", "term2", "term3"]

    manager = SchemaManager(cache_dir=temp_cache_dir)

    # Test with default schemas
    terms = manager.get_schema_terms()
    assert terms == ["term1", "term2", "term3"]
    mock_load_terms.assert_called_with(["dwc_simple", "abcd_206"])

    # Test with specific schemas
    terms = manager.get_schema_terms(["custom_schema"])
    mock_load_terms.assert_called_with(["custom_schema"])


@patch("dwc.schema_manager.validate_schema_compatibility")
def test_validate_terms(mock_validate, temp_cache_dir):
    """Test term validation."""
    mock_validate.return_value = {
        "valid": ["term1", "term2"],
        "invalid": ["term3"],
        "deprecated": [],
    }

    manager = SchemaManager(cache_dir=temp_cache_dir)
    result = manager.validate_terms(["term1", "term2", "term3"])

    assert result["valid"] == ["term1", "term2"]
    assert result["invalid"] == ["term3"]
    mock_validate.assert_called_with(["term1", "term2", "term3"], ["dwc_simple", "abcd_206"])


@patch("dwc.schema_manager.auto_generate_mappings_from_schemas")
def test_generate_mappings(mock_generate, temp_cache_dir):
    """Test mapping generation."""
    mock_generate.return_value = {"field1": "term1", "field2": "term2"}

    manager = SchemaManager(cache_dir=temp_cache_dir)
    mappings = manager.generate_mappings()

    assert mappings == {"field1": "term1", "field2": "term2"}
    mock_generate.assert_called_with(["dwc_simple", "abcd_206"], True, 0.6)


@patch("dwc.schema_manager.suggest_mapping_improvements")
def test_suggest_mappings(mock_suggest, temp_cache_dir):
    """Test mapping suggestions."""
    mock_suggest.return_value = {"unmapped_field": ["suggestion1", "suggestion2"]}

    manager = SchemaManager(cache_dir=temp_cache_dir)
    suggestions = manager.suggest_mappings(["unmapped_field"])

    assert suggestions == {"unmapped_field": ["suggestion1", "suggestion2"]}
    mock_suggest.assert_called_with(["unmapped_field"], ["dwc_simple", "abcd_206"], 0.6)


def test_get_schema_compatibility_report(temp_cache_dir, monkeypatch):
    """Test schema compatibility reporting."""
    source_schema = SchemaInfo(
        name="source",
        version="1.0",
        namespace="http://source.org/",
        terms=["term1", "term2", "term3"],
        schema_type=SchemaType.DWC,
    )

    target_schema = SchemaInfo(
        name="target",
        version="1.0",
        namespace="http://target.org/",
        terms=["term2", "term3", "term4"],
        schema_type=SchemaType.DWC,
    )

    manager = SchemaManager(cache_dir=temp_cache_dir)

    # Mock get_schemas to return test data
    monkeypatch.setattr(
        manager, "get_schemas", lambda: {"source": source_schema, "target": target_schema}
    )

    report = manager.get_schema_compatibility_report("source", ["target"])

    assert report["source_schema"] == "source"
    assert report["source_term_count"] == 3
    assert "target" in report["target_schemas"]

    target_report = report["target_schemas"]["target"]
    assert target_report["overlapping_terms"] == 2  # term2, term3
    assert target_report["compatibility_score"] == 2 / 3  # 2 out of 3 source terms
    assert target_report["unique_to_source"] == 1  # term1
    assert target_report["unique_to_target"] == 1  # term4


def test_get_status(temp_cache_dir, monkeypatch):
    """Test status reporting."""
    manager = SchemaManager(cache_dir=temp_cache_dir, update_interval_days=15)

    # Mock get_schemas to return test data
    monkeypatch.setattr(manager, "get_schemas", lambda: {"schema1": Mock(), "schema2": Mock()})

    status = manager.get_status()

    assert status["cache_dir"] == str(temp_cache_dir)
    assert status["update_interval_days"] == 15
    assert status["preferred_schemas"] == ["dwc_simple", "abcd_206"]
    assert status["schema_count"] == 2
    assert set(status["available_schemas"]) == {"schema1", "schema2"}


def test_metadata_persistence(temp_cache_dir, mock_schema_info):
    """Test metadata saving and loading."""
    manager = SchemaManager(cache_dir=temp_cache_dir)

    # Save metadata
    metadata = {
        "last_update": "2023-01-01T12:00:00",
        "schemas": {"test": {"name": "test", "version": "1.0"}},
    }
    manager._save_metadata(metadata)

    # Load metadata
    loaded = manager._load_metadata()
    assert loaded["last_update"] == "2023-01-01T12:00:00"
    assert "test" in loaded["schemas"]


@pytest.mark.parametrize(
    "days_old,should_update",
    [
        (10, False),  # Recent, should not update
        (40, True),  # Old, should update
    ],
)
def test_should_update_schemas(temp_cache_dir, days_old, should_update):
    """Test schema update timing logic."""
    manager = SchemaManager(cache_dir=temp_cache_dir, update_interval_days=30)

    # Set up metadata with specific age
    old_date = datetime.now() - timedelta(days=days_old)
    metadata = {"last_update": old_date.isoformat()}
    manager._save_metadata(metadata)

    assert manager._should_update_schemas() == should_update


class TestSchemaManagerIntegration:
    """Integration tests for SchemaManager."""

    def test_full_workflow(self, temp_cache_dir):
        """Test a complete workflow of schema management."""
        with patch("dwc.schema_manager.fetch_official_schemas") as mock_fetch:
            # Mock schema data
            mock_schema = SchemaInfo(
                name="dwc_simple",
                version="1.0",
                namespace="http://rs.tdwg.org/dwc/terms/",
                terms=["catalogNumber", "scientificName", "eventDate"],
                schema_type=SchemaType.DWC,
                source_url="http://rs.tdwg.org/dwc/xsd/tdwg_dwc_simple.xsd",
            )
            mock_fetch.return_value = {"dwc_simple": mock_schema}

            manager = SchemaManager(cache_dir=temp_cache_dir)

            # Get schemas (should fetch and cache)
            schemas = manager.get_schemas()
            assert "dwc_simple" in schemas

            # Check that metadata was saved
            metadata = manager._load_metadata()
            assert "last_update" in metadata
            assert "dwc_simple" in metadata["schemas"]

            # Second call should use cache
            mock_fetch.reset_mock()
            schemas = manager.get_schemas()
            mock_fetch.assert_not_called()  # Should not fetch again

            # Force update should fetch again
            schemas = manager.get_schemas(force_update=True)
            mock_fetch.assert_called_once()
