"""Event bus for pub/sub pattern."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Callable, List

from .types import Event


class HybridEventBus:
    """
    Hybrid event bus with in-memory pub/sub and persistent event log.

    Features:
    - Real-time event delivery to subscribers (in-memory)
    - Persistent event log (JSONL file)
    - No external dependencies
    - Single process

    Usage:
        bus = HybridEventBus(event_log_path="events.jsonl")
        bus.subscribe("specimen.completed", lambda e: print(e.data))
        bus.emit("specimen.completed", {"id": "abc123", "success": True})
    """

    def __init__(self, event_log_path: Path | str | None = None):
        """
        Initialize event bus.

        Args:
            event_log_path: Path to event log file (optional for logging only)
        """
        self.subscribers: dict[str, List[Callable]] = defaultdict(list)
        self.event_log_path = Path(event_log_path) if event_log_path else None
        self.event_log_file = None

        if self.event_log_path:
            # Open log file in append mode
            self.event_log_file = open(self.event_log_path, "a")

    def emit(self, event_type: str, data: dict) -> None:
        """
        Emit event to all subscribers and log to disk.

        Args:
            event_type: Type of event (e.g., "specimen.completed")
            data: Event data dictionary
        """
        event = Event(event_type=event_type, data=data)

        # Persist to log if enabled
        if self.event_log_file:
            self.event_log_file.write(json.dumps(event.to_dict()) + "\n")
            self.event_log_file.flush()

        # Notify subscribers
        for handler in self.subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                # Don't let consumer errors break the bus
                print(f"Error in event handler for {event_type}: {e}")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to event type.

        Args:
            event_type: Type of event to listen for
            handler: Callback function(event) to handle event
        """
        self.subscribers[event_type].append(handler)

    def close(self) -> None:
        """Close event log file."""
        if self.event_log_file:
            self.event_log_file.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close on exit."""
        self.close()
