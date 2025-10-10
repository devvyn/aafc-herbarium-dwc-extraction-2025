# Event Bus Integration Guide

## Quick Start: Add Event-Driven Monitoring to Extraction Scripts

This guide shows how to integrate the event bus into existing extraction scripts for real-time monitoring and early failure detection.

## Problem Solved

**Before Event Bus:**
- Batch processing → 22 hours → discover 0% success rate
- 4 days before human notices the failure
- No real-time visibility into extraction progress

**After Event Bus:**
- Checkpoint at specimen 5 → fail in 2.5 minutes if <50% success
- Real-time metrics streaming
- Persistent event log for debugging

## Integration Steps

### Step 1: Import Event System

```python
from pathlib import Path
import sys

# Add src to path (if needed)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from events import (
    HybridEventBus,
    ExtractionEvent,
    ValidationConsumer,
    MetricsConsumer,
)
from events.consumers import EarlyValidationError
```

### Step 2: Initialize Event Bus

```python
def main():
    # Setup output directory
    output_dir = Path("extraction_output")
    output_dir.mkdir(exist_ok=True)

    # Create event log
    event_log = output_dir / "events.jsonl"

    # Initialize event bus
    with HybridEventBus(event_log_path=event_log) as event_bus:
        # Setup consumers
        validator = ValidationConsumer(
            event_bus,
            early_checkpoint=5,      # Validate after 5 specimens
            early_threshold=0.5,     # Require 50% success
            warning_threshold=0.7,   # Warn if <70% success
            warning_interval=50,     # Check every 50 specimens
        )
        metrics = MetricsConsumer(event_bus)

        # Run extraction
        run_extraction(event_bus, output_dir)
```

### Step 3: Emit Events During Extraction

```python
def run_extraction(event_bus, output_dir):
    images = list(Path("images").glob("*.jpg"))

    # Emit start event
    event_bus.emit(
        ExtractionEvent.STARTED,
        {
            "run_id": "extraction_001",
            "total_specimens": len(images),
            "model": "gpt-4o-mini",
        },
    )

    successful = 0
    failed = 0

    try:
        for i, image_path in enumerate(images):
            # Emit processing event
            event_bus.emit(
                ExtractionEvent.SPECIMEN_PROCESSING,
                {
                    "specimen_id": image_path.stem,
                    "sequence": i + 1,
                },
            )

            # Do extraction
            result = extract_specimen(image_path)

            # Track success/failure
            if result.get("dwc") and len(result["dwc"]) > 0:
                successful += 1
                event_type = ExtractionEvent.SPECIMEN_COMPLETED
            else:
                failed += 1
                event_type = ExtractionEvent.SPECIMEN_FAILED

            # Emit completion event with metrics
            event_bus.emit(
                event_type,
                {
                    "specimen_id": image_path.stem,
                    "sequence": i + 1,
                    "result": result,
                    "metrics": {
                        "total_processed": i + 1,
                        "success_count": successful,
                        "failed_count": failed,
                        "success_rate": successful / (i + 1),
                    },
                },
            )

        # Emit completion event
        event_bus.emit(
            ExtractionEvent.EXTRACTION_COMPLETED,
            {
                "run_id": "extraction_001",
                "total_processed": len(images),
                "successful": successful,
                "failed": failed,
                "success_rate": successful / len(images),
            },
        )

    except EarlyValidationError as e:
        # Early validation failed - stop extraction
        print(f"❌ {e}")
        event_bus.emit(
            ExtractionEvent.EXTRACTION_FAILED,
            {
                "run_id": "extraction_001",
                "reason": "early_validation_failed",
                "processed": i + 1,
                "success_rate": successful / (i + 1),
            },
        )
        sys.exit(1)
```

## Real-World Example: OpenRouter Extraction

Here's how to integrate into `scripts/extract_openrouter.py`:

### Before (Current Implementation)

```python
# scripts/extract_openrouter.py (simplified)

def main():
    images = list(args.input.glob("**/*.jpg"))
    output_file = args.output / "raw.jsonl"

    successful = 0
    failed = 0

    with open(output_file, "w") as f:
        for i, image_path in enumerate(tqdm(images)):
            result = extract_specimen(image_path)

            # Stream result
            f.write(json.dumps(result) + "\n")
            f.flush()

            # Track success
            if result.get("dwc"):
                successful += 1
            else:
                failed += 1

            # Manual checkpoint
            if i == 4:
                success_rate = successful / 5
                if success_rate < 0.5:
                    print("❌ EARLY FAILURE DETECTED")
                    sys.exit(1)
```

