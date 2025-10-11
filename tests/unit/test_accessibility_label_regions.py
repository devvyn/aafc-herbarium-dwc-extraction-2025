"""
Unit tests for src/accessibility/label_regions.py

Tests label region classes for keyboard navigation and structured non-visual access.
"""

import pytest

from src.accessibility.label_regions import (
    BoundingBox,
    LabelRegion,
    SpecimenImageMetadata,
)


class TestBoundingBox:
    """Test BoundingBox class."""

    def test_create_bounding_box(self):
        """Test basic creation of BoundingBox."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)

        assert bbox.x == 120
        assert bbox.y == 340
        assert bbox.width == 280
        assert bbox.height == 45

    def test_center(self):
        """Test center point calculation."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)

        center_x, center_y = bbox.center()

        assert center_x == 125  # 100 + 50//2
        assert center_y == 215  # 200 + 30//2

    def test_contains_point_inside(self):
        """Test contains method with point inside bounding box."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)

        # Points inside
        assert bbox.contains(100, 200) is True  # Top-left corner
        assert bbox.contains(150, 230) is True  # Bottom-right corner
        assert bbox.contains(125, 215) is True  # Center
        assert bbox.contains(110, 210) is True  # Interior point

    def test_contains_point_outside(self):
        """Test contains method with point outside bounding box."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)

        # Points outside
        assert bbox.contains(99, 200) is False  # Left edge - 1
        assert bbox.contains(151, 230) is False  # Right edge + 1
        assert bbox.contains(100, 199) is False  # Top edge - 1
        assert bbox.contains(150, 231) is False  # Bottom edge + 1
        assert bbox.contains(0, 0) is False  # Far away

    def test_area(self):
        """Test area calculation."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)

        assert bbox.area() == 5000  # 100 * 50

    def test_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)

        result = bbox.to_dict()

        assert result == {"x": 120, "y": 340, "width": 280, "height": 45}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"x": 200, "y": 400, "width": 150, "height": 60}

        bbox = BoundingBox.from_dict(data)

        assert bbox.x == 200
        assert bbox.y == 400
        assert bbox.width == 150
        assert bbox.height == 60


class TestLabelRegion:
    """Test LabelRegion class."""

    def test_create_label_region(self):
        """Test basic creation of LabelRegion."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)
        region = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox,
            aria_label="Scientific name: Carex praticola, confidence 87%",
            keyboard_focus="1",
            ocr_engine="gpt-4o-mini",
        )

        assert region.field_name == "scientificName"
        assert region.text_content == "Carex praticola"
        assert region.confidence == 0.87
        assert region.bounding_box == bbox
        assert region.aria_label == "Scientific name: Carex praticola, confidence 87%"
        assert region.keyboard_focus == "1"
        assert region.ocr_engine == "gpt-4o-mini"

    def test_label_region_optional_ocr_engine(self):
        """Test LabelRegion with optional ocr_engine."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        region = LabelRegion(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.92,
            bounding_box=bbox,
            aria_label="Locality: Saskatchewan, confidence 92%",
            keyboard_focus="2",
        )

        assert region.ocr_engine is None

    def test_confidence_validation(self):
        """Test confidence range validation."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)

        # Valid confidences
        LabelRegion(
            field_name="test",
            text_content="test",
            confidence=0.0,
            bounding_box=bbox,
            aria_label="test",
            keyboard_focus="1",
        )
        LabelRegion(
            field_name="test",
            text_content="test",
            confidence=0.5,
            bounding_box=bbox,
            aria_label="test",
            keyboard_focus="1",
        )
        LabelRegion(
            field_name="test",
            text_content="test",
            confidence=1.0,
            bounding_box=bbox,
            aria_label="test",
            keyboard_focus="1",
        )

        # Invalid confidences
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            LabelRegion(
                field_name="test",
                text_content="test",
                confidence=-0.1,
                bounding_box=bbox,
                aria_label="test",
                keyboard_focus="1",
            )

        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            LabelRegion(
                field_name="test",
                text_content="test",
                confidence=1.1,
                bounding_box=bbox,
                aria_label="test",
                keyboard_focus="1",
            )

    def test_create_factory_method(self):
        """Test create factory method with auto-generated ARIA label."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)

        region = LabelRegion.create(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox,
            keyboard_focus="1",
            ocr_engine="gpt-4o-mini",
        )

        assert region.field_name == "scientificName"
        assert region.text_content == "Carex praticola"
        assert region.confidence == 0.87
        assert region.bounding_box == bbox
        assert region.keyboard_focus == "1"
        assert region.ocr_engine == "gpt-4o-mini"
        # Check auto-generated ARIA label
        assert "Scientific Name" in region.aria_label  # Friendly name (single space)
        assert "Carex praticola" in region.aria_label  # Text content
        assert "87%" in region.aria_label  # Percentage
        assert "high confidence" in region.aria_label  # Confidence level

    def test_create_confidence_levels(self):
        """Test create factory method with different confidence levels."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)

        # High confidence (>= 0.85)
        high = LabelRegion.create(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.92,
            bounding_box=bbox,
            keyboard_focus="1",
        )
        assert "high confidence" in high.aria_label

        # Medium confidence (>= 0.65)
        medium = LabelRegion.create(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.70,
            bounding_box=bbox,
            keyboard_focus="1",
        )
        assert "medium confidence" in medium.aria_label

        # Low confidence (< 0.65)
        low = LabelRegion.create(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.45,
            bounding_box=bbox,
            keyboard_focus="1",
        )
        assert "low confidence" in low.aria_label

    def test_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)
        region = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox,
            aria_label="Scientific name: Carex praticola, confidence 87%",
            keyboard_focus="1",
            ocr_engine="gpt-4o-mini",
        )

        result = region.to_dict()

        assert result == {
            "field_name": "scientificName",
            "text_content": "Carex praticola",
            "confidence": 0.87,
            "bounding_box": {"x": 120, "y": 340, "width": 280, "height": 45},
            "aria_label": "Scientific name: Carex praticola, confidence 87%",
            "keyboard_focus": "1",
            "ocr_engine": "gpt-4o-mini",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "field_name": "locality",
            "text_content": "Saskatchewan",
            "confidence": 0.92,
            "bounding_box": {"x": 200, "y": 500, "width": 150, "height": 40},
            "aria_label": "Locality: Saskatchewan, confidence 92%",
            "keyboard_focus": "2",
            "ocr_engine": "apple-vision",
        }

        region = LabelRegion.from_dict(data)

        assert region.field_name == "locality"
        assert region.text_content == "Saskatchewan"
        assert region.confidence == 0.92
        assert region.bounding_box.x == 200
        assert region.bounding_box.y == 500
        assert region.aria_label == "Locality: Saskatchewan, confidence 92%"
        assert region.keyboard_focus == "2"
        assert region.ocr_engine == "apple-vision"


