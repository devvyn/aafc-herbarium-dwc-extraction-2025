"""
Review Engine for Extracted Specimen Data

Loads extraction results, applies GBIF validation, and provides
prioritized review queue for manual curation.

Features:
- Load results from raw.jsonl
- Apply GBIF taxonomy + locality validation
- Calculate quality scores per specimen
- Prioritize review queue (lowest quality first)
- Track review/approval status
"""

import json
import logging
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status for specimens."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ReviewPriority(Enum):
    """Priority levels for review queue."""

    CRITICAL = 1  # Major issues, requires immediate attention
    HIGH = 2  # Multiple issues or low confidence
    MEDIUM = 3  # Some issues but mostly complete
    LOW = 4  # Minor issues only
    MINIMAL = 5  # High quality, minimal review needed


@dataclass
class SpecimenReview:
    """Complete review record for a single specimen."""

    # Identity
    specimen_id: str
    sha256_hash: Optional[str] = None

    # Extraction data
    dwc_fields: Dict = dataclass_field(default_factory=dict)
    extraction_timestamp: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None

    # GBIF validation
    gbif_taxonomy_verified: bool = False
    gbif_taxonomy_confidence: float = 0.0
    gbif_taxonomy_issues: List[str] = dataclass_field(default_factory=list)
    gbif_locality_verified: bool = False
    gbif_locality_issues: List[str] = dataclass_field(default_factory=list)

    # Quality metrics
    completeness_score: float = 0.0  # 0-100%
    confidence_score: float = 0.0  # 0-100%
    quality_score: float = 0.0  # Combined metric
    priority: ReviewPriority = ReviewPriority.MEDIUM

    # Review tracking
    status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    corrections: Dict = dataclass_field(default_factory=dict)
    notes: Optional[str] = None

    # Issues
    critical_issues: List[str] = dataclass_field(default_factory=list)
    warnings: List[str] = dataclass_field(default_factory=list)

    def calculate_quality_score(self):
        """Calculate overall quality score from components."""
        # Weighted combination of completeness and confidence
        self.quality_score = (self.completeness_score * 0.6) + (self.confidence_score * 0.4)

    def determine_priority(self):
        """Determine review priority based on quality and issues."""
        # Critical priority if major issues
        if self.critical_issues or not self.dwc_fields:
            self.priority = ReviewPriority.CRITICAL
        # High priority if low quality or GBIF issues
        elif self.quality_score < 50 or self.gbif_taxonomy_issues or self.gbif_locality_issues:
            self.priority = ReviewPriority.HIGH
        # Medium priority if moderate quality
        elif self.quality_score < 75:
            self.priority = ReviewPriority.MEDIUM
        # Low priority if good quality but some warnings
        elif self.warnings:
            self.priority = ReviewPriority.LOW
        # Minimal priority if excellent quality
        else:
            self.priority = ReviewPriority.MINIMAL

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "specimen_id": self.specimen_id,
            "sha256_hash": self.sha256_hash,
            "dwc_fields": self.dwc_fields,
            "extraction_timestamp": self.extraction_timestamp,
            "model": self.model,
            "provider": self.provider,
            "gbif_validation": {
                "taxonomy_verified": self.gbif_taxonomy_verified,
                "taxonomy_confidence": self.gbif_taxonomy_confidence,
                "taxonomy_issues": self.gbif_taxonomy_issues,
                "locality_verified": self.gbif_locality_verified,
                "locality_issues": self.gbif_locality_issues,
            },
            "quality": {
                "completeness_score": self.completeness_score,
                "confidence_score": self.confidence_score,
                "quality_score": self.quality_score,
                "priority": self.priority.name,
            },
            "review": {
                "status": self.status.name,
                "reviewed_by": self.reviewed_by,
                "reviewed_at": self.reviewed_at,
                "corrections": self.corrections,
                "notes": self.notes,
            },
            "issues": {
                "critical": self.critical_issues,
                "warnings": self.warnings,
            },
        }


