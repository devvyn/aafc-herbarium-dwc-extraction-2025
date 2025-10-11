"""
Structured label region metadata for non-visual navigation of specimen images.

Enables keyboard users and screen reader users to navigate specimen labels
semantically rather than spatially, supporting information parity for users
with different sensory configurations.

Constitutional Reference: Core Principle VI - Information Parity and Inclusive Design
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BoundingBox:
    """
    Bounding box coordinates for a label region in an image.

    Coordinates are in pixels, origin at top-left of image.

    Attributes:
        x: Left edge x-coordinate
        y: Top edge y-coordinate
        width: Width in pixels
        height: Height in pixels
    """

    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: Dict) -> "BoundingBox":
        """Create from dictionary (deserialization)."""
        return cls(x=data["x"], y=data["y"], width=data["width"], height=data["height"])

    def center(self) -> tuple[int, int]:
        """Calculate center point of bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, x: int, y: int) -> bool:
        """Check if point (x, y) is within this bounding box."""
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def area(self) -> int:
        """Calculate area of bounding box in square pixels."""
        return self.width * self.height


@dataclass
class LabelRegion:
    """
    Structured representation of a label region on a specimen image.

    Enables non-visual navigation by providing:
    - Semantic identification (what Darwin Core field)
    - Text content (extracted value)
    - Spatial location (for visual highlighting)
    - Confidence score (extraction quality)
    - Keyboard navigation (shortcut key)

    Example:
        >>> region = LabelRegion(
        ...     field_name="scientificName",
        ...     text_content="Carex praticola",
        ...     confidence=0.87,
        ...     bounding_box=BoundingBox(x=120, y=340, w=280, h=45),
        ...     aria_label="Scientific name: Carex praticola, confidence 87%",
        ...     keyboard_focus="1"
        ... )
        >>> # User presses '1' key -> viewport pans to this region
        >>> # Screen reader announces: "Scientific name: Carex praticola, confidence 87%"
    """

    field_name: str  # Darwin Core field (e.g., "scientificName")
    text_content: str  # Extracted text from this region
    confidence: float  # Extraction confidence (0.0-1.0)
    bounding_box: BoundingBox  # Spatial location in image
    aria_label: str  # Screen reader announcement
    keyboard_focus: str  # Keyboard shortcut (e.g., "1" for first region)
    ocr_engine: Optional[str] = None  # Which OCR engine extracted this

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "field_name": self.field_name,
            "text_content": self.text_content,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict(),
            "aria_label": self.aria_label,
            "keyboard_focus": self.keyboard_focus,
            "ocr_engine": self.ocr_engine,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "LabelRegion":
        """Create from dictionary (deserialization)."""
        return cls(
            field_name=data["field_name"],
            text_content=data["text_content"],
            confidence=data["confidence"],
            bounding_box=BoundingBox.from_dict(data["bounding_box"]),
            aria_label=data["aria_label"],
            keyboard_focus=data["keyboard_focus"],
            ocr_engine=data.get("ocr_engine"),
        )

    @classmethod
    def create(
        cls,
        field_name: str,
        text_content: str,
        confidence: float,
        bounding_box: BoundingBox,
        keyboard_focus: str,
        ocr_engine: Optional[str] = None,
    ) -> "LabelRegion":
        """
        Create label region with auto-generated ARIA label.

        Args:
            field_name: Darwin Core field name
            text_content: Extracted text
            confidence: Confidence score (0.0-1.0)
            bounding_box: Spatial location
            keyboard_focus: Keyboard shortcut
            ocr_engine: Optional OCR engine identifier

        Returns:
            LabelRegion with auto-generated aria_label
        """
        # Generate human-friendly field name
        friendly_name = field_name.replace("_", " ").replace("Name", " name").title()

        # Generate ARIA label with context
        if confidence >= 0.85:
            confidence_text = "high confidence"
        elif confidence >= 0.65:
            confidence_text = "medium confidence"
        else:
            confidence_text = "low confidence"

        aria_label = f"{friendly_name}: {text_content}, {confidence:.0%} {confidence_text}"

        return cls(
            field_name=field_name,
            text_content=text_content,
            confidence=confidence,
            bounding_box=bounding_box,
            aria_label=aria_label,
            keyboard_focus=keyboard_focus,
            ocr_engine=ocr_engine,
        )


