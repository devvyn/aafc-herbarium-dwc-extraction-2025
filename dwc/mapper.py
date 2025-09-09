from __future__ import annotations

from typing import Any, Dict, Iterable

from .schema import DwcRecord, resolve_term
from . import schema
from .normalize import normalize_institution, normalize_vocab, _load_rules
from .validators import validate


_CUSTOM_MAPPINGS: Dict[str, str] = {}


def configure_mappings(mapping: Dict[str, str]) -> None:
    """Register custom field mappings from the configuration."""
    _CUSTOM_MAPPINGS.clear()
    for raw, term in mapping.items():
        _CUSTOM_MAPPINGS[raw.lower()] = term


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

    return record
