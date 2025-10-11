"""
Unit tests for DwcRecord accessibility field integration (Phase 2A).

Tests that DwcRecord properly handles optional accessibility metadata
while maintaining backward compatibility with existing code.
"""

from dwc.schema import DwcRecord
from src.accessibility import (
    PresentationMetadata,
    QualityIndicator,
    SpecimenImageMetadata,
)


class TestDwcRecordAccessibilityFields:
    """Test DwcRecord with accessibility fields."""

    def test_create_record_without_accessibility_fields(self):
        """Test backward compatibility - record without accessibility fields."""
        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            recordedBy="J. Smith",
            eventDate="1985-06-15",
        )

        assert record.catalogNumber == "DSC_1162"
        assert record.scientificName == "Carex praticola"
        assert record.presentation_metadata is None
        assert record.quality_indicator is None
        assert record.image_metadata is None

    def test_create_record_with_accessibility_fields(self):
        """Test creating record with full accessibility metadata."""
        presentation_meta = PresentationMetadata(
            visual="✅ APPROVED",
            auditory="Approved - high quality specimen",
            textual="APPROVED",
            aria_label="Status: Approved, 87% quality",
        ).to_dict()

        quality_ind = QualityIndicator.from_score(0.87, context="specimen").to_dict()

        image_meta = {
            "specimen_id": "DSC_1162",
            "alt_text": "Herbarium specimen DSC_1162: Carex praticola",
            "label_regions": [],
            "keyboard_navigation": {},
        }

        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            presentation_metadata=presentation_meta,
            quality_indicator=quality_ind,
            image_metadata=image_meta,
        )

        assert record.catalogNumber == "DSC_1162"
        assert record.presentation_metadata == presentation_meta
        assert record.quality_indicator == quality_ind
        assert record.image_metadata == image_meta

    def test_to_dict_excludes_accessibility_fields(self):
        """Test that to_dict() excludes accessibility fields (CSV compatibility)."""
        presentation_meta = {"visual": "test", "auditory": "test"}
        quality_ind = {"score": 0.87, "level": "approved"}
        image_meta = {"specimen_id": "TEST"}

        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            presentation_metadata=presentation_meta,
            quality_indicator=quality_ind,
            image_metadata=image_meta,
        )

        result = record.to_dict()

        # Accessibility fields should NOT be in to_dict() output
        assert "presentation_metadata" not in result
        assert "quality_indicator" not in result
        assert "image_metadata" not in result

        # Darwin Core fields should be present
        assert "catalogNumber" in result
        assert "scientificName" in result
        assert result["catalogNumber"] == "DSC_1162"
        assert result["scientificName"] == "Carex praticola"

    def test_to_dict_with_accessibility_includes_all_fields(self):
        """Test that to_dict_with_accessibility() includes accessibility fields."""
        presentation_meta = {"visual": "test", "auditory": "test"}
        quality_ind = {"score": 0.87, "level": "approved"}
        image_meta = {"specimen_id": "TEST"}

        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            presentation_metadata=presentation_meta,
            quality_indicator=quality_ind,
            image_metadata=image_meta,
        )

        result = record.to_dict_with_accessibility()

        # All accessibility fields should be present
        assert result["presentation_metadata"] == presentation_meta
        assert result["quality_indicator"] == quality_ind
        assert result["image_metadata"] == image_meta

        # Darwin Core fields should also be present
        assert result["catalogNumber"] == "DSC_1162"
        assert result["scientificName"] == "Carex praticola"

    def test_to_dict_with_accessibility_omits_none_fields(self):
        """Test that to_dict_with_accessibility() omits None accessibility fields."""
        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            presentation_metadata=None,  # Explicitly None
            quality_indicator={"score": 0.87, "level": "approved"},
            image_metadata=None,  # Explicitly None
        )

        result = record.to_dict_with_accessibility()

        # Only non-None accessibility fields should be present
        assert "presentation_metadata" not in result
        assert "quality_indicator" in result
        assert "image_metadata" not in result

    def test_integration_with_quality_indicator_class(self):
        """Test integration with QualityIndicator factory method."""
        # Create quality indicator using factory method
        quality_ind = QualityIndicator.from_score(0.68, context="specimen")

        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            quality_indicator=quality_ind.to_dict(),
        )

        # Verify quality indicator data is accessible
        assert record.quality_indicator is not None
        assert record.quality_indicator["score"] == 0.68
        assert record.quality_indicator["level"] == "medium"
        assert "visual" in record.quality_indicator
        assert "auditory" in record.quality_indicator

    def test_integration_with_specimen_image_metadata(self):
        """Test integration with SpecimenImageMetadata factory method."""
        extraction_data = {
            "scientificName": "Carex praticola",
            "locality": "Saskatchewan",
            "eventDate": "1985-06-15",
        }

        ocr_results = {
            "scientificName": {
                "confidence": 0.87,
                "bounding_box": {"x": 120, "y": 340, "width": 280, "height": 45},
                "engine": "gpt-4o-mini",
            }
        }

        # Create metadata using factory method
        specimen_meta = SpecimenImageMetadata.create_from_extraction(
            specimen_id="DSC_1162", extraction_data=extraction_data, ocr_results=ocr_results
        )

        record = DwcRecord(
            catalogNumber="DSC_1162",
            scientificName="Carex praticola",
            locality="Saskatchewan",
            eventDate="1985-06-15",
            image_metadata=specimen_meta.to_dict(),
        )

        # Verify image metadata is accessible
        assert record.image_metadata is not None
        assert record.image_metadata["specimen_id"] == "DSC_1162"
        assert "alt_text" in record.image_metadata
        assert "label_regions" in record.image_metadata
        assert "keyboard_navigation" in record.image_metadata
