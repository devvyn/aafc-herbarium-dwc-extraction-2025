"""Spatial zone detection for herbarium label text.

This module implements coarse 9-zone grid detection (top/middle/bottom × left/center/right)
for mapping text field locations on specimen labels. Zone assignments use percentage-based
coordinates to enable reuse across different image sizes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple


class VerticalZone(str, Enum):
    """Vertical position zones."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class HorizontalZone(str, Enum):
    """Horizontal position zones."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class BoundingBox:
    """Normalized bounding box in percentage coordinates.

    Vision Framework returns bounding boxes with origin (0,0) at bottom-left.
    All coordinates are in [0, 1] range representing percentages.

    Attributes
    ----------
    x : float
        Left edge position (0.0 = left edge, 1.0 = right edge)
    y : float
        Bottom edge position (0.0 = bottom edge, 1.0 = top edge)
    width : float
        Box width as fraction of image width
    height : float
        Box height as fraction of image height
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def center_x(self) -> float:
        """Horizontal center position."""
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        """Vertical center position."""
        return self.y + (self.height / 2)

    @classmethod
    def from_list(cls, coords: List[float]) -> BoundingBox:
        """Create from Vision API coordinate list [x, y, width, height]."""
        if len(coords) != 4:
            raise ValueError(f"Expected 4 coordinates, got {len(coords)}")
        return cls(x=coords[0], y=coords[1], width=coords[2], height=coords[3])


@dataclass
class TextBlock:
    """Text block with spatial information."""

    text: str
    box: BoundingBox
    confidence: float


@dataclass
class ZoneInfo:
    """Zone classification for a text block."""

    vertical: VerticalZone
    horizontal: HorizontalZone
    box: BoundingBox | None = None  # Optional: bounding box coordinates

    def __str__(self) -> str:
        """Human-readable zone description."""
        return f"{self.vertical.value}-{self.horizontal.value}"

    def to_dict(self) -> Dict[str, str | List[float]]:
        """Convert to dictionary."""
        result = {"vertical": self.vertical.value, "horizontal": self.horizontal.value}
        if self.box:
            result["box"] = [self.box.x, self.box.y, self.box.width, self.box.height]
        return result


@dataclass
class SpatialTemplate:
    """Spatial zone template for a specimen.

    Maps DWC field names to their typical zones on the label.
    """

    specimen_id: str
    zones_by_text: Dict[str, ZoneInfo]  # Maps text content to zone
    image_width: int | None = None  # Optional: for validation
    image_height: int | None = None  # Optional: for validation

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "specimen_id": self.specimen_id,
            "zones": {text: zone.to_dict() for text, zone in self.zones_by_text.items()},
            "image_width": self.image_width,
            "image_height": self.image_height,
        }


def classify_zone(
    box: BoundingBox,
    vertical_thresholds: Tuple[float, float] = (0.33, 0.67),
    horizontal_thresholds: Tuple[float, float] = (0.33, 0.67),
) -> ZoneInfo:
    """Classify bounding box into 9-zone grid using center point.

    Parameters
    ----------
    box : BoundingBox
        The bounding box to classify
    vertical_thresholds : tuple of float
        (lower, upper) thresholds for vertical zones (default: 33%, 67%)
    horizontal_thresholds : tuple of float
        (lower, upper) thresholds for horizontal zones (default: 33%, 67%)

    Returns
    -------
    ZoneInfo
        Zone classification

    Notes
    -----
    Vision Framework uses bottom-left origin, so:
    - y < 0.33 = bottom zone
    - y > 0.67 = top zone
    - 0.33 <= y <= 0.67 = middle zone
    """
    vert_low, vert_high = vertical_thresholds
    horiz_low, horiz_high = horizontal_thresholds

    # Vertical classification (Vision uses bottom-left origin)
    if box.center_y < vert_low:
        vertical = VerticalZone.BOTTOM
    elif box.center_y > vert_high:
        vertical = VerticalZone.TOP
    else:
        vertical = VerticalZone.MIDDLE

    # Horizontal classification
    if box.center_x < horiz_low:
        horizontal = HorizontalZone.LEFT
    elif box.center_x > horiz_high:
        horizontal = HorizontalZone.RIGHT
    else:
        horizontal = HorizontalZone.CENTER

    return ZoneInfo(vertical=vertical, horizontal=horizontal)


def analyze_text_zones(text_blocks: List[TextBlock]) -> Dict[str, ZoneInfo]:
    """Analyze spatial zones for all text blocks.

    Parameters
    ----------
    text_blocks : list of TextBlock
        Text blocks with bounding boxes

    Returns
    -------
    dict
        Maps text content to zone classification
    """
    zones = {}
    for block in text_blocks:
        zone = classify_zone(block.box)
        # Attach bounding box to zone info for visualization
        zone.box = block.box
        zones[block.text] = zone
    return zones


def create_template(
    specimen_id: str, tokens: List[str], boxes: List[List[float]], confidences: List[float]
) -> SpatialTemplate:
    """Create spatial template from Vision API output.

    Parameters
    ----------
    specimen_id : str
        Specimen identifier (SHA256 hash)
    tokens : list of str
        Recognized text tokens from Vision API
    boxes : list of list of float
        Bounding boxes from Vision API [[x, y, w, h], ...]
    confidences : list of float
        Confidence scores for each token

    Returns
    -------
    SpatialTemplate
        Template mapping text to zones
    """
    text_blocks = [
        TextBlock(text=text, box=BoundingBox.from_list(box), confidence=conf)
        for text, box, conf in zip(tokens, boxes, confidences)
    ]

    zones = analyze_text_zones(text_blocks)

    return SpatialTemplate(specimen_id=specimen_id, zones_by_text=zones)


def get_zone_statistics(templates: List[SpatialTemplate]) -> Dict[str, Dict[str, int]]:
    """Calculate zone distribution statistics across templates.

    Parameters
    ----------
    templates : list of SpatialTemplate
        Spatial templates to analyze

    Returns
    -------
    dict
        Zone frequency counts: {zone_name: count}
    """
    zone_counts: Dict[str, int] = {}

    for template in templates:
        for zone in template.zones_by_text.values():
            zone_str = str(zone)
            zone_counts[zone_str] = zone_counts.get(zone_str, 0) + 1

    return {"zone_distribution": zone_counts}


__all__ = [
    "VerticalZone",
    "HorizontalZone",
    "BoundingBox",
    "TextBlock",
    "ZoneInfo",
    "SpatialTemplate",
    "classify_zone",
    "analyze_text_zones",
    "create_template",
    "get_zone_statistics",
]