### After (With Event Bus)

```python
# scripts/extract_openrouter.py (with event bus)

from events import HybridEventBus, ExtractionEvent, ValidationConsumer, MetricsConsumer
from events.consumers import EarlyValidationError

def main():
    images = list(args.input.glob("**/*.jpg"))
    output_file = args.output / "raw.jsonl"
    event_log = args.output / "events.jsonl"

    # Initialize event bus
    with HybridEventBus(event_log_path=event_log) as event_bus:
        # Setup consumers
        validator = ValidationConsumer(event_bus, early_checkpoint=5)
        metrics = MetricsConsumer(event_bus)

        # Emit start event
        event_bus.emit(
            ExtractionEvent.STARTED,
            {
                "run_id": args.output.name,
                "total_specimens": len(images),
                "model": model_id,
            },
        )

        successful = 0
        failed = 0

        try:
            with open(output_file, "w") as f:
                for i, image_path in enumerate(tqdm(images)):
                    # Emit processing event
                    event_bus.emit(
                        ExtractionEvent.SPECIMEN_PROCESSING,
                        {"specimen_id": image_path.stem, "sequence": i + 1},
                    )

                    result = extract_specimen(image_path)

                    # Stream result
                    f.write(json.dumps(result) + "\n")
                    f.flush()

                    # Track success
                    if result.get("dwc"):
                        successful += 1
                        event_type = ExtractionEvent.SPECIMEN_COMPLETED
                    else:
                        failed += 1
                        event_type = ExtractionEvent.SPECIMEN_FAILED

                    # Emit event with metrics (validation happens automatically)
                    event_bus.emit(
                        event_type,
                        {
                            "specimen_id": image_path.stem,
                            "sequence": i + 1,
                            "result": result,
                            "metrics": {
                                "total_processed": i + 1,
                                "success_count": successful,
                                "success_rate": successful / (i + 1),
                            },
                        },
                    )

            # Emit completion event
            event_bus.emit(
                ExtractionEvent.EXTRACTION_COMPLETED,
                {
                    "run_id": args.output.name,
                    "total": len(images),
                    "successful": successful,
                },
            )

        except EarlyValidationError as e:
            print(f"\n❌ Extraction stopped: {e}")
            sys.exit(1)
```

## Benefits

### Before Integration
```bash
# Start extraction
python scripts/extract_openrouter.py

# Wait 22 hours...

# Check results
cat extraction/raw.jsonl | head -1
# {"dwc": {}}  # Empty! 0% success!

# Discover failure 4 days later
# Wasted: 22 hours compute + 4 days human time
```

### After Integration
```bash
# Start extraction
python scripts/extract_openrouter.py

# Output:
# Processing specimen 1/2885...
# Processing specimen 2/2885...
# Processing specimen 3/2885...
# Processing specimen 4/2885...
# Processing specimen 5/2885...
# ❌ Extraction stopped: Early validation failed: 0% success rate after 5 specimens
#
# Total time: 2.5 minutes
# Saved: 21.96 hours of wasted processing
```

## Event Log Analysis

The persistent event log enables debugging and analysis:

```bash
# Count events by type
cat extraction/events.jsonl | jq -r '.event_type' | sort | uniq -c

# Result:
#   1 extraction.started
#   5 specimen.processing
#   5 specimen.failed
#   1 validation.checkpoint
#   1 extraction.failed
```

```bash
# Find when success rate dropped
cat extraction/events.jsonl | \
  jq 'select(.event_type == "specimen.completed") |
      {sequence: .data.sequence, success_rate: .data.metrics.success_rate}'

# Result (time-series):
# {"sequence": 1, "success_rate": 1.0}
# {"sequence": 2, "success_rate": 1.0}
# {"sequence": 3, "success_rate": 1.0}
# {"sequence": 10, "success_rate": 0.8}
# {"sequence": 20, "success_rate": 0.65}  # Dropped below 70% threshold
```

## Custom Consumers

Create custom consumers for specific needs:

### Email Alerting Consumer

