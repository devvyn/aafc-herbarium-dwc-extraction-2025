"""
Unit tests for src/accessibility/presentation.py

Tests multi-modal presentation classes for accessibility-first design.
"""

import pytest

from src.accessibility.presentation import (
    PresentationMetadata,
    QualityIndicator,
    VisualPresentation,
)


class TestVisualPresentation:
    """Test VisualPresentation class."""

    def test_create_visual_presentation(self):
        """Test basic creation of VisualPresentation."""
        visual = VisualPresentation(
            color="#28a745", icon="✅", text="APPROVED", css_class="badge-approved"
        )

        assert visual.color == "#28a745"
        assert visual.icon == "✅"
        assert visual.text == "APPROVED"
        assert visual.css_class == "badge-approved"

    def test_visual_presentation_optional_css_class(self):
        """Test VisualPresentation with optional css_class."""
        visual = VisualPresentation(color="#dc3545", icon="🔴", text="CRITICAL")

        assert visual.color == "#dc3545"
        assert visual.icon == "🔴"
        assert visual.text == "CRITICAL"
        assert visual.css_class is None

    def test_to_dict(self):
        """Test serialization to dictionary."""
        visual = VisualPresentation(
            color="#ffc107", icon="⚠️", text="MEDIUM", css_class="badge-medium"
        )

        result = visual.to_dict()

        assert result == {
            "color": "#ffc107",
            "icon": "⚠️",
            "text": "MEDIUM",
            "css_class": "badge-medium",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"color": "#fd7e14", "icon": "🟡", "text": "HIGH", "css_class": "badge-high"}

        visual = VisualPresentation.from_dict(data)

        assert visual.color == "#fd7e14"
        assert visual.icon == "🟡"
        assert visual.text == "HIGH"
        assert visual.css_class == "badge-high"

    def test_from_dict_without_css_class(self):
        """Test deserialization without optional css_class."""
        data = {"color": "#000000", "icon": "⚫", "text": "UNKNOWN"}

        visual = VisualPresentation.from_dict(data)

        assert visual.color == "#000000"
        assert visual.icon == "⚫"
        assert visual.text == "UNKNOWN"
        assert visual.css_class is None


class TestPresentationMetadata:
    """Test PresentationMetadata class."""

    def test_create_presentation_metadata(self):
        """Test basic creation of PresentationMetadata."""
        metadata = PresentationMetadata(
            visual="🔴 CRITICAL",
            auditory="Critical priority - requires immediate review",
            textual="CRITICAL",
            aria_label="Status: Critical priority, 26% quality, requires immediate attention",
            keyboard_hint="Press 'c' to filter critical items",
            structured={"status": "critical", "priority": 1, "urgent": True},
        )

        assert metadata.visual == "🔴 CRITICAL"
        assert metadata.auditory == "Critical priority - requires immediate review"
        assert metadata.textual == "CRITICAL"
        assert (
            metadata.aria_label
            == "Status: Critical priority, 26% quality, requires immediate attention"
        )
        assert metadata.keyboard_hint == "Press 'c' to filter critical items"
        assert metadata.structured == {"status": "critical", "priority": 1, "urgent": True}

    def test_presentation_metadata_optional_fields(self):
        """Test PresentationMetadata with optional fields."""
        metadata = PresentationMetadata(
            visual="✅ APPROVED",
            auditory="Approved - high quality specimen",
            textual="APPROVED",
            aria_label="Status: Approved, 87% quality",
        )

        assert metadata.keyboard_hint is None
        assert metadata.structured == {}

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metadata = PresentationMetadata(
            visual="⚠️ MEDIUM",
            auditory="Medium quality - review recommended",
            textual="MEDIUM",
            aria_label="Status: Medium quality, 68% quality",
            keyboard_hint="m",
            structured={"status": "medium", "priority": 2},
        )

        result = metadata.to_dict()

        assert result == {
            "visual": "⚠️ MEDIUM",
            "auditory": "Medium quality - review recommended",
            "textual": "MEDIUM",
            "aria_label": "Status: Medium quality, 68% quality",
            "keyboard_hint": "m",
            "structured": {"status": "medium", "priority": 2},
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "visual": "🟡 HIGH",
            "auditory": "High priority - requires attention",
            "textual": "HIGH",
            "aria_label": "Status: High priority, 52% quality",
            "keyboard_hint": "h",
            "structured": {"status": "high", "priority": 3},
        }

        metadata = PresentationMetadata.from_dict(data)

        assert metadata.visual == "🟡 HIGH"
        assert metadata.auditory == "High priority - requires attention"
        assert metadata.textual == "HIGH"
        assert metadata.aria_label == "Status: High priority, 52% quality"
        assert metadata.keyboard_hint == "h"
        assert metadata.structured == {"status": "high", "priority": 3}


