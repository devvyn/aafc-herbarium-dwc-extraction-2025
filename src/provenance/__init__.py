"""
Provenance tracking for scientific data lineage.

Implements immutable fragment pattern for end-to-end traceability
from camera capture to GBIF publication.
"""

from .fragment import (
    ProvenanceFragment,
    FragmentType,
    create_extraction_fragment,
    write_provenance_fragments,
)

__all__ = [
    "ProvenanceFragment",
    "FragmentType",
    "create_extraction_fragment",
    "write_provenance_fragments",
]
