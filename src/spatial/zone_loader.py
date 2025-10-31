"""Zone template loading and caching.

This module provides functions to load spatial zone templates from JSONL files
and cache them in memory for efficient access during review sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .zone_detector import SpatialTemplate, ZoneInfo, BoundingBox, VerticalZone, HorizontalZone


class ZoneTemplateCache:
    """In-memory cache for zone templates."""

    def __init__(self):
        self._cache: Dict[str, SpatialTemplate] = {}
        self._zones_file: Optional[Path] = None

    def load_from_file(self, zones_file: Path) -> None:
        """Load all zone templates from JSONL file into cache.

        Parameters
        ----------
        zones_file : Path
            Path to spatial_zones.jsonl file

        Raises
        ------
        FileNotFoundError
            If zones file doesn't exist
        """
        if not zones_file.exists():
            raise FileNotFoundError(f"Zone templates file not found: {zones_file}")

        self._cache.clear()
        self._zones_file = zones_file

        with open(zones_file) as f:
            for line in f:
                template = self._parse_template(line)
                self._cache[template.specimen_id] = template

    def _parse_template(self, jsonl_line: str) -> SpatialTemplate:
        """Parse zone template from JSONL line.

        Parameters
        ----------
        jsonl_line : str
            JSON line from spatial_zones.jsonl

        Returns
        -------
        SpatialTemplate
            Parsed spatial template
        """
        data = json.loads(jsonl_line)

        # Reconstruct zones_by_text dictionary
        zones_by_text = {}
        for text, zone_data in data["zones"].items():
            # Parse zone classification
            vertical = VerticalZone(zone_data["vertical"])
            horizontal = HorizontalZone(zone_data["horizontal"])

            # Parse bounding box if present
            box = None
            if "box" in zone_data:
                box_coords = zone_data["box"]
                box = BoundingBox(
                    x=box_coords[0],
                    y=box_coords[1],
                    width=box_coords[2],
                    height=box_coords[3],
                )

            zones_by_text[text] = ZoneInfo(vertical=vertical, horizontal=horizontal, box=box)

        return SpatialTemplate(
            specimen_id=data["specimen_id"],
            zones_by_text=zones_by_text,
            image_width=data.get("image_width"),
            image_height=data.get("image_height"),
        )

    def get(self, specimen_id: str) -> Optional[SpatialTemplate]:
        """Get zone template for specimen from cache.

        Parameters
        ----------
        specimen_id : str
            Specimen identifier (SHA256 hash)

        Returns
        -------
        SpatialTemplate or None
            Template if found in cache, None otherwise
        """
        return self._cache.get(specimen_id)

    def has(self, specimen_id: str) -> bool:
        """Check if template exists in cache.

        Parameters
        ----------
        specimen_id : str
            Specimen identifier

        Returns
        -------
        bool
            True if template exists in cache
        """
        return specimen_id in self._cache

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._zones_file = None

    def __len__(self) -> int:
        """Get number of cached templates."""
        return len(self._cache)


def get_zones_file_path(extraction_dir: Path) -> Path:
    """Get standard path for spatial zones file.

    Parameters
    ----------
    extraction_dir : Path
        Extraction directory (e.g., deliverables/v1.0_vision_baseline)

    Returns
    -------
    Path
        Path to spatial_zones.jsonl
    """
    return extraction_dir / "spatial_zones.jsonl"


def load_zone_template(specimen_id: str, zones_file: Path) -> Optional[SpatialTemplate]:
    """Load zone template for a single specimen.

    This function reads through the zones file to find the template.
    For efficient repeated access, use ZoneTemplateCache instead.

    Parameters
    ----------
    specimen_id : str
        Specimen identifier (SHA256 hash)
    zones_file : Path
        Path to spatial_zones.jsonl file

    Returns
    -------
    SpatialTemplate or None
        Template if found, None otherwise

    Raises
    ------
    FileNotFoundError
        If zones file doesn't exist
    """
    if not zones_file.exists():
        raise FileNotFoundError(f"Zone templates file not found: {zones_file}")

    cache = ZoneTemplateCache()
    with open(zones_file) as f:
        for line in f:
            data = json.loads(line)
            if data["specimen_id"] == specimen_id:
                return cache._parse_template(line)

    return None


__all__ = [
    "ZoneTemplateCache",
    "get_zones_file_path",
    "load_zone_template",
]