class TestQualityIndicator:
    """Test QualityIndicator class."""

    def test_create_quality_indicator(self):
        """Test basic creation of QualityIndicator."""
        visual = VisualPresentation(
            color="#dc3545", icon="🔴", text="CRITICAL", css_class="badge-critical"
        )

        indicator = QualityIndicator(
            score=0.26,
            level="critical",
            visual=visual,
            auditory="Critical priority - requires immediate review",
            aria_label="Status: Critical priority, 26% quality, 4 issues detected",
            keyboard_shortcut="c",
        )

        assert indicator.score == 0.26
        assert indicator.level == "critical"
        assert indicator.visual == visual
        assert indicator.auditory == "Critical priority - requires immediate review"
        assert indicator.aria_label == "Status: Critical priority, 26% quality, 4 issues detected"
        assert indicator.keyboard_shortcut == "c"

    def test_quality_indicator_score_validation(self):
        """Test score range validation."""
        visual = VisualPresentation(color="#000", icon="⚫", text="TEST")

        # Valid scores
        QualityIndicator(
            score=0.0, level="critical", visual=visual, auditory="test", aria_label="test"
        )
        QualityIndicator(
            score=0.5, level="medium", visual=visual, auditory="test", aria_label="test"
        )
        QualityIndicator(
            score=1.0, level="approved", visual=visual, auditory="test", aria_label="test"
        )

        # Invalid scores
        with pytest.raises(ValueError, match="Quality score must be between 0.0 and 1.0"):
            QualityIndicator(
                score=-0.1, level="critical", visual=visual, auditory="test", aria_label="test"
            )

        with pytest.raises(ValueError, match="Quality score must be between 0.0 and 1.0"):
            QualityIndicator(
                score=1.1, level="approved", visual=visual, auditory="test", aria_label="test"
            )

    def test_from_score_approved(self):
        """Test from_score factory method for approved quality."""
        indicator = QualityIndicator.from_score(0.87, context="specimen")

        assert indicator.score == 0.87
        assert indicator.level == "approved"
        assert indicator.visual.color == "#28a745"
        assert indicator.visual.icon == "✅"
        assert indicator.visual.text == "APPROVED"
        assert indicator.auditory == "Approved - high quality specimen"
        assert indicator.aria_label == "Status: Approved, 87% quality"
        assert indicator.keyboard_shortcut == "a"

    def test_from_score_medium(self):
        """Test from_score factory method for medium quality."""
        indicator = QualityIndicator.from_score(0.68, context="field")

        assert indicator.score == 0.68
        assert indicator.level == "medium"
        assert indicator.visual.color == "#ffc107"
        assert indicator.visual.icon == "⚠️"
        assert indicator.visual.text == "MEDIUM"
        assert indicator.auditory == "Medium quality - review recommended for field"
        assert indicator.aria_label == "Status: Medium quality, 68%, review recommended"
        assert indicator.keyboard_shortcut == "m"

    def test_from_score_high(self):
        """Test from_score factory method for high priority."""
        indicator = QualityIndicator.from_score(0.52, context="extraction")

        assert indicator.score == 0.52
        assert indicator.level == "high"
        assert indicator.visual.color == "#fd7e14"
        assert indicator.visual.icon == "🟡"
        assert indicator.visual.text == "HIGH"
        assert indicator.auditory == "High priority - extraction requires attention"
        assert indicator.aria_label == "Status: High priority, 52% quality, requires review"
        assert indicator.keyboard_shortcut == "h"

    def test_from_score_critical(self):
        """Test from_score factory method for critical priority."""
        indicator = QualityIndicator.from_score(0.26, context="specimen")

        assert indicator.score == 0.26
        assert indicator.level == "critical"
        assert indicator.visual.color == "#dc3545"
        assert indicator.visual.icon == "🔴"
        assert indicator.visual.text == "CRITICAL"
        assert indicator.auditory == "Critical priority - specimen requires immediate review"
        assert (
            indicator.aria_label
            == "Status: Critical priority, 26% quality, requires immediate attention"
        )
        assert indicator.keyboard_shortcut == "c"

    def test_from_score_boundary_cases(self):
        """Test from_score factory method at score boundaries."""
        # Exactly at boundaries
        assert QualityIndicator.from_score(0.85).level == "approved"
        assert QualityIndicator.from_score(0.65).level == "medium"
        assert QualityIndicator.from_score(0.40).level == "high"
        assert QualityIndicator.from_score(0.39).level == "critical"

        # Just below boundaries
        assert QualityIndicator.from_score(0.84).level == "medium"
        assert QualityIndicator.from_score(0.64).level == "high"
        assert QualityIndicator.from_score(0.39).level == "critical"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        visual = VisualPresentation(
            color="#28a745", icon="✅", text="APPROVED", css_class="badge-approved"
        )
        indicator = QualityIndicator(
            score=0.87,
            level="approved",
            visual=visual,
            auditory="Approved - high quality specimen",
            aria_label="Status: Approved, 87% quality",
            keyboard_shortcut="a",
        )

        result = indicator.to_dict()

        assert result == {
            "score": 0.87,
            "level": "approved",
            "visual": {
                "color": "#28a745",
                "icon": "✅",
                "text": "APPROVED",
                "css_class": "badge-approved",
            },
            "auditory": "Approved - high quality specimen",
            "aria_label": "Status: Approved, 87% quality",
            "keyboard_shortcut": "a",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "score": 0.68,
            "level": "medium",
            "visual": {
                "color": "#ffc107",
                "icon": "⚠️",
                "text": "MEDIUM",
                "css_class": "badge-medium",
            },
            "auditory": "Medium quality - review recommended",
            "aria_label": "Status: Medium quality, 68%, review recommended",
            "keyboard_shortcut": "m",
        }

        indicator = QualityIndicator.from_dict(data)

        assert indicator.score == 0.68
        assert indicator.level == "medium"
        assert indicator.visual.color == "#ffc107"
        assert indicator.visual.icon == "⚠️"
        assert indicator.visual.text == "MEDIUM"
        assert indicator.auditory == "Medium quality - review recommended"
        assert indicator.aria_label == "Status: Medium quality, 68%, review recommended"
        assert indicator.keyboard_shortcut == "m"