class TestSpecimenImageMetadata:
    """Test SpecimenImageMetadata class."""

    def test_create_specimen_image_metadata(self):
        """Test basic creation of SpecimenImageMetadata."""
        bbox1 = BoundingBox(x=120, y=340, width=280, height=45)
        bbox2 = BoundingBox(x=200, y=500, width=150, height=40)

        region1 = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox1,
            aria_label="Scientific name: Carex praticola, confidence 87%",
            keyboard_focus="1",
        )
        region2 = LabelRegion(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.92,
            bounding_box=bbox2,
            aria_label="Locality: Saskatchewan, confidence 92%",
            keyboard_focus="2",
        )

        metadata = SpecimenImageMetadata(
            specimen_id="DSC_1162",
            alt_text="Herbarium specimen DSC_1162: Carex praticola collected by J. Smith in 1985",
            label_regions=[region1, region2],
            keyboard_navigation={"1": "scientificName", "2": "locality"},
        )

        assert metadata.specimen_id == "DSC_1162"
        assert (
            metadata.alt_text
            == "Herbarium specimen DSC_1162: Carex praticola collected by J. Smith in 1985"
        )
        assert len(metadata.label_regions) == 2
        assert metadata.label_regions[0] == region1
        assert metadata.label_regions[1] == region2
        assert metadata.keyboard_navigation == {"1": "scientificName", "2": "locality"}

    def test_get_region_by_key(self):
        """Test get_region_by_key method."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=50)
        bbox2 = BoundingBox(x=0, y=100, width=100, height=50)

        region1 = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox1,
            aria_label="test1",
            keyboard_focus="1",
        )
        region2 = LabelRegion(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.92,
            bounding_box=bbox2,
            aria_label="test2",
            keyboard_focus="2",
        )

        metadata = SpecimenImageMetadata(
            specimen_id="TEST",
            alt_text="Test specimen",
            label_regions=[region1, region2],
            keyboard_navigation={"1": "scientificName", "2": "locality"},
        )

        # Find existing regions
        found1 = metadata.get_region_by_key("1")
        assert found1 == region1
        assert found1.field_name == "scientificName"

        found2 = metadata.get_region_by_key("2")
        assert found2 == region2
        assert found2.field_name == "locality"

        # Key not found
        not_found = metadata.get_region_by_key("9")
        assert not_found is None

    def test_get_region_by_field(self):
        """Test get_region_by_field method."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=50)
        bbox2 = BoundingBox(x=0, y=100, width=100, height=50)

        region1 = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox1,
            aria_label="test1",
            keyboard_focus="1",
        )
        region2 = LabelRegion(
            field_name="locality",
            text_content="Saskatchewan",
            confidence=0.92,
            bounding_box=bbox2,
            aria_label="test2",
            keyboard_focus="2",
        )

        metadata = SpecimenImageMetadata(
            specimen_id="TEST",
            alt_text="Test specimen",
            label_regions=[region1, region2],
            keyboard_navigation={"1": "scientificName", "2": "locality"},
        )

        # Find existing regions
        found1 = metadata.get_region_by_field("scientificName")
        assert found1 == region1
        assert found1.keyboard_focus == "1"

        found2 = metadata.get_region_by_field("locality")
        assert found2 == region2
        assert found2.keyboard_focus == "2"

        # Field not found
        not_found = metadata.get_region_by_field("eventDate")
        assert not_found is None

    def test_create_from_extraction_basic(self):
        """Test create_from_extraction factory method without OCR results."""
        extraction_data = {
            "scientificName": "Carex praticola",
            "recordedBy": "J. Smith",
            "eventDate": "1985-06-15",
        }

        metadata = SpecimenImageMetadata.create_from_extraction(
            specimen_id="DSC_1162", extraction_data=extraction_data
        )

        assert metadata.specimen_id == "DSC_1162"
        assert "DSC_1162" in metadata.alt_text
        assert "Carex praticola" in metadata.alt_text
        assert "J. Smith" in metadata.alt_text
        assert "1985-06-15" in metadata.alt_text
        assert len(metadata.label_regions) == 0  # No OCR results provided
        assert metadata.keyboard_navigation == {}

    def test_create_from_extraction_with_ocr(self):
        """Test create_from_extraction factory method with OCR results."""
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
            },
            "locality": {
                "confidence": 0.92,
                "bounding_box": {"x": 200, "y": 500, "width": 150, "height": 40},
                "engine": "apple-vision",
            },
        }

        metadata = SpecimenImageMetadata.create_from_extraction(
            specimen_id="DSC_1162", extraction_data=extraction_data, ocr_results=ocr_results
        )

        assert metadata.specimen_id == "DSC_1162"
        assert len(metadata.label_regions) == 2  # scientificName + locality
        assert metadata.keyboard_navigation == {"1": "scientificName", "2": "locality"}

        # Check first region (scientificName)
        region1 = metadata.label_regions[0]
        assert region1.field_name == "scientificName"
        assert region1.text_content == "Carex praticola"
        assert region1.confidence == 0.87
        assert region1.bounding_box.x == 120
        assert region1.keyboard_focus == "1"
        assert region1.ocr_engine == "gpt-4o-mini"

        # Check second region (locality)
        region2 = metadata.label_regions[1]
        assert region2.field_name == "locality"
        assert region2.text_content == "Saskatchewan"
        assert region2.confidence == 0.92
        assert region2.bounding_box.x == 200
        assert region2.keyboard_focus == "2"
        assert region2.ocr_engine == "apple-vision"

    def test_create_from_extraction_field_priority(self):
        """Test that create_from_extraction respects field priority order."""
        extraction_data = {
            "scientificName": "Carex praticola",
            "locality": "Saskatchewan",
            "eventDate": "1985-06-15",
            "recordedBy": "J. Smith",
            "stateProvince": "SK",
            "country": "Canada",
            "habitat": "Grassland",
        }

        ocr_results = {
            field: {"confidence": 0.8, "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 50}}
            for field in extraction_data
        }

        metadata = SpecimenImageMetadata.create_from_extraction(
            specimen_id="TEST", extraction_data=extraction_data, ocr_results=ocr_results
        )

        # Check priority order: scientificName, locality, eventDate, recordedBy, stateProvince, country, habitat
        expected_order = [
            "scientificName",
            "locality",
            "eventDate",
            "recordedBy",
            "stateProvince",
            "country",
            "habitat",
        ]

        for idx, field in enumerate(expected_order, start=1):
            assert metadata.keyboard_navigation[str(idx)] == field
            region = metadata.get_region_by_key(str(idx))
            assert region.field_name == field

    def test_to_dict(self):
        """Test serialization to dictionary."""
        bbox = BoundingBox(x=120, y=340, width=280, height=45)
        region = LabelRegion(
            field_name="scientificName",
            text_content="Carex praticola",
            confidence=0.87,
            bounding_box=bbox,
            aria_label="Scientific name: Carex praticola, confidence 87%",
            keyboard_focus="1",
        )

        metadata = SpecimenImageMetadata(
            specimen_id="DSC_1162",
            alt_text="Herbarium specimen DSC_1162: Carex praticola",
            label_regions=[region],
            keyboard_navigation={"1": "scientificName"},
        )

        result = metadata.to_dict()

        assert result == {
            "specimen_id": "DSC_1162",
            "alt_text": "Herbarium specimen DSC_1162: Carex praticola",
            "label_regions": [
                {
                    "field_name": "scientificName",
                    "text_content": "Carex praticola",
                    "confidence": 0.87,
                    "bounding_box": {"x": 120, "y": 340, "width": 280, "height": 45},
                    "aria_label": "Scientific name: Carex praticola, confidence 87%",
                    "keyboard_focus": "1",
                    "ocr_engine": None,
                }
            ],
            "keyboard_navigation": {"1": "scientificName"},
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "specimen_id": "DSC_1162",
            "alt_text": "Herbarium specimen DSC_1162: Carex praticola",
            "label_regions": [
                {
                    "field_name": "scientificName",
                    "text_content": "Carex praticola",
                    "confidence": 0.87,
                    "bounding_box": {"x": 120, "y": 340, "width": 280, "height": 45},
                    "aria_label": "Scientific name: Carex praticola, confidence 87%",
                    "keyboard_focus": "1",
                    "ocr_engine": "gpt-4o-mini",
                }
            ],
            "keyboard_navigation": {"1": "scientificName"},
        }

        metadata = SpecimenImageMetadata.from_dict(data)

        assert metadata.specimen_id == "DSC_1162"
        assert metadata.alt_text == "Herbarium specimen DSC_1162: Carex praticola"
        assert len(metadata.label_regions) == 1
        assert metadata.label_regions[0].field_name == "scientificName"
        assert metadata.label_regions[0].text_content == "Carex praticola"
        assert metadata.keyboard_navigation == {"1": "scientificName"}
