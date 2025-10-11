"""
GBIF Validation Integration for Review System

Wraps qc/gbif.py GBIF lookup for integration with review engine.
Provides simplified interface for specimen validation.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add parent to path for qc imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qc.gbif import GbifLookup

logger = logging.getLogger(__name__)


class GBIFValidator:
    """
    Wrapper around GBIF lookup for review system integration.

    Simplifies GBIF API calls and provides review-friendly
    validation results.
    """

    def __init__(
        self,
        min_confidence_score: float = 0.80,
        enable_fuzzy_matching: bool = True,
        enable_occurrence_validation: bool = False,
    ):
        """
        Initialize GBIF validator.

        Args:
            min_confidence_score: Minimum confidence for taxonomy match (0-1)
            enable_fuzzy_matching: Allow fuzzy name matching
            enable_occurrence_validation: Validate against known occurrences
        """
        self.gbif = GbifLookup(
            min_confidence_score=min_confidence_score,
            enable_fuzzy_matching=enable_fuzzy_matching,
            enable_occurrence_validation=enable_occurrence_validation,
        )

        logger.info(
            f"GBIF validator initialized (min confidence: {min_confidence_score}, "
            f"fuzzy: {enable_fuzzy_matching})"
        )

    def verify_taxonomy(self, record: Dict) -> Tuple[Dict, Dict]:
        """
        Verify taxonomic information with GBIF.

        Args:
            record: Darwin Core record with scientificName, family, etc.

        Returns:
            Tuple of (updated_record, validation_metadata)
        """
        try:
            return self.gbif.verify_taxonomy(record)
        except Exception as e:
            logger.error(f"Taxonomy validation error: {e}")
            return record, {
                "gbif_taxonomy_verified": False,
                "gbif_match_type": None,
                "gbif_confidence": 0.0,
                "gbif_issues": [f"validation_error: {str(e)}"],
            }

    def verify_locality(self, record: Dict) -> Tuple[Dict, Dict]:
        """
        Verify geographic information with GBIF.

        Args:
            record: Darwin Core record with decimalLatitude/decimalLongitude

        Returns:
            Tuple of (updated_record, validation_metadata)
        """
        try:
            return self.gbif.verify_locality(record)
        except Exception as e:
            logger.error(f"Locality validation error: {e}")
            return record, {
                "gbif_locality_verified": False,
                "gbif_coordinate_valid": False,
                "gbif_distance_km": None,
                "gbif_issues": [f"validation_error: {str(e)}"],
            }

    def validate_occurrence(self, record: Dict) -> Tuple[Dict, Dict]:
        """
        Validate against known GBIF occurrences.

        Args:
            record: Darwin Core record

        Returns:
            Tuple of (updated_record, validation_metadata)
        """
        if not self.gbif.enable_occurrence_validation:
            return record, {"gbif_occurrence_validation": "disabled"}

        try:
            return self.gbif.validate_occurrence(record)
        except Exception as e:
            logger.error(f"Occurrence validation error: {e}")
            return record, {
                "gbif_occurrence_validated": False,
                "gbif_similar_occurrences": 0,
                "gbif_occurrence_issues": [f"validation_error: {str(e)}"],
            }

    def get_suggestions(self, partial_name: str, limit: int = 10) -> list:
        """
        Get taxonomic name suggestions from GBIF.

        Args:
            partial_name: Partial scientific name
            limit: Maximum number of suggestions

        Returns:
            List of suggested scientific names
        """
        try:
            # Use GBIF suggest endpoint
            import urllib.request
            import urllib.parse
            import json

            params = urllib.parse.urlencode({"q": partial_name, "limit": limit})
            url = f"{self.gbif.suggest_endpoint}?{params}"

            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.load(response)

            suggestions = []
            for result in data:
                if "scientificName" in result:
                    suggestions.append(
                        {
                            "scientificName": result["scientificName"],
                            "rank": result.get("rank", ""),
                            "kingdom": result.get("kingdom", ""),
                            "family": result.get("family", ""),
                        }
                    )

            return suggestions

        except Exception as e:
            logger.error(f"Suggestion lookup error: {e}")
            return []


# Factory function
def create_gbif_validator(config: Optional[Dict] = None) -> GBIFValidator:
    """
    Create GBIF validator from configuration.

    Args:
        config: Optional configuration dict

    Returns:
        Configured GBIFValidator instance
    """
    if config is None:
        config = {}

    return GBIFValidator(
        min_confidence_score=config.get("min_confidence_score", 0.80),
        enable_fuzzy_matching=config.get("enable_fuzzy_matching", True),
        enable_occurrence_validation=config.get("enable_occurrence_validation", False),
    )
