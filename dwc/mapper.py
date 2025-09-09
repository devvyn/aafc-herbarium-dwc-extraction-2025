from __future__ import annotations

from typing import Any, Dict, Iterable

from .schema import DwcRecord, resolve_term
from . import schema
from .normalize import normalize_field_name, normalize_institution, normalize_vocab
from .validators import validate


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
    for raw_key, value in ocr_output.items():
        field = normalize_field_name(str(raw_key))
        term = resolve_term(field)
        if term in schema.DWC_TERMS:
            data[term] = value

    # Normalise institution codes
    for field in ("institutionCode", "ownerInstitutionCode"):
        if field in data and data[field]:
            data[field] = normalize_institution(str(data[field]))

    # Normalise vocabulary-based terms
    vocab_terms = ["basisOfRecord"]
    for field in vocab_terms:
        if field in data and data[field]:
            data[field] = normalize_vocab(str(data[field]), field)

    record = DwcRecord(**data)

    flags = validate(record, minimal_fields)
    if flags:
        existing = record.flags.split(";") if record.flags else []
        record.flags = ";".join(existing + flags)

    return record