@dataclass
class SpecimenImageMetadata:
    """
    Complete accessibility metadata for a specimen image.

    Combines:
    - Alt text (for screen readers when image not visible)
    - Label regions (for structured navigation)
    - Keyboard navigation map (which keys jump where)

    Example:
        >>> metadata = SpecimenImageMetadata(
        ...     specimen_id="DSC_1162",
        ...     alt_text="Herbarium specimen DSC_1162: Carex praticola collected by J. Smith in 1985",
        ...     label_regions=[region1, region2, region3],
        ...     keyboard_navigation={
        ...         "1": "scientificName",
        ...         "2": "locality",
        ...         "3": "eventDate"
        ...     }
        ... )
    """

    specimen_id: str
    alt_text: str  # Full image description for screen readers
    label_regions: List[LabelRegion]
    keyboard_navigation: Dict[str, str]  # key -> field_name mapping

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "specimen_id": self.specimen_id,
            "alt_text": self.alt_text,
            "label_regions": [r.to_dict() for r in self.label_regions],
            "keyboard_navigation": self.keyboard_navigation,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SpecimenImageMetadata":
        """Create from dictionary (deserialization)."""
        return cls(
            specimen_id=data["specimen_id"],
            alt_text=data["alt_text"],
            label_regions=[LabelRegion.from_dict(r) for r in data["label_regions"]],
            keyboard_navigation=data["keyboard_navigation"],
        )

    def get_region_by_key(self, key: str) -> Optional[LabelRegion]:
        """Get label region by keyboard shortcut."""
        for region in self.label_regions:
            if region.keyboard_focus == key:
                return region
        return None

    def get_region_by_field(self, field_name: str) -> Optional[LabelRegion]:
        """Get label region by Darwin Core field name."""
        for region in self.label_regions:
            if region.field_name == field_name:
                return region
        return None

    @classmethod
    def create_from_extraction(
        cls,
        specimen_id: str,
        extraction_data: Dict,
        ocr_results: Optional[Dict] = None,
    ) -> "SpecimenImageMetadata":
        """
        Create metadata from extraction results and optional OCR bounding boxes.

        Args:
            specimen_id: Specimen identifier
            extraction_data: Darwin Core extraction results
            ocr_results: Optional OCR bounding box data

        Returns:
            SpecimenImageMetadata with structured regions
        """
        # Generate alt text from extraction data
        scientific_name = extraction_data.get("scientificName", "Unknown species")
        recorded_by = extraction_data.get("recordedBy", "Unknown collector")
        event_date = extraction_data.get("eventDate", "Unknown date")

        alt_text = f"Herbarium specimen {specimen_id}: {scientific_name} collected by {recorded_by} in {event_date}"

        # Create label regions from OCR results if available
        label_regions = []
        keyboard_navigation = {}

        if ocr_results:
            # Map Darwin Core fields to keyboard shortcuts (priority order)
            field_priority = [
                "scientificName",
                "locality",
                "eventDate",
                "recordedBy",
                "stateProvince",
                "country",
                "habitat",
            ]

            for idx, field_name in enumerate(field_priority, start=1):
                if field_name in extraction_data and field_name in ocr_results:
                    ocr_data = ocr_results[field_name]
                    key = str(idx)

                    region = LabelRegion.create(
                        field_name=field_name,
                        text_content=extraction_data[field_name],
                        confidence=ocr_data.get("confidence", 0.5),
                        bounding_box=BoundingBox.from_dict(
                            ocr_data.get("bounding_box", {"x": 0, "y": 0, "width": 0, "height": 0})
                        ),
                        keyboard_focus=key,
                        ocr_engine=ocr_data.get("engine"),
                    )

                    label_regions.append(region)
                    keyboard_navigation[key] = field_name

        return cls(
            specimen_id=specimen_id,
            alt_text=alt_text,
            label_regions=label_regions,
            keyboard_navigation=keyboard_navigation,
        )
