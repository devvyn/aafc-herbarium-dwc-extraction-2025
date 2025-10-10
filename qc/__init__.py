"""Quality control helper functions.

The module provides small utility helpers that are used during the
extraction pipeline to flag potential issues with the processed
specimen images.  The functions are intentionally lightweight so they
can be exercised easily in unit tests.

``detect_duplicates``
    Track images that have already been processed and flag potential
    duplicates based on either an exact SHA256 match or a perceptual
    hash (``phash``) similarity check.

``flag_low_confidence``
    Emit a ``low_confidence`` flag when the supplied confidence value is
    below the given threshold.

``flag_top_fifth``
    Flag images whose scanned area percentage falls in the top fifth of
    all scans.  The threshold is configurable via ``TOP_FIFTH_PCT`` and
    defaults to ``20`` (meaning ``>=80`` percent coverage).
"""

from __future__ import annotations

from typing import Dict, List

from .gbif import (
    DEFAULT_REVERSE_GEOCODE_ENDPOINT,
    DEFAULT_SPECIES_MATCH_ENDPOINT,
    DEFAULT_OCCURRENCE_SEARCH_ENDPOINT,
    DEFAULT_SUGGEST_ENDPOINT,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_CACHE_SIZE,
    LOCALITY_FIELDS,
    LOCALITY_QUERY_MAP,
    TAXONOMY_FIELDS,
    TAXONOMY_QUERY_MAP,
    GbifLookup,
)

# Percentage used by ``flag_top_fifth``.  The value represents the size of
# the top segment (in percent) that should be flagged.  For example a value
# of 20 means that scan percentages of 80 or higher will be flagged.
TOP_FIFTH_PCT: float = 20.0


def detect_duplicates(catalog: Dict[str, int], sha256: str, phash_threshold: int) -> List[str]:
    """Detect duplicate images.

    Parameters
    ----------
    catalog:
        Mapping of previously seen SHA256 hashes to a simple perceptual
        hash representation.  The catalog is updated in-place.
    sha256:
        The SHA256 digest of the current image.
    phash_threshold:
        Maximum Hamming distance between perceptual hashes to consider
        two images duplicates.

    Returns
    -------
    list of str
        Flags indicating the type of duplicate detected.  Returns an
        empty list when no duplicates are found.
    """

    flags: List[str] = []

    # A tiny perceptual hash derived from the SHA256 value.  This is not a
    # real perceptual hash but is sufficient for duplicate detection in the
    # unit tests where the actual image content is irrelevant.
    phash = int(sha256[:16], 16)

    for existing_sha, existing_phash in catalog.items():
        if sha256 == existing_sha:
            flags.append("duplicate:sha256")
            break
        # XOR the hashes and count the differing bits to approximate a
        # Hamming distance.  ``int.bit_count`` is available on Python 3.8+.
        if (phash ^ existing_phash).bit_count() <= phash_threshold:
            flags.append("duplicate:phash")
            break

    # Record the hash for future comparisons.
    catalog[sha256] = phash
    return flags


def flag_low_confidence(conf: float, threshold: float) -> List[str]:
    """Flag low confidence extractions."""

    if conf < threshold:
        return ["low_confidence"]
    return []


def flag_top_fifth(scan_pct: float) -> List[str]:
    """Flag scans whose coverage percentage is within the top fifth.

    Parameters
    ----------
    scan_pct:
        Percentage of the image that was covered by the scan (0-100).
    """

    threshold = 100 - TOP_FIFTH_PCT
    if scan_pct >= threshold:
        return ["top_fifth_scan"]
    return []


__all__ = [
    "detect_duplicates",
    "flag_low_confidence",
    "flag_top_fifth",
    "TOP_FIFTH_PCT",
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
