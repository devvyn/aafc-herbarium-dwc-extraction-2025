from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional, List
from difflib import SequenceMatcher
from collections import defaultdict

from .schema import (
    DwcRecord,
    resolve_term,
    fetch_official_schemas,
    SchemaInfo,
    validate_schema_compatibility,
)
from . import schema
from .normalize import normalize_institution, normalize_vocab, _load_rules
from .validators import validate


_CUSTOM_MAPPINGS: Dict[str, str] = {}
_DYNAMIC_MAPPINGS: Dict[str, str] = {}
_CACHED_SCHEMAS: Optional[Dict[str, SchemaInfo]] = None


def configure_mappings(mapping: Dict[str, str]) -> None:
    """Register custom field mappings from the configuration."""
    _CUSTOM_MAPPINGS.clear()
    for raw, term in mapping.items():
        _CUSTOM_MAPPINGS[raw.lower()] = term


def map_custom_schema(
    record: Dict[str, Any], schema_mapping: Dict[str, str] | None = None
) -> DwcRecord:
    """Translate a record from a custom schema into Darwin Core terms.

    Mappings come from the ``[dwc.custom]`` section loaded via
    :func:`configure_mappings`.  A ``schema_mapping`` argument can override or
    supply additional rules directly.
    """
    data: Dict[str, Any] = {}
    rules = {k.lower(): v for k, v in _load_rules("dwc_rules").get("fields", {}).items()}
    rules.update(_DYNAMIC_MAPPINGS)
    rules.update(_CUSTOM_MAPPINGS)
    if schema_mapping:
        for raw, term in schema_mapping.items():
            rules[raw.lower()] = term
    for raw_key, value in record.items():
        term = resolve_term(str(raw_key))
        if term in schema.DWC_TERMS:
            data[term] = value
            continue
        mapped = rules.get(str(raw_key).lower())
        if mapped in schema.DWC_TERMS:
            data[mapped] = value

    for field in ("institutionCode", "ownerInstitutionCode"):
        if field in data and data[field]:
            data[field] = normalize_institution(str(data[field]))

    vocab_terms = ["basisOfRecord", "typeStatus"]
    for field in vocab_terms:
        if field in data and data[field]:
            data[field] = normalize_vocab(str(data[field]), field)

    record_obj = DwcRecord(**data)
    flags = validate(record_obj, ())
    if flags:
        existing = record_obj.flags.split(";") if record_obj.flags else []
        record_obj.flags = ";".join(existing + flags)

    return record_obj


def map_ocr_to_dwc(ocr_output: Dict[str, Any], minimal_fields: Iterable[str] = ()) -> DwcRecord:
    """Translate OCR output into a :class:`DwcRecord`.

    Parameters
    ----------
    ocr_output: Dict[str, Any]
        Dictionary containing raw OCR/GPT extracted data.  Keys that match
        Darwin Core terms are copied into the resulting model.
    minimal_fields: Iterable[str]
        Optional list of required Darwin Core terms.  Missing fields are
        recorded in the ``flags`` attribute of the returned model.
    """

    data: Dict[str, Any] = {}
    rules = {k.lower(): v for k, v in _load_rules("dwc_rules").get("fields", {}).items()}
    rules.update(_DYNAMIC_MAPPINGS)
    rules.update(_CUSTOM_MAPPINGS)
    for raw_key, value in ocr_output.items():
        term = resolve_term(str(raw_key))
        if term in schema.DWC_TERMS:
            data[term] = value
            continue
        mapped = rules.get(str(raw_key).lower())
        if mapped in schema.DWC_TERMS:
            data[mapped] = value

    # Normalise institution codes
    for field in ("institutionCode", "ownerInstitutionCode"):
        if field in data and data[field]:
            data[field] = normalize_institution(str(data[field]))

    # Normalise vocabulary-based terms
    vocab_terms = ["basisOfRecord", "typeStatus"]
    for field in vocab_terms:
        if field in data and data[field]:
            data[field] = normalize_vocab(str(data[field]), field)

    record = DwcRecord(**data)

    flags = validate(record, minimal_fields)
    if flags:
        existing = record.flags.split(";") if record.flags else []
        record.flags = ";".join(existing + flags)

    # Validate against schemas if configured
    validation_result = validate_mapping_against_schemas(record)
    if not validation_result["validation_passed"]:
        validation_flags = [
            f"invalid_fields:{','.join(validation_result['invalid_field_names'][:3])}"
        ]
        if validation_result["deprecated_field_names"]:
            validation_flags.append(
                f"deprecated_fields:{','.join(validation_result['deprecated_field_names'][:3])}"
            )

        existing = record.flags.split(";") if record.flags else []
        record.flags = ";".join(existing + validation_flags)

    return record


