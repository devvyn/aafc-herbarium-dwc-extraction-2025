"""Event types for extraction pipeline."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict


class ExtractionEvent:
    """Event type constants for extraction pipeline."""

    STARTED = "extraction.started"
    SPECIMEN_QUEUED = "specimen.queued"
    SPECIMEN_PROCESSING = "specimen.processing"
    SPECIMEN_COMPLETED = "specimen.completed"
    SPECIMEN_FAILED = "specimen.failed"
    VALIDATION_CHECKPOINT = "validation.checkpoint"
    VALIDATION_WARNING = "validation.warning"
    EXTRACTION_COMPLETED = "extraction.completed"
    EXTRACTION_FAILED = "extraction.failed"


@dataclass
class Event:
    """Event with type, data, and timestamp."""

    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }
