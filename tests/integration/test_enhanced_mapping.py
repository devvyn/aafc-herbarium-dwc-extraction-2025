"""Integration tests for enhanced schema and mapping functionality."""

import pytest
from unittest.mock import patch

from dwc import (
    SchemaManager,
    configure_dynamic_mappings,
    map_ocr_to_dwc,
    auto_generate_mappings_from_schemas,
    validate_mapping_against_schemas,
    suggest_mapping_improvements,
)
from dwc.schema import SchemaInfo, SchemaType


@pytest.fixture
def mock_dwc_schema():
    """Mock Darwin Core schema for testing."""
    return SchemaInfo(
        name="dwc_simple",
        version="1.0",
        namespace="http://rs.tdwg.org/dwc/terms/",
        terms=[
            "catalogNumber",
            "scientificName",
            "eventDate",
            "recordedBy",
            "locality",
            "decimalLatitude",
            "decimalLongitude",
            "family",
            "genus",
            "country",
            "stateProvince",
        ],
        schema_type=SchemaType.DWC,
        source_url="http://rs.tdwg.org/dwc/xsd/tdwg_dwc_simple.xsd",
    )


@pytest.fixture
def mock_abcd_schema():
    """Mock ABCD schema for testing."""
    return SchemaInfo(
        name="abcd_206",
        version="2.06",
        namespace="http://www.bgbm.org/TDWG/2005/ABCD/",
        terms=[
            "catalogNumber",
            "scientificName",
            "gatheringDate",
            "gatheringAgent",
            "locality",
            "latitude",
            "longitude",
            "higherTaxonName",
            "country",
            "province",
        ],
        schema_type=SchemaType.ABCD,
        source_url="https://abcd.tdwg.org/xml/documentation/abcd_2.06.xsd",
    )


class TestEnhancedMapping:
    """Test enhanced mapping functionality."""

    @pytest.mark.skip(
        reason="Feature not implemented: auto_generate_mappings_from_schemas fuzzy matching"
    )
    @patch("dwc.mapper.fetch_official_schemas")
    def test_auto_generate_mappings(self, mock_fetch, mock_dwc_schema):
        """Test automatic mapping generation from schemas."""
        mock_fetch.return_value = {"dwc_simple": mock_dwc_schema}

        mappings = auto_generate_mappings_from_schemas(
            schema_names=["dwc_simple"], include_fuzzy=True
        )

        # Should include case variations
        assert "catalognumber" in mappings
        assert mappings["catalognumber"] == "catalogNumber"
        assert "CATALOGNUMBER" in mappings
        assert mappings["CATALOGNUMBER"] == "catalogNumber"

        # Should include common field names
        assert "lat" in mappings
        assert mappings["lat"] == "decimalLatitude"
        assert "scientific_name" in mappings
        assert mappings["scientific_name"] == "scientificName"

    @patch("dwc.mapper.fetch_official_schemas")
    def test_configure_dynamic_mappings(self, mock_fetch, mock_dwc_schema):
        """Test configuration of dynamic mappings."""
        mock_fetch.return_value = {"dwc_simple": mock_dwc_schema}

        configure_dynamic_mappings(schema_names=["dwc_simple"])

        # Test that dynamic mappings work in OCR mapping
        ocr_output = {
            "barcode": "ABC123",  # Should map via rules
            "lat": "45.5",  # Should map via dynamic mappings
            "scientific_name": "Plantus testicus",  # Should map via dynamic mappings
        }

        record = map_ocr_to_dwc(ocr_output)

        assert record.catalogNumber == "ABC123"
        assert record.decimalLatitude == "45.5"
        assert record.scientificName == "Plantus testicus"

    @pytest.mark.skip(reason="Feature not implemented: validate_mapping_against_schemas")
    @patch("dwc.mapper.fetch_official_schemas")
    def test_validate_mapping_against_schemas(self, mock_fetch, mock_dwc_schema):
        """Test validation of mapped records against schemas."""
        mock_fetch.return_value = {"dwc_simple": mock_dwc_schema}

        # Create a record with mixed valid/invalid fields
        record = map_ocr_to_dwc(
            {
                "catalogNumber": "ABC123",  # Valid
                "scientificName": "Test sp.",  # Valid
                "invalidField": "value",  # Invalid
            }
        )

        validation_result = validate_mapping_against_schemas(record, target_schemas=["dwc_simple"])

        assert validation_result["validation_passed"] is False
        assert "invalidField" in validation_result["invalid_field_names"]
        assert validation_result["valid_fields"] >= 2  # At least catalogNumber and scientificName

    @pytest.mark.skip(reason="Feature not implemented: suggest_mapping_improvements")
    @patch("dwc.mapper.fetch_official_schemas")
    def test_suggest_mapping_improvements(self, mock_fetch, mock_dwc_schema):
        """Test mapping suggestions for unmapped fields."""
        mock_fetch.return_value = {"dwc_simple": mock_dwc_schema}

        unmapped_fields = [
            "collector",  # Should suggest recordedBy
            "species",  # Should suggest scientificName
            "collection_date",  # Should suggest eventDate
            "latitude",  # Should suggest decimalLatitude
        ]

        suggestions = suggest_mapping_improvements(
            unmapped_fields, target_schemas=["dwc_simple"], similarity_threshold=0.5
        )

        assert "collector" in suggestions
        assert "recordedBy" in suggestions["collector"]

        assert "species" in suggestions
        assert "scientificName" in suggestions["species"]

        assert "latitude" in suggestions
        assert "decimalLatitude" in suggestions["latitude"]


