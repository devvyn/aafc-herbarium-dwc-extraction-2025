"""Event consumers for extraction pipeline."""

from typing import Optional

from .types import Event, ExtractionEvent


class EarlyValidationError(Exception):
    """Raised when early validation checkpoint fails."""

    pass


class ValidationConsumer:
    """
    Validates extraction success rate at checkpoints.

    Fails fast if success rate drops below threshold.
    """

    def __init__(
        self,
        event_bus,
        early_checkpoint: int = 5,
        early_threshold: float = 0.5,
        warning_threshold: float = 0.7,
        warning_interval: int = 50,
    ):
        """
        Initialize validation consumer.

        Args:
            event_bus: Event bus to subscribe to
            early_checkpoint: Specimen count for early validation (default: 5)
            early_threshold: Minimum success rate for early validation (default: 0.5)
            warning_threshold: Success rate below this triggers warnings (default: 0.7)
            warning_interval: Check every N specimens for warnings (default: 50)
        """
        self.event_bus = event_bus
        self.early_checkpoint = early_checkpoint
        self.early_threshold = early_threshold
        self.warning_threshold = warning_threshold
        self.warning_interval = warning_interval

        # Subscribe to specimen completion events
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.on_specimen)

    def on_specimen(self, event: Event) -> None:
        """Handle specimen completion event."""
        metrics = event.data.get("metrics", {})
        sequence = event.data.get("sequence", 0)

        # Early validation checkpoint
        if sequence == self.early_checkpoint:
            success_rate = metrics.get("success_rate", 0.0)

            if success_rate < self.early_threshold:
                # Emit failure event
                self.event_bus.emit(
                    ExtractionEvent.EXTRACTION_FAILED,
                    {
                        "reason": "early_validation_failed",
                        "success_rate": success_rate,
                        "checkpoint": self.early_checkpoint,
                        "threshold": self.early_threshold,
                    },
                )

                # Raise error to stop extraction
                raise EarlyValidationError(
                    f"Early validation failed: {success_rate:.0%} success rate "
                    f"after {self.early_checkpoint} specimens (threshold: {self.early_threshold:.0%})"
                )
            else:
                # Emit success event
                self.event_bus.emit(
                    ExtractionEvent.VALIDATION_CHECKPOINT,
                    {
                        "checkpoint": self.early_checkpoint,
                        "status": "passed",
                        "success_rate": success_rate,
                    },
                )

        # Continuous monitoring warnings
        if sequence > 0 and sequence % self.warning_interval == 0:
            success_rate = metrics.get("success_rate", 0.0)
            if success_rate < self.warning_threshold:
                self.event_bus.emit(
                    ExtractionEvent.VALIDATION_WARNING,
                    {
                        "sequence": sequence,
                        "success_rate": success_rate,
                        "threshold": self.warning_threshold,
                    },
                )


class MetricsConsumer:
    """
    Aggregates and tracks real-time metrics.
    """

    def __init__(self, event_bus):
        """Initialize metrics consumer."""
        self.event_bus = event_bus
        self.metrics_history = []

        # Subscribe to relevant events
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.on_specimen)
        event_bus.subscribe(ExtractionEvent.VALIDATION_CHECKPOINT, self.on_checkpoint)
        event_bus.subscribe(ExtractionEvent.VALIDATION_WARNING, self.on_warning)

    def on_specimen(self, event: Event) -> None:
        """Record specimen completion metrics."""
        metrics = event.data.get("metrics", {})
        self.metrics_history.append({"timestamp": event.timestamp, "metrics": metrics})

    def on_checkpoint(self, event: Event) -> None:
        """Log validation checkpoint."""
        checkpoint = event.data.get("checkpoint")
        success_rate = event.data.get("success_rate", 0.0)
        print(f"✅ Early validation passed: checkpoint {checkpoint}, {success_rate:.0%} success")

    def on_warning(self, event: Event) -> None:
        """Log validation warning."""
        sequence = event.data.get("sequence")
        success_rate = event.data.get("success_rate", 0.0)
        print(f"⚠️  WARNING: Success rate dropped to {success_rate:.0%} at specimen {sequence}")

    def get_latest_metrics(self) -> Optional[dict]:
        """Get most recent metrics snapshot."""
        if self.metrics_history:
            return self.metrics_history[-1]["metrics"]
        return None


class LoggingConsumer:
    """
    Logs events to console or file.

    Useful for debugging and monitoring.
    """

    def __init__(self, event_bus, verbose: bool = False):
        """
        Initialize logging consumer.

        Args:
            event_bus: Event bus to subscribe to
            verbose: Log all events (default: False, only logs important events)
        """
        self.event_bus = event_bus
        self.verbose = verbose

        # Subscribe to all event types
        if verbose:
            # Subscribe to everything
            for event_type in [
                ExtractionEvent.STARTED,
                ExtractionEvent.SPECIMEN_QUEUED,
                ExtractionEvent.SPECIMEN_PROCESSING,
                ExtractionEvent.SPECIMEN_COMPLETED,
                ExtractionEvent.SPECIMEN_FAILED,
                ExtractionEvent.VALIDATION_CHECKPOINT,
                ExtractionEvent.VALIDATION_WARNING,
                ExtractionEvent.EXTRACTION_COMPLETED,
                ExtractionEvent.EXTRACTION_FAILED,
            ]:
                event_bus.subscribe(event_type, self.on_event)
        else:
            # Only important events
            event_bus.subscribe(ExtractionEvent.VALIDATION_CHECKPOINT, self.on_event)
            event_bus.subscribe(ExtractionEvent.VALIDATION_WARNING, self.on_event)
            event_bus.subscribe(ExtractionEvent.EXTRACTION_FAILED, self.on_event)

    def on_event(self, event: Event) -> None:
        """Log event to console."""
        if self.verbose:
            print(f"[{event.timestamp.isoformat()}] {event.event_type}: {event.data}")
