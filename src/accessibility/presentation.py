"""
Multi-modal presentation metadata for accessibility-first design.

This module provides classes for representing information across multiple
sensory modalities (visual, auditory, textual, structured) to ensure
information parity for all users.

Constitutional Reference: Core Principle VI - Information Parity and Inclusive Design
Pattern Reference: ~/devvyn-meta-project/knowledge-base/patterns/information-parity-design.md
"""

from dataclasses import dataclass, field
from typing import Dict, Literal, Optional


@dataclass
class PresentationMetadata:
    """
    Multi-modal presentation guidance for a piece of information.

    Ensures information parity by specifying how data should be presented
    across different sensory modalities.

    Attributes:
        visual: How information appears visually (text, color, icon)
        auditory: Screen reader announcement text
        textual: Plain text alternative (for copy/paste, non-visual access)
        aria_label: ARIA label for web accessibility
        keyboard_hint: Optional keyboard shortcut or navigation hint
        structured: Machine-readable format (for automation, bots, APIs)

    Example:
        >>> metadata = PresentationMetadata(
        ...     visual="🔴 CRITICAL",
        ...     auditory="Critical priority - requires immediate review",
        ...     textual="CRITICAL",
        ...     aria_label="Status: Critical priority, 26% quality, requires immediate attention",
        ...     keyboard_hint="Press 'c' to filter critical items",
        ...     structured={"status": "critical", "priority": 1, "urgent": True}
        ... )
    """

    visual: str
    auditory: str
    textual: str
    aria_label: str
    keyboard_hint: Optional[str] = None
    structured: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "visual": self.visual,
            "auditory": self.auditory,
            "textual": self.textual,
            "aria_label": self.aria_label,
            "keyboard_hint": self.keyboard_hint,
            "structured": self.structured,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PresentationMetadata":
        """Create from dictionary (deserialization)."""
        return cls(
            visual=data["visual"],
            auditory=data["auditory"],
            textual=data["textual"],
            aria_label=data["aria_label"],
            keyboard_hint=data.get("keyboard_hint"),
            structured=data.get("structured", {}),
        )


@dataclass
class VisualPresentation:
    """Visual representation details."""

    color: str  # Hex color code (e.g., "#dc3545")
    icon: str  # Emoji or icon identifier (e.g., "🔴")
    text: str  # Display text (e.g., "CRITICAL")
    css_class: Optional[str] = None  # CSS class for styling

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "color": self.color,
            "icon": self.icon,
            "text": self.text,
            "css_class": self.css_class,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "VisualPresentation":
        """Create from dictionary (deserialization)."""
        return cls(
            color=data["color"],
            icon=data["icon"],
            text=data["text"],
            css_class=data.get("css_class"),
        )


@dataclass
class QualityIndicator:
    """
    Multi-modal quality/status indicator for specimens or data.

    Represents quality or status information across all sensory modalities
    to ensure no user is privileged or disadvantaged by their sensory configuration.

    Attributes:
        score: Numeric quality score (0.0-1.0)
        level: Categorical quality level
        visual: Visual representation (color, icon, text)
        auditory: Screen reader announcement
        aria_label: Full context for assistive technology
        keyboard_shortcut: Optional keyboard shortcut for filtering/navigation

    Example:
        >>> indicator = QualityIndicator(
        ...     score=0.26,
        ...     level="critical",
        ...     visual=VisualPresentation(
        ...         color="#dc3545",
        ...         icon="🔴",
        ...         text="CRITICAL",
        ...         css_class="badge-critical"
        ...     ),
        ...     auditory="Critical priority - requires immediate review",
        ...     aria_label="Status: Critical priority, 26% quality, 4 issues detected",
        ...     keyboard_shortcut="c"
        ... )
    """

    score: float  # 0.0 to 1.0
    level: Literal["critical", "high", "medium", "low", "approved"]
    visual: VisualPresentation
    auditory: str
    aria_label: str
    keyboard_shortcut: Optional[str] = None

    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Quality score must be between 0.0 and 1.0, got {self.score}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "score": self.score,
            "level": self.level,
            "visual": self.visual.to_dict(),
            "auditory": self.auditory,
            "aria_label": self.aria_label,
            "keyboard_shortcut": self.keyboard_shortcut,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QualityIndicator":
        """Create from dictionary (deserialization)."""
        return cls(
            score=data["score"],
            level=data["level"],
            visual=VisualPresentation.from_dict(data["visual"]),
            auditory=data["auditory"],
            aria_label=data["aria_label"],
            keyboard_shortcut=data.get("keyboard_shortcut"),
        )

    @classmethod
    def from_score(cls, score: float, context: str = "specimen") -> "QualityIndicator":
        """
        Create quality indicator from numeric score with sensible defaults.

        Args:
            score: Quality score (0.0-1.0)
            context: Context for messaging ("specimen", "field", "extraction")

        Returns:
            QualityIndicator with appropriate multi-modal representation
        """
        if score >= 0.85:
            return cls(
                score=score,
                level="approved",
                visual=VisualPresentation(
                    color="#28a745", icon="✅", text="APPROVED", css_class="badge-approved"
                ),
                auditory=f"Approved - high quality {context}",
                aria_label=f"Status: Approved, {score:.0%} quality",
                keyboard_shortcut="a",
            )
        elif score >= 0.65:
            return cls(
                score=score,
                level="medium",
                visual=VisualPresentation(
                    color="#ffc107", icon="⚠️", text="MEDIUM", css_class="badge-medium"
                ),
                auditory=f"Medium quality - review recommended for {context}",
                aria_label=f"Status: Medium quality, {score:.0%}, review recommended",
                keyboard_shortcut="m",
            )
        elif score >= 0.40:
            return cls(
                score=score,
                level="high",
                visual=VisualPresentation(
                    color="#fd7e14", icon="🟡", text="HIGH", css_class="badge-high"
                ),
                auditory=f"High priority - {context} requires attention",
                aria_label=f"Status: High priority, {score:.0%} quality, requires review",
                keyboard_shortcut="h",
            )
        else:
            return cls(
                score=score,
                level="critical",
                visual=VisualPresentation(
                    color="#dc3545", icon="🔴", text="CRITICAL", css_class="badge-critical"
                ),
                auditory=f"Critical priority - {context} requires immediate review",
                aria_label=f"Status: Critical priority, {score:.0%} quality, requires immediate attention",
                keyboard_shortcut="c",
            )
