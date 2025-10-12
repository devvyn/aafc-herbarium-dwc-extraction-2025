"""
Integration tests for Phase 2B - Review API with accessibility metadata.

Tests the v2 API endpoints that include multi-modal accessibility data
for SpecimenReview objects.
"""

import pytest
from src.review.engine import ReviewStatus, ReviewPriority, SpecimenReview


class TestReviewAccessibilityIntegration:
    """Test SpecimenReview accessibility methods."""

    def test_to_dict_with_accessibility_includes_quality_indicator(self):
        """Test that to_dict_with_accessibility includes QualityIndicator."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            quality_score=87.0,
            completeness_score=95.0,
            confidence_score=75.0,
            status=ReviewStatus.PENDING,
        )

        result = review.to_dict_with_accessibility()

        assert "accessibility" in result
        assert "quality_indicator" in result["accessibility"]
        assert result["accessibility"]["quality_indicator"]["score"] == pytest.approx(0.87)
        assert result["accessibility"]["quality_indicator"]["level"] == "approved"

    def test_to_dict_with_accessibility_includes_presentation_metadata(self):
        """Test that to_dict_with_accessibility includes PresentationMetadata."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            quality_score=50.0,
            status=ReviewStatus.APPROVED,
            reviewed_by="curator@example.com",
        )

        result = review.to_dict_with_accessibility()

        assert "presentation_metadata" in result["accessibility"]
        meta = result["accessibility"]["presentation_metadata"]
        assert "visual" in meta
        assert "Approved" in meta["visual"]
        assert "auditory" in meta
        assert "aria_label" in meta

    def test_to_dict_with_accessibility_includes_keyboard_shortcuts(self):
        """Test that keyboard shortcuts are documented in response."""
        review = SpecimenReview(specimen_id="DSC_1162", quality_score=75.0)

        result = review.to_dict_with_accessibility()

        assert "keyboard_shortcuts" in result["accessibility"]
        shortcuts = result["accessibility"]["keyboard_shortcuts"]
        assert shortcuts["approve"] == "a"
        assert shortcuts["reject"] == "r"
        assert shortcuts["flag"] == "f"

    def test_to_dict_backward_compatibility(self):
        """Test that to_dict() does NOT include accessibility fields (v1 API)."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            quality_score=87.0,
            completeness_score=95.0,
        )

        result = review.to_dict()

        # v1 API should NOT have accessibility field
        assert "accessibility" not in result
        # But should have base data
        assert result["specimen_id"] == "DSC_1162"
        assert "quality" in result
        assert result["quality"]["quality_score"] == 87.0

    def test_status_presentation_for_pending(self):
        """Test presentation metadata for PENDING status."""
        review = SpecimenReview(specimen_id="DSC_1162", status=ReviewStatus.PENDING)

        result = review.to_dict_with_accessibility()
        meta = result["accessibility"]["presentation_metadata"]

        assert "Pending" in meta["visual"]
        assert "PENDING" == meta["textual"]
        assert "awaiting curator" in meta["auditory"]

    def test_status_presentation_for_approved(self):
        """Test presentation metadata for APPROVED status."""
        review = SpecimenReview(
            specimen_id="DSC_1162", status=ReviewStatus.APPROVED, reviewed_by="curator@example.com"
        )

        result = review.to_dict_with_accessibility()
        meta = result["accessibility"]["presentation_metadata"]

        assert "Approved" in meta["visual"]
        assert "APPROVED" == meta["textual"]
        assert "Approved by curator@example.com" in meta["aria_label"]

    def test_status_presentation_for_rejected(self):
        """Test presentation metadata for REJECTED status."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            status=ReviewStatus.REJECTED,
            reviewed_by="curator@example.com",
            notes="Missing locality data",
        )

        result = review.to_dict_with_accessibility()
        meta = result["accessibility"]["presentation_metadata"]

        assert "Rejected" in meta["visual"]
        assert "REJECTED" == meta["textual"]
        assert "requires correction" in meta["auditory"]
        assert "Missing locality data" in meta["aria_label"]

    def test_status_presentation_for_flagged(self):
        """Test presentation metadata for FLAGGED status."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            status=ReviewStatus.FLAGGED,
            reviewed_by="curator@example.com",
            notes="Uncertain taxonomy",
        )

        result = review.to_dict_with_accessibility()
        meta = result["accessibility"]["presentation_metadata"]

        assert "Flagged" in meta["visual"]
        assert "FLAGGED" == meta["textual"]
        assert "expert review" in meta["auditory"]
        assert "Uncertain taxonomy" in meta["aria_label"]

    def test_quality_indicator_score_levels(self):
        """Test that quality indicators match score thresholds."""
        # Test approved level (>= 0.85)
        review_approved = SpecimenReview(specimen_id="TEST1", quality_score=90.0)
        result_approved = review_approved.to_dict_with_accessibility()
        assert result_approved["accessibility"]["quality_indicator"]["level"] == "approved"

        # Test medium level (0.65 - 0.84)
        review_medium = SpecimenReview(specimen_id="TEST2", quality_score=68.0)
        result_medium = review_medium.to_dict_with_accessibility()
        assert result_medium["accessibility"]["quality_indicator"]["level"] == "medium"

        # Test high level (0.40 - 0.64)
        review_high = SpecimenReview(specimen_id="TEST3", quality_score=50.0)
        result_high = review_high.to_dict_with_accessibility()
        assert result_high["accessibility"]["quality_indicator"]["level"] == "high"

        # Test critical level (< 0.40)
        review_critical = SpecimenReview(specimen_id="TEST4", quality_score=30.0)
        result_critical = review_critical.to_dict_with_accessibility()
        assert result_critical["accessibility"]["quality_indicator"]["level"] == "critical"

    def test_structured_metadata_includes_review_state(self):
        """Test that structured metadata includes review state information."""
        review = SpecimenReview(
            specimen_id="DSC_1162",
            quality_score=75.0,
            status=ReviewStatus.IN_REVIEW,
            priority=ReviewPriority.HIGH,
            reviewed_by="curator@example.com",
        )

        result = review.to_dict_with_accessibility()
        structured = result["accessibility"]["presentation_metadata"]["structured"]

        assert structured["status"] == "IN_REVIEW"
        assert structured["priority"] == "HIGH"
        assert structured["quality_score"] == 75.0
        assert structured["reviewed"] is True

    def test_keyboard_hint_in_presentation(self):
        """Test that keyboard hints are included in presentation metadata."""
        review = SpecimenReview(specimen_id="DSC_1162")

        result = review.to_dict_with_accessibility()
        meta = result["accessibility"]["presentation_metadata"]

        assert "keyboard_hint" in meta
        assert "approve" in meta["keyboard_hint"]
        assert "reject" in meta["keyboard_hint"]