```python
class EmailAlertConsumer:
    def __init__(self, event_bus, recipient):
        self.recipient = recipient
        event_bus.subscribe(ExtractionEvent.EXTRACTION_FAILED, self.on_failure)
        event_bus.subscribe(ExtractionEvent.VALIDATION_WARNING, self.on_warning)

    def on_failure(self, event):
        send_email(
            to=self.recipient,
            subject="🚨 Extraction Failed",
            body=f"Early validation failed: {event.data}",
        )

    def on_warning(self, event):
        success_rate = event.data["success_rate"]
        if success_rate < 0.6:  # Critical threshold
            send_email(
                to=self.recipient,
                subject="⚠️ Low Success Rate",
                body=f"Success rate dropped to {success_rate:.0%}",
            )
```

### Slack Notification Consumer

```python
class SlackConsumer:
    def __init__(self, event_bus, webhook_url):
        self.webhook_url = webhook_url
        event_bus.subscribe(ExtractionEvent.VALIDATION_CHECKPOINT, self.on_checkpoint)
        event_bus.subscribe(ExtractionEvent.EXTRACTION_COMPLETED, self.on_complete)

    def on_checkpoint(self, event):
        requests.post(
            self.webhook_url,
            json={
                "text": f"✅ Early validation passed: {event.data['success_rate']:.0%} success"
            },
        )

    def on_complete(self, event):
        requests.post(
            self.webhook_url,
            json={
                "text": f"🎉 Extraction completed: {event.data['successful']}/{event.data['total']}"
            },
        )
```

### Database Metrics Consumer

```python
class DatabaseMetricsConsumer:
    def __init__(self, event_bus, db_conn):
        self.db = db_conn
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.record_metrics)

    def record_metrics(self, event):
        metrics = event.data["metrics"]
        self.db.execute(
            """
            INSERT INTO extraction_metrics (timestamp, success_rate, throughput)
            VALUES (?, ?, ?)
            """,
            (event.timestamp, metrics["success_rate"], metrics.get("specimens_per_minute", 0)),
        )
        self.db.commit()
```

## Testing

Run the demo to verify event bus behavior:

```bash
# Run event bus demonstration
python examples/event_bus_demo.py

# Output shows:
# - Successful extraction with 92% success
# - Failed extraction caught at checkpoint 5 (20% success)
# - Event logs written to demo_event_output/
```

Verify event log contents:

```bash
# View first event
cat demo_event_output/events.jsonl | head -1 | jq

# Result:
# {
#   "event_type": "extraction.started",
#   "timestamp": "2025-10-10T12:00:00.000Z",
#   "data": {
#     "run_id": "demo_run_001",
#     "total_specimens": 25,
#     "model": "demo-model"
#   }
# }
```

## Migration Checklist

When integrating event bus into existing scripts:

- [ ] Import event system (`from events import ...`)
- [ ] Initialize `HybridEventBus` with event log path
- [ ] Add `ValidationConsumer` for early validation
- [ ] Add `MetricsConsumer` for real-time tracking
- [ ] Emit `EXTRACTION_STARTED` at beginning
- [ ] Emit `SPECIMEN_PROCESSING` before each extraction
- [ ] Emit `SPECIMEN_COMPLETED` or `SPECIMEN_FAILED` after each extraction
- [ ] Include metrics in completion events
- [ ] Catch `EarlyValidationError` and exit gracefully
- [ ] Emit `EXTRACTION_COMPLETED` at end
- [ ] Test with small batch (5-10 specimens)
- [ ] Verify event log created and populated
- [ ] Test early validation failure (mock low success rate)

## Performance Impact

**Overhead:**
- Event emission: ~0.1ms per event (negligible vs 30s extraction)
- File I/O: Buffered with flush() - minimal impact
- Validation: Simple arithmetic - <0.01ms

**Total Impact:**
- ~0.2ms per specimen
- ~0.0007% overhead on 30-second extraction
- Effectively zero performance impact

**Benefits:**
- Save 22 hours on failed runs (early detection)
- Real-time visibility into extraction
- Persistent audit trail for debugging

## Next Steps

1. **Test with current extraction**: Add event bus to `scripts/extract_openrouter.py`
2. **Verify early validation**: Test with intentionally broken prompts
3. **Add dashboard integration**: Connect event stream to web UI
4. **Enable alerting**: Add Slack/email consumers for production
5. **Analyze historical runs**: Query event logs to find patterns

## See Also

- [Streaming Event Architecture](STREAMING_EVENT_ARCHITECTURE.md) - Full architecture design
- [examples/event_bus_demo.py](../../examples/event_bus_demo.py) - Working demonstration
- [src/events/](../../src/events/) - Event system implementation
