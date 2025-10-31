"""Image annotation for spatial zone visualization.

This module provides functions to draw spatial zone overlays on herbarium specimen images,
including grid lines and color-coded bounding boxes for text regions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw

from .zone_detector import SpatialTemplate, VerticalZone, HorizontalZone


# Zone color scheme
ZONE_COLORS = {
    # Top zones - Blue shades
    (VerticalZone.TOP, HorizontalZone.LEFT): "#4A90E2",
    (VerticalZone.TOP, HorizontalZone.CENTER): "#5DA5E8",
    (VerticalZone.TOP, HorizontalZone.RIGHT): "#70BAEE",
    # Middle zones - Green shades
    (VerticalZone.MIDDLE, HorizontalZone.LEFT): "#50C878",
    (VerticalZone.MIDDLE, HorizontalZone.CENTER): "#6CD890",
    (VerticalZone.MIDDLE, HorizontalZone.RIGHT): "#88E8A8",
    # Bottom zones - Orange shades
    (VerticalZone.BOTTOM, HorizontalZone.LEFT): "#F39C12",
    (VerticalZone.BOTTOM, HorizontalZone.CENTER): "#F5B041",
    (VerticalZone.BOTTOM, HorizontalZone.RIGHT): "#F8C471",
}

GRID_COLOR = "#CCCCCC"  # Light gray for grid lines
GRID_WIDTH = 2  # Grid line thickness
BOX_WIDTH = 3  # Bounding box line thickness


def draw_zone_grid(
    image: Image.Image,
    vertical_thresholds: Tuple[float, float] = (0.33, 0.67),
    horizontal_thresholds: Tuple[float, float] = (0.33, 0.67),
) -> Image.Image:
    """Draw 9-zone grid overlay on image.

    Parameters
    ----------
    image : PIL.Image.Image
        Source image
    vertical_thresholds : tuple of float
        (lower, upper) thresholds for vertical zones (default: 33%, 67%)
    horizontal_thresholds : tuple of float
        (lower, upper) thresholds for horizontal zones (default: 33%, 67%)

    Returns
    -------
    PIL.Image.Image
        Image with grid overlay
    """
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Vertical grid lines (33% and 67% from left)
    for h_threshold in horizontal_thresholds:
        x = int(width * h_threshold)
        draw.line([(x, 0), (x, height)], fill=GRID_COLOR, width=GRID_WIDTH)

    # Horizontal grid lines (Vision uses bottom-left origin, so flip)
    # 33% from bottom = 67% from top, 67% from bottom = 33% from top
    for v_threshold in vertical_thresholds:
        # Flip y-axis: Vision's y=0.33 is at top 67%
        y = int(height * (1.0 - v_threshold))
        draw.line([(0, y), (width, y)], fill=GRID_COLOR, width=GRID_WIDTH)

    return img


def draw_text_boxes(
    image: Image.Image,
    zone_template: SpatialTemplate,
) -> Image.Image:
    """Draw color-coded bounding boxes for text zones.

    Parameters
    ----------
    image : PIL.Image.Image
        Source image
    zone_template : SpatialTemplate
        Spatial template with zone classifications and bounding boxes

    Returns
    -------
    PIL.Image.Image
        Image with bounding box overlays
    """
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size

    for text, zone_info in zone_template.zones_by_text.items():
        if not zone_info.box:
            continue  # Skip if no bounding box available

        # Get color for this zone
        zone_key = (zone_info.vertical, zone_info.horizontal)
        color = ZONE_COLORS.get(zone_key, "#808080")  # Gray fallback

        # Convert normalized coordinates to pixel coordinates
        # Vision Framework uses bottom-left origin (y=0 at bottom)
        box = zone_info.box
        x1 = int(box.x * width)
        # Flip y-axis: Vision's y=0 is at bottom, PIL's y=0 is at top
        y1 = int((1.0 - (box.y + box.height)) * height)
        x2 = int((box.x + box.width) * width)
        y2 = int((1.0 - box.y) * height)

        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=BOX_WIDTH)

    return img


def annotate_specimen_image(
    image_path: Path,
    zone_template: SpatialTemplate,
    output_path: Path | None = None,
    draw_grid: bool = True,
    draw_boxes: bool = True,
) -> Image.Image:
    """Create annotated specimen image with zone overlays.

    Parameters
    ----------
    image_path : Path
        Path to source image
    zone_template : SpatialTemplate
        Spatial template with zone data
    output_path : Path, optional
        Path to save annotated image (if None, not saved)
    draw_grid : bool
        Whether to draw zone grid lines (default: True)
    draw_boxes : bool
        Whether to draw text bounding boxes (default: True)

    Returns
    -------
    PIL.Image.Image
        Annotated image

    Raises
    ------
    FileNotFoundError
        If source image not found
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Load image
    img = Image.open(image_path)

    # Apply overlays
    if draw_grid:
        img = draw_zone_grid(img)
    if draw_boxes:
        img = draw_text_boxes(img, zone_template)

    # Save if output path specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)

    return img


__all__ = [
    "ZONE_COLORS",
    "draw_zone_grid",
    "draw_text_boxes",
    "annotate_specimen_image",
]
