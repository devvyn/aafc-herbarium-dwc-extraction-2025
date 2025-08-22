from __future__ import annotations

import re
from typing import Iterable, List

from .schema import DwcRecord

# Simple ISO date pattern YYYY-MM-DD
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_minimal_fields(record: DwcRecord, minimal_fields: Iterable[str]) -> List[str]:
    """Return a list of required fields missing from ``record``."""

    missing = [field for field in minimal_fields if not getattr(record, field, None)]
    return missing


def validate_event_date(value: str | None) -> bool:
    """Validate that ``value`` conforms to a basic ISO date pattern."""

    if not value:
        return True
    return bool(ISO_DATE_RE.match(value))


def validate(record: DwcRecord, minimal_fields: Iterable[str] = ()) -> List[str]:
    """Validate ``record`` returning a list of flag strings.

    Flags are simple text markers describing which checks failed.  The
    current implementation checks for required fields and validates the
    ``eventDate`` format.
    """

    flags: List[str] = []
    missing = validate_minimal_fields(record, minimal_fields)
    if missing:
        flags.append("missing:" + ",".join(missing))
    if not validate_event_date(record.eventDate):
        flags.append("invalid:eventDate")
    return flags