def validate_mapping_against_schemas(
    record: DwcRecord, target_schemas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate a mapped record against target schemas.

    Args:
        record: The DwcRecord to validate
        target_schemas: List of schema names to validate against

    Returns:
        Dictionary containing validation results
    """
    if target_schemas is None:
        target_schemas = ["dwc_simple", "abcd_206"]

    # Get all non-empty fields from the record
    record_dict = record.to_dict()
    populated_fields = [field for field, value in record_dict.items() if value]

    # Validate compatibility
    compatibility = validate_schema_compatibility(populated_fields, target_schemas)

    return {
        "total_fields": len(populated_fields),
        "valid_fields": len(compatibility["valid"]),
        "invalid_fields": len(compatibility["invalid"]),
        "deprecated_fields": len(compatibility["deprecated"]),
        "compatibility_score": len(compatibility["valid"]) / len(populated_fields)
        if populated_fields
        else 0.0,
        "invalid_field_names": compatibility["invalid"],
        "deprecated_field_names": compatibility["deprecated"],
        "validation_passed": len(compatibility["invalid"]) == 0,
    }


def suggest_mapping_improvements(
    unmapped_fields: List[str],
    target_schemas: Optional[List[str]] = None,
    similarity_threshold: float = 0.6,
) -> Dict[str, List[str]]:
    """Suggest mapping improvements for unmapped fields.

    Args:
        unmapped_fields: List of field names that couldn't be mapped
        target_schemas: List of schema names to suggest mappings for
        similarity_threshold: Minimum similarity score for suggestions

    Returns:
        Dictionary mapping unmapped fields to suggested target terms
    """
    global _CACHED_SCHEMAS
    logger = logging.getLogger(__name__)

    if target_schemas is None:
        target_schemas = ["dwc_simple", "abcd_206"]

    try:
        # Ensure we have schemas cached
        if _CACHED_SCHEMAS is None:
            _CACHED_SCHEMAS = fetch_official_schemas()

        if not _CACHED_SCHEMAS:
            logger.warning("No schemas available for suggestions")
            return {}

        # Collect terms from target schemas
        target_terms = set()
        for schema_name in target_schemas:
            if schema_name in _CACHED_SCHEMAS:
                target_terms.update(_CACHED_SCHEMAS[schema_name].terms)

        # Add project terms
        target_terms.update(schema.PROJECT_TERMS)
        target_terms_list = list(target_terms)

        suggestions = {}
        for field in unmapped_fields:
            field_suggestions = []
            field_lower = field.lower()

            # Find similar terms
            for target_term in target_terms_list:
                # Calculate similarity
                similarity = SequenceMatcher(None, field_lower, target_term.lower()).ratio()
                if similarity >= similarity_threshold:
                    field_suggestions.append((target_term, similarity))

            # Sort by similarity and take top suggestions
            field_suggestions.sort(key=lambda x: x[1], reverse=True)
            suggestions[field] = [term for term, _ in field_suggestions[:3]]

        return suggestions

    except Exception as e:
        logger.error(f"Failed to generate mapping suggestions: {e}")
        return {}


def generate_fuzzy_mappings(
    target_terms: List[str], similarity_threshold: float = 0.6, max_suggestions: int = 3
) -> Dict[str, List[str]]:
    """Generate fuzzy mappings for terms based on string similarity.

    Args:
        target_terms: List of terms to match against (e.g., DwC terms)
        similarity_threshold: Minimum similarity score (0.0-1.0)
        max_suggestions: Maximum number of suggestions per term

    Returns:
        Dictionary mapping potential source terms to suggested target terms
    """
    logger = logging.getLogger(__name__)

    # Common variations and patterns to match
    common_variations = {
        "scientific_name": ["scientificName", "species", "taxon"],
        "collector": ["recordedBy", "collected_by"],
        "collection_date": ["eventDate", "date_collected"],
        "latitude": ["decimalLatitude", "lat"],
        "longitude": ["decimalLongitude", "long", "lng"],
        "country": ["country"],
        "province": ["stateProvince", "state"],
        "locality": ["locality", "location"],
        "barcode": ["catalogNumber", "specimen_number"],
        "family": ["family"],
        "genus": ["genus"],
        "habitat": ["habitat", "environment"],
    }

    fuzzy_mappings = defaultdict(list)

    # Generate mappings for common variations
    for source_pattern, target_candidates in common_variations.items():
        for target_candidate in target_candidates:
            if target_candidate in target_terms:
                fuzzy_mappings[source_pattern].append(target_candidate)
                # Add variations of the source pattern
                variations = [
                    source_pattern.replace("_", " "),
                    source_pattern.replace("_", ""),
                    source_pattern.upper(),
                    source_pattern.lower(),
                    source_pattern.title(),
                ]
                for variation in variations:
                    if variation != source_pattern:
                        fuzzy_mappings[variation].append(target_candidate)

    # Generate similarity-based mappings for all target terms
    for target_term in target_terms:
        target_lower = target_term.lower()

        # Generate potential source variations
        potential_sources = [
            target_term,  # Exact match
            target_lower,  # Lowercase
            target_term.upper(),  # Uppercase
            "_".join(target_term.split()),  # Space to underscore
            " ".join(target_term.split("_")),  # Underscore to space
            target_term.replace("decimal", ""),  # Remove decimal prefix
            target_term.replace("verbatim", ""),  # Remove verbatim prefix
        ]

        for source in potential_sources:
            source = source.strip("_").strip()
            if source and source not in fuzzy_mappings:
                fuzzy_mappings[source] = [target_term]

    # Limit suggestions per mapping
    for source_term in fuzzy_mappings:
        fuzzy_mappings[source_term] = fuzzy_mappings[source_term][:max_suggestions]

    logger.info(f"Generated {len(fuzzy_mappings)} fuzzy mappings")
    return dict(fuzzy_mappings)


def auto_generate_mappings_from_schemas(
    schema_names: Optional[List[str]] = None,
    include_fuzzy: bool = True,
    similarity_threshold: float = 0.6,
) -> Dict[str, str]:
    """Automatically generate term mappings from official schemas.

    Args:
        schema_names: List of schema names to use for mapping generation
        include_fuzzy: Whether to include fuzzy/similarity-based mappings
        similarity_threshold: Minimum similarity for fuzzy matches

    Returns:
        Dictionary of generated mappings from various forms to canonical terms
    """
    global _CACHED_SCHEMAS
    logger = logging.getLogger(__name__)

    try:
        # Fetch schemas if not cached
        if _CACHED_SCHEMAS is None:
            _CACHED_SCHEMAS = fetch_official_schemas()

        if not _CACHED_SCHEMAS:
            logger.warning("No schemas available for mapping generation")
            return {}

        # Use specified schemas or all available
        if schema_names:
            schemas_to_use = {
                name: schema for name, schema in _CACHED_SCHEMAS.items() if name in schema_names
            }
        else:
            schemas_to_use = _CACHED_SCHEMAS

        # Collect all terms from selected schemas
        all_terms = set()
        for schema_info in schemas_to_use.values():
            all_terms.update(schema_info.terms)

        # Add project terms
        all_terms.update(schema.PROJECT_TERMS)

        generated_mappings = {}

        # Generate direct mappings (case variations, etc.)
        for term in all_terms:
            variations = [
                term.lower(),
                term.upper(),
                term.replace("_", " "),
                term.replace(" ", "_"),
                term.replace("decimal", "").strip("_"),
                term.replace("verbatim", "").strip("_"),
            ]

            for variation in variations:
                if variation and variation != term:
                    generated_mappings[variation] = term

        # Generate fuzzy mappings if requested
        if include_fuzzy:
            fuzzy_mappings = generate_fuzzy_mappings(list(all_terms), similarity_threshold)

            # Convert fuzzy mappings to direct mappings (take first suggestion)
            for source, targets in fuzzy_mappings.items():
                if source not in generated_mappings and targets:
                    generated_mappings[source] = targets[0]

        logger.info(f"Generated {len(generated_mappings)} automatic mappings")
        return generated_mappings

    except Exception as e:
        logger.error(f"Failed to generate automatic mappings: {e}")
        return {}


def configure_dynamic_mappings(
    schema_names: Optional[List[str]] = None,
    include_fuzzy: bool = True,
    similarity_threshold: float = 0.6,
) -> None:
    """Configure dynamic mappings based on official schemas.

    Args:
        schema_names: List of schema names to use for mapping generation
        include_fuzzy: Whether to include fuzzy/similarity-based mappings
        similarity_threshold: Minimum similarity for fuzzy matches
    """
    global _DYNAMIC_MAPPINGS
    _DYNAMIC_MAPPINGS = auto_generate_mappings_from_schemas(
        schema_names, include_fuzzy, similarity_threshold
    )
