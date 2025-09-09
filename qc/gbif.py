"""GBIF lookup interface for taxonomy and locality verification.

This module outlines the endpoints, parameter mappings, and result fields
needed to integrate GBIF-based checks into the quality-control pipeline.  It
contains only type stubs and placeholders for future implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

DEFAULT_SPECIES_MATCH_ENDPOINT = "https://api.gbif.org/v1/species/match"
DEFAULT_REVERSE_GEOCODE_ENDPOINT = "https://api.gbif.org/v1/geocode/reverse"

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
    """Stub for GBIF lookup operations."""

    species_match_endpoint: str = DEFAULT_SPECIES_MATCH_ENDPOINT
    reverse_geocode_endpoint: str = DEFAULT_REVERSE_GEOCODE_ENDPOINT

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
        )

    def verify_taxonomy(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of ``record`` with taxonomy fields updated.

        Parameters
        ----------
        record:
            Local record containing at least the fields defined in
            :data:`TAXONOMY_QUERY_MAP`.

        Returns
        -------
        Dict[str, Any]
            Updated record including the fields listed in
            :data:`TAXONOMY_FIELDS`.
        """

        raise NotImplementedError("Taxonomy verification not yet implemented.")

    def verify_locality(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of ``record`` with locality fields updated.

        Parameters
        ----------
        record:
            Local record containing at least ``decimalLatitude`` and
            ``decimalLongitude``.

        Returns
        -------
        Dict[str, Any]
            Updated record including the fields listed in
            :data:`LOCALITY_FIELDS`.
        """

        raise NotImplementedError("Locality verification not yet implemented.")


__all__ = [
    "GbifLookup",
    "DEFAULT_SPECIES_MATCH_ENDPOINT",
    "DEFAULT_REVERSE_GEOCODE_ENDPOINT",
    "TAXONOMY_QUERY_MAP",
    "LOCALITY_QUERY_MAP",
    "TAXONOMY_FIELDS",
    "LOCALITY_FIELDS",
]