class ReviewEngine:
    """
    Engine for managing specimen review workflow.

    Loads extraction results, validates with GBIF, and provides
    prioritized review queue.
    """

    # Required Darwin Core fields for GBIF publication
    REQUIRED_FIELDS = [
        "catalogNumber",
        "scientificName",
        "eventDate",
        "recordedBy",
        "country",
        "stateProvince",
        "locality",
    ]

    def __init__(self, gbif_validator=None):
        """
        Initialize review engine.

        Args:
            gbif_validator: Optional GBIFValidator instance
        """
        self.gbif_validator = gbif_validator
        self.reviews: Dict[str, SpecimenReview] = {}

        logger.info("Review engine initialized")

    def load_extraction_results(self, results_file: Path) -> int:
        """
        Load extraction results from raw.jsonl file.

        Args:
            results_file: Path to raw.jsonl

        Returns:
            Number of specimens loaded
        """
        logger.info(f"Loading extraction results from {results_file}")

        count = 0
        with open(results_file) as f:
            for line in f:
                result = json.loads(line)

                # Extract specimen info
                specimen_id = result.get("image", "unknown")
                dwc_fields = result.get("dwc", {})

                if not dwc_fields:
                    # Failed extraction
                    review = SpecimenReview(
                        specimen_id=specimen_id,
                        extraction_timestamp=result.get("timestamp"),
                        model=result.get("model"),
                        provider=result.get("provider"),
                        critical_issues=[result.get("error", "No data extracted")],
                    )
                else:
                    review = SpecimenReview(
                        specimen_id=specimen_id,
                        dwc_fields=dwc_fields,
                        extraction_timestamp=result.get("timestamp"),
                        model=result.get("model"),
                        provider=result.get("provider"),
                    )

                    # Calculate metrics
                    self._calculate_completeness(review)
                    self._calculate_confidence(review)
                    self._identify_issues(review)

                    # Apply GBIF validation if available
                    if self.gbif_validator:
                        self._apply_gbif_validation(review)

                    # Calculate overall quality and priority
                    review.calculate_quality_score()
                    review.determine_priority()

                self.reviews[specimen_id] = review
                count += 1

        logger.info(f"Loaded {count} specimens for review")
        return count

    def _calculate_completeness(self, review: SpecimenReview):
        """Calculate completeness score based on required fields."""
        present = 0
        for field in self.REQUIRED_FIELDS:
            field_data = review.dwc_fields.get(field, {})
            if isinstance(field_data, dict):
                value = field_data.get("value")
            else:
                value = field_data

            if value and str(value).strip():
                present += 1

        review.completeness_score = (present / len(self.REQUIRED_FIELDS)) * 100

    def _calculate_confidence(self, review: SpecimenReview):
        """Calculate average confidence across all fields."""
        confidences = []

        for field, field_data in review.dwc_fields.items():
            if isinstance(field_data, dict):
                conf = field_data.get("confidence", 0.0)
                if conf > 0:
                    confidences.append(conf)

        if confidences:
            review.confidence_score = sum(confidences) / len(confidences)
        else:
            review.confidence_score = 0.0

    def _identify_issues(self, review: SpecimenReview):
        """Identify critical issues and warnings."""
        # Check for missing required fields
        for field in self.REQUIRED_FIELDS:
            field_data = review.dwc_fields.get(field, {})
            if isinstance(field_data, dict):
                value = field_data.get("value")
            else:
                value = field_data

            if not value or not str(value).strip():
                review.critical_issues.append(f"Missing required field: {field}")

        # Check for low confidence fields
        for field, field_data in review.dwc_fields.items():
            if isinstance(field_data, dict):
                conf = field_data.get("confidence", 0.0)
                value = field_data.get("value")

                if value and conf < 0.5:  # Confidence threshold
                    review.warnings.append(f"Low confidence for {field}: {conf:.2f}")

    def _apply_gbif_validation(self, review: SpecimenReview):
        """Apply GBIF validation to specimen record."""
        if not self.gbif_validator:
            return

        # Prepare record for GBIF validation
        dwc_record = {}
        for field, field_data in review.dwc_fields.items():
            if isinstance(field_data, dict):
                dwc_record[field] = field_data.get("value", "")
            else:
                dwc_record[field] = field_data

        try:
            # Validate taxonomy
            if dwc_record.get("scientificName"):
                _, tax_metadata = self.gbif_validator.verify_taxonomy(dwc_record)
                review.gbif_taxonomy_verified = tax_metadata.get("gbif_taxonomy_verified", False)
                review.gbif_taxonomy_confidence = tax_metadata.get("gbif_confidence", 0.0)
                review.gbif_taxonomy_issues = tax_metadata.get("gbif_issues", [])

            # Validate locality
            if dwc_record.get("decimalLatitude") and dwc_record.get("decimalLongitude"):
                _, loc_metadata = self.gbif_validator.verify_locality(dwc_record)
                review.gbif_locality_verified = loc_metadata.get("gbif_locality_verified", False)
                review.gbif_locality_issues = loc_metadata.get("gbif_issues", [])

        except Exception as e:
            logger.warning(f"GBIF validation error for {review.specimen_id}: {e}")
            review.warnings.append(f"GBIF validation error: {str(e)}")

    def get_review_queue(
        self,
        status: Optional[ReviewStatus] = None,
        priority: Optional[ReviewPriority] = None,
        sort_by: str = "priority",
    ) -> List[SpecimenReview]:
        """
        Get prioritized review queue.

        Args:
            status: Filter by review status
            priority: Filter by priority level
            sort_by: Sort field ("priority", "quality", "completeness")

        Returns:
            Sorted list of SpecimenReview objects
        """
        reviews = list(self.reviews.values())

        # Apply filters
        if status:
            reviews = [r for r in reviews if r.status == status]

        if priority:
            reviews = [r for r in reviews if r.priority == priority]

        # Sort
        if sort_by == "priority":
            reviews.sort(key=lambda r: r.priority.value)
        elif sort_by == "quality":
            reviews.sort(key=lambda r: r.quality_score)
        elif sort_by == "completeness":
            reviews.sort(key=lambda r: r.completeness_score)

        return reviews

    def get_review(self, specimen_id: str) -> Optional[SpecimenReview]:
        """Get review record for a specific specimen."""
        return self.reviews.get(specimen_id)

    def update_review(
        self,
        specimen_id: str,
        corrections: Optional[Dict] = None,
        status: Optional[ReviewStatus] = None,
        reviewed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """
        Update review record.

        Args:
            specimen_id: Specimen identifier
            corrections: Field corrections
            status: New review status
            reviewed_by: Reviewer identifier
            notes: Review notes
        """
        review = self.reviews.get(specimen_id)
        if not review:
            logger.warning(f"Review not found: {specimen_id}")
            return

        if corrections:
            review.corrections.update(corrections)

        if status:
            review.status = status

        if reviewed_by:
            review.reviewed_by = reviewed_by

        if notes:
            review.notes = notes

        review.reviewed_at = datetime.now().isoformat()

        logger.info(f"Updated review: {specimen_id} (status: {review.status.name})")

    def get_statistics(self) -> dict:
        """Get review statistics."""
        total = len(self.reviews)

        return {
            "total_specimens": total,
            "status_counts": {
                status.name: sum(1 for r in self.reviews.values() if r.status == status)
                for status in ReviewStatus
            },
            "priority_counts": {
                priority.name: sum(1 for r in self.reviews.values() if r.priority == priority)
                for priority in ReviewPriority
            },
            "avg_quality_score": (
                sum(r.quality_score for r in self.reviews.values()) / total if total > 0 else 0.0
            ),
            "avg_completeness": (
                sum(r.completeness_score for r in self.reviews.values()) / total
                if total > 0
                else 0.0
            ),
            "gbif_validated": sum(1 for r in self.reviews.values() if r.gbif_taxonomy_verified),
        }

    def export_reviews(self, output_path: Path):
        """Export all reviews to JSON file."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_specimens": len(self.reviews),
            "reviews": [review.to_dict() for review in self.reviews.values()],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.reviews)} reviews to {output_path}")