class TestSchemaManagerIntegration:
    """Test SchemaManager integration with mapping system."""

    @pytest.mark.skip(reason="Feature not implemented: SchemaManager.configure_dynamic_mappings")
    def test_complete_workflow(self, tmp_path, mock_dwc_schema, mock_abcd_schema):
        """Test complete workflow from schema management to mapping."""
        cache_dir = tmp_path / "cache"

        with patch("dwc.schema_manager.fetch_official_schemas") as mock_fetch:
            mock_fetch.return_value = {
                "dwc_simple": mock_dwc_schema,
                "abcd_206": mock_abcd_schema,
            }

            # Initialize schema manager
            manager = SchemaManager(
                cache_dir=cache_dir, preferred_schemas=["dwc_simple", "abcd_206"]
            )

            # Get schemas
            schemas = manager.get_schemas()
            assert len(schemas) == 2

            # Generate mappings
            mappings = manager.generate_mappings()
            assert len(mappings) > 0

            # Configure dynamic mappings
            manager.configure_dynamic_mappings()

            # Test mapping with dynamic configuration
            ocr_output = {
                "barcode": "XYZ789",
                "species": "Testus dynamicus",
                "collector": "Dr. Test",
                "collection_date": "2023-05-15",
                "lat": "50.0",
                "long": "-100.0",
            }

            record = map_ocr_to_dwc(ocr_output)

            # Verify mappings worked
            assert record.catalogNumber == "XYZ789"
            assert record.scientificName == "Testus dynamicus"
            assert record.recordedBy == "Dr. Test"
            assert record.eventDate == "2023-05-15"
            assert record.decimalLatitude == "50.0"
            assert record.decimalLongitude == "-100.0"

            # Validate the result
            validation = manager.validate_terms(
                list(record.to_dict().keys()), target_schemas=["dwc_simple"]
            )

            assert len(validation["invalid"]) == 0

    def test_schema_compatibility_reporting(self, tmp_path, mock_dwc_schema, mock_abcd_schema):
        """Test schema compatibility reporting."""
        cache_dir = tmp_path / "cache"

        with patch("dwc.schema_manager.fetch_official_schemas") as mock_fetch:
            mock_fetch.return_value = {
                "dwc_simple": mock_dwc_schema,
                "abcd_206": mock_abcd_schema,
            }

            manager = SchemaManager(cache_dir=cache_dir)

            # Generate compatibility report
            report = manager.get_schema_compatibility_report("dwc_simple", ["abcd_206"])

            assert report["source_schema"] == "dwc_simple"
            assert "abcd_206" in report["target_schemas"]

            abcd_report = report["target_schemas"]["abcd_206"]
            # Should have some overlap (catalogNumber, scientificName, locality, country)
            assert abcd_report["overlapping_terms"] > 0
            assert abcd_report["compatibility_score"] > 0.0
            assert abcd_report["unique_to_source"] > 0
            assert abcd_report["unique_to_target"] > 0

    @pytest.mark.skip(reason="Feature not implemented: SchemaManager.suggest_mappings")
    def test_mapping_suggestions_workflow(self, tmp_path, mock_dwc_schema):
        """Test workflow for getting mapping suggestions."""
        cache_dir = tmp_path / "cache"

        with patch("dwc.schema_manager.fetch_official_schemas") as mock_fetch:
            mock_fetch.return_value = {"dwc_simple": mock_dwc_schema}

            manager = SchemaManager(cache_dir=cache_dir)

            # Simulate unmapped fields from OCR output
            unmapped_fields = [
                "specimen_id",  # Similar to catalogNumber
                "taxon",  # Similar to scientificName
                "when_collected",  # Similar to eventDate
                "who_collected",  # Similar to recordedBy
                "where",  # Similar to locality
            ]

            suggestions = manager.suggest_mappings(unmapped_fields)

            # Should get suggestions for most fields
            assert len(suggestions) > 0

            # Check some specific suggestions
            if "specimen_id" in suggestions:
                assert "catalogNumber" in suggestions["specimen_id"]

            if "taxon" in suggestions:
                assert "scientificName" in suggestions["taxon"]


class TestErrorHandling:
    """Test error handling in enhanced mapping functionality."""

    @pytest.mark.skip(reason="Feature not implemented: auto_generate_mappings_from_schemas")
    @patch("dwc.mapper.fetch_official_schemas")
    def test_mapping_with_no_schemas(self, mock_fetch):
        """Test mapping behavior when no schemas are available."""
        mock_fetch.return_value = {}

        # Should not raise an exception
        mappings = auto_generate_mappings_from_schemas()
        assert mappings == {}

        # OCR mapping should still work with existing rules
        record = map_ocr_to_dwc({"barcode": "ABC123"})
        assert record.catalogNumber == "ABC123"

    @pytest.mark.skip(reason="Feature not implemented: suggest_mapping_improvements error handling")
    @patch("dwc.mapper.fetch_official_schemas")
    def test_validation_with_schema_errors(self, mock_fetch):
        """Test validation when schema fetching fails."""
        mock_fetch.side_effect = Exception("Network error")

        # Should not raise an exception
        suggestions = suggest_mapping_improvements(["test_field"])
        assert suggestions == {}

    def test_schema_manager_with_invalid_cache(self, tmp_path):
        """Test SchemaManager behavior with corrupted cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create corrupted metadata file
        metadata_file = cache_dir / "schema_metadata.json"
        metadata_file.write_text("invalid json content")

        # Should handle corrupted metadata gracefully
        manager = SchemaManager(cache_dir=cache_dir)
        metadata = manager._load_metadata()
        assert metadata == {}  # Should return empty dict on error
