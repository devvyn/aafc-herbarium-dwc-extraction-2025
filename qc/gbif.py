"""GBIF lookup interface for taxonomy and locality verification.

The module provides a tiny wrapper around the public GBIF API that is
used by the quality-control step to confirm scientific names and
geographic coordinates.  It intentionally exposes only the small subset
of functionality required by the tests but includes hooks for endpoint
configuration and network timeouts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import socket
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

DEFAULT_SPECIES_MATCH_ENDPOINT = "https://api.gbif.org/v1/species/match"
DEFAULT_REVERSE_GEOCODE_ENDPOINT = "https://api.gbif.org/v1/geocode/reverse"
DEFAULT_OCCURRENCE_SEARCH_ENDPOINT = "https://api.gbif.org/v1/occurrence/search"
DEFAULT_SUGGEST_ENDPOINT = "https://api.gbif.org/v1/species/suggest"
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_CACHE_SIZE = 1000

# Mapping of local record fields to GBIF query parameters
TAXONOMY_QUERY_MAP: Dict[str, str] = {
    "scientificName": "name",
    "kingdom": "kingdom",
    "phylum": "phylum",
    "class": "class",
    "order": "order",
    "family": "family",
    "genus": "genus",
    "specificEpithet": "species",
}

LOCALITY_QUERY_MAP: Dict[str, str] = {
    "decimalLatitude": "lat",
    "decimalLongitude": "lng",
}

# Data fields to append or replace after GBIF lookup
TAXONOMY_FIELDS: List[str] = [
    "taxonKey",
    "acceptedTaxonKey",
    "acceptedScientificName",
    "scientificName",
    "rank",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
]

LOCALITY_FIELDS: List[str] = [
    "country",
    "countryCode",
    "stateProvince",
    "decimalLatitude",
    "decimalLongitude",
]


@dataclass
class GbifLookup:
    """Enhanced GBIF lookup client used during quality control with caching and retry logic."""

    species_match_endpoint: str = DEFAULT_SPECIES_MATCH_ENDPOINT
    reverse_geocode_endpoint: str = DEFAULT_REVERSE_GEOCODE_ENDPOINT
    occurrence_search_endpoint: str = DEFAULT_OCCURRENCE_SEARCH_ENDPOINT
    suggest_endpoint: str = DEFAULT_SUGGEST_ENDPOINT
    timeout: float | None = DEFAULT_TIMEOUT
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    cache_size: int = DEFAULT_CACHE_SIZE
    enable_fuzzy_matching: bool = True
    min_confidence_score: float = 0.80
    enable_occurrence_validation: bool = False
    _logger: Optional[logging.Logger] = None

    def __post_init__(self):
        """Initialize logger and configure caching."""
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        # Configure LRU cache for network requests
        self._request_json = lru_cache(maxsize=self.cache_size)(self._request_json_uncached)

    @classmethod
    def from_config(cls, cfg: Dict[str, Any]) -> "GbifLookup":
        """Create a lookup instance from configuration settings."""
        gbif_cfg = cfg.get("qc", {}).get("gbif", {})
        return cls(
            species_match_endpoint=gbif_cfg.get(
                "species_match_endpoint", DEFAULT_SPECIES_MATCH_ENDPOINT
            ),
            reverse_geocode_endpoint=gbif_cfg.get(
                "reverse_geocode_endpoint", DEFAULT_REVERSE_GEOCODE_ENDPOINT
            ),
            occurrence_search_endpoint=gbif_cfg.get(
                "occurrence_search_endpoint", DEFAULT_OCCURRENCE_SEARCH_ENDPOINT
            ),
            suggest_endpoint=gbif_cfg.get("suggest_endpoint", DEFAULT_SUGGEST_ENDPOINT),
            timeout=gbif_cfg.get("timeout", DEFAULT_TIMEOUT),
            retry_attempts=gbif_cfg.get("retry_attempts", DEFAULT_RETRY_ATTEMPTS),
            backoff_factor=gbif_cfg.get("backoff_factor", DEFAULT_BACKOFF_FACTOR),
            cache_size=gbif_cfg.get("cache_size", DEFAULT_CACHE_SIZE),
            enable_fuzzy_matching=gbif_cfg.get("enable_fuzzy_matching", True),
            min_confidence_score=gbif_cfg.get("min_confidence_score", 0.80),
            enable_occurrence_validation=gbif_cfg.get("enable_occurrence_validation", False),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request_json_uncached(self, url: str) -> Any | None:
        """Fetch ``url`` and decode JSON with retry logic, returning ``None`` on errors."""
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                with urlopen(url, timeout=self.timeout) as resp:
                    data = json.load(resp)
                    if self._logger:
                        self._logger.debug(f"GBIF API success: {url} (attempt {attempt + 1})")
                    return data
            except (URLError, HTTPError, json.JSONDecodeError, socket.timeout) as e:
                last_exception = e
                if self._logger:
                    self._logger.warning(f"GBIF API error on attempt {attempt + 1}: {e}")

                if attempt < self.retry_attempts - 1:
                    sleep_time = self.backoff_factor * (2**attempt)
                    time.sleep(sleep_time)

        if self._logger:
            self._logger.error(
                f"GBIF API failed after {self.retry_attempts} attempts: {last_exception}"
            )
        return None

    def _request_json(self, url: str) -> Any | None:
        """Cached wrapper for JSON requests."""
        return self._request_json_uncached(url)

    def verify_taxonomy(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Return a copy of ``record`` with taxonomy fields updated and verification metadata.

        Parameters
        ----------
        record:
            Local record containing at least the fields defined in
            :data:`TAXONOMY_QUERY_MAP`.

        Returns
        -------
        Tuple[Dict[str, Any], Dict[str, Any]]
            Tuple of (updated record, verification metadata) including confidence scores,
            match type, and validation flags.
        """

        params = {
            query: record[field] for field, query in TAXONOMY_QUERY_MAP.items() if record.get(field)
        }

        updated = record.copy()
        metadata = {
            "gbif_taxonomy_verified": False,
            "gbif_match_type": None,
            "gbif_confidence": 0.0,
            "gbif_issues": [],
        }

        if not params:
            metadata["gbif_issues"].append("no_taxonomy_fields")
            return updated, metadata

        url = f"{self.species_match_endpoint}?{urlencode(params)}"
        data = self._request_json(url)
        if not isinstance(data, dict):
            metadata["gbif_issues"].append("api_error")
            return updated, metadata

        # Extract match information
        match_type = data.get("matchType", "UNKNOWN")
        confidence = data.get("confidence", 0)

        metadata["gbif_match_type"] = match_type
        metadata["gbif_confidence"] = confidence

        # Check confidence threshold
        if confidence >= (self.min_confidence_score * 100):  # GBIF confidence is 0-100
            metadata["gbif_taxonomy_verified"] = True
        else:
            metadata["gbif_issues"].append(f"low_confidence_{confidence}")

        # Handle different match types
        if match_type in ["NONE", "HIGHERRANK"]:
            metadata["gbif_issues"].append(f"poor_match_{match_type.lower()}")
            if not self.enable_fuzzy_matching:
                return updated, metadata

        # Map GBIF response to our fields
        if "usageKey" in data:
            data["taxonKey"] = data["usageKey"]
        if "acceptedUsageKey" in data:
            data["acceptedTaxonKey"] = data["acceptedUsageKey"]

        # Update record with verified fields
        for field in TAXONOMY_FIELDS:
            if field in data and data[field]:
                updated[field] = data[field]

        # Add verification status to record
        if "gbif_verification" not in updated:
            updated["gbif_verification"] = {}
        updated["gbif_verification"]["taxonomy"] = metadata

        return updated, metadata

    def verify_locality(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Return a copy of ``record`` with locality fields updated and verification metadata.

        Parameters
        ----------
        record:
            Local record containing at least ``decimalLatitude`` and
            ``decimalLongitude``.

        Returns
        -------
        Tuple[Dict[str, Any], Dict[str, Any]]
            Tuple of (updated record, verification metadata) including coordinate
            validation, distance calculations, and geographic consistency checks.
        """

        params = {
            query: record[field]
            for field, query in LOCALITY_QUERY_MAP.items()
            if record.get(field) is not None
        }

        updated = record.copy()
        metadata = {
            "gbif_locality_verified": False,
            "gbif_coordinate_valid": False,
            "gbif_distance_km": None,
            "gbif_issues": [],
        }

        if not params:
            metadata["gbif_issues"].append("no_coordinates")
            return updated, metadata

        # Validate coordinate ranges
        lat = params.get("lat")
        lng = params.get("lng")
        if lat is not None:
            try:
                lat_val = float(lat)
                if not (-90 <= lat_val <= 90):
                    metadata["gbif_issues"].append("invalid_latitude")
                    return updated, metadata
            except (ValueError, TypeError):
                metadata["gbif_issues"].append("invalid_latitude_format")
                return updated, metadata

        if lng is not None:
            try:
                lng_val = float(lng)
                if not (-180 <= lng_val <= 180):
                    metadata["gbif_issues"].append("invalid_longitude")
                    return updated, metadata
            except (ValueError, TypeError):
                metadata["gbif_issues"].append("invalid_longitude_format")
                return updated, metadata

        url = f"{self.reverse_geocode_endpoint}?{urlencode(params)}"
        data = self._request_json(url)
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            metadata["gbif_issues"].append("api_error")
            return updated, metadata

        metadata["gbif_coordinate_valid"] = True
        metadata["gbif_locality_verified"] = True

        # Calculate distance if original coordinates were provided
        if "decimalLatitude" in record and "decimalLongitude" in record:
            orig_lat = record.get("decimalLatitude")
            orig_lng = record.get("decimalLongitude")
            gbif_lat = data.get("decimalLatitude")
            gbif_lng = data.get("decimalLongitude")

            if all(v is not None for v in [orig_lat, orig_lng, gbif_lat, gbif_lng]):
                try:
                    distance = self._calculate_distance(
                        float(orig_lat), float(orig_lng), float(gbif_lat), float(gbif_lng)
                    )
                    metadata["gbif_distance_km"] = distance

                    # Flag significant coordinate differences (>10km)
                    if distance > 10.0:
                        metadata["gbif_issues"].append(f"coordinate_discrepancy_{distance:.1f}km")
                except (ValueError, TypeError):
                    metadata["gbif_issues"].append("coordinate_calculation_error")

        # Update record with verified fields
        for field in LOCALITY_FIELDS:
            if field in data and data[field]:
                updated[field] = data[field]

        # Add verification status to record
        if "gbif_verification" not in updated:
            updated["gbif_verification"] = {}
        updated["gbif_verification"]["locality"] = metadata

        return updated, metadata

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points in kilometers.

        Uses the Haversine formula for accurate distance calculation.
        """
        import math

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371
        return c * r

    def validate_occurrence(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Validate occurrence data against GBIF occurrence records.

        This method searches for similar occurrence records to validate
        specimen data against known occurrences.

        Parameters
        ----------
        record:
            Local record with taxonomic and geographic data.

        Returns
        -------
        Tuple[Dict[str, Any], Dict[str, Any]]
            Tuple of (updated record, validation metadata).
        """
        if not self.enable_occurrence_validation:
            return record.copy(), {"gbif_occurrence_validation": "disabled"}

        updated = record.copy()
        metadata = {
            "gbif_occurrence_validated": False,
            "gbif_similar_occurrences": 0,
            "gbif_occurrence_issues": [],
        }

        # Build search parameters
        params = {}
        if record.get("scientificName"):
            params["scientificName"] = record["scientificName"]
        if record.get("decimalLatitude") and record.get("decimalLongitude"):
            # Search within 10km radius
            params["decimalLatitude"] = record["decimalLatitude"]
            params["decimalLongitude"] = record["decimalLongitude"]
            params["distanceFromCentroidInMeters"] = "10000"

        if not params:
            metadata["gbif_occurrence_issues"].append("insufficient_search_data")
            return updated, metadata

        # Limit results for performance
        params["limit"] = "20"

        url = f"{self.occurrence_search_endpoint}?{urlencode(params)}"
        data = self._request_json(url)

        if not isinstance(data, dict) or "results" not in data:
            metadata["gbif_occurrence_issues"].append("api_error")
            return updated, metadata

        occurrences = data.get("results", [])
        metadata["gbif_similar_occurrences"] = len(occurrences)

        if occurrences:
            metadata["gbif_occurrence_validated"] = True

            # Add the count to the record for reference
            updated["gbif_similar_occurrence_count"] = len(occurrences)
        else:
            metadata["gbif_occurrence_issues"].append("no_similar_occurrences")

        # Add validation status to record
        if "gbif_verification" not in updated:
            updated["gbif_verification"] = {}
        updated["gbif_verification"]["occurrence"] = metadata

        return updated, metadata


__all__ = [
    "GbifLookup",
    "DEFAULT_SPECIES_MATCH_ENDPOINT",
    "DEFAULT_REVERSE_GEOCODE_ENDPOINT",
    "DEFAULT_OCCURRENCE_SEARCH_ENDPOINT",
    "DEFAULT_SUGGEST_ENDPOINT",
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRY_ATTEMPTS",
    "DEFAULT_BACKOFF_FACTOR",
    "DEFAULT_CACHE_SIZE",
    "TAXONOMY_QUERY_MAP",
    "LOCALITY_QUERY_MAP",
    "TAXONOMY_FIELDS",
    "LOCALITY_FIELDS",
]
