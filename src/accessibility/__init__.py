"""
Accessibility module for multi-modal information presentation.

Provides data structures and utilities for ensuring information parity
across different sensory modalities (visual, auditory, textual, structured).

Constitutional Reference: Core Principle VI - Information Parity and Inclusive Design

Classes:
    PresentationMetadata: Multi-modal presentation guidance
    VisualPresentation: Visual representation details
    QualityIndicator: Multi-modal quality/status indicators
    BoundingBox: Spatial coordinates for label regions
    LabelRegion: Structured label region for non-visual navigation
    SpecimenImageMetadata: Complete accessibility metadata for specimen images
"""

from .label_regions import BoundingBox, LabelRegion, SpecimenImageMetadata
from .presentation import (
    PresentationMetadata,
    QualityIndicator,
    VisualPresentation,
)

__all__ = [
    # Presentation classes
    "PresentationMetadata",
    "VisualPresentation",
    "QualityIndicator",
    # Label region classes
    "BoundingBox",
    "LabelRegion",
    "SpecimenImageMetadata",
]
