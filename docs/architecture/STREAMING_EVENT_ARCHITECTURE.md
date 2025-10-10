# Streaming Event Architecture

## Problem Statement

**Current Issue:** Batch-oriented processing creates delayed failure detection and poor real-time visibility.

**Recent Example:** Oct 6 extraction processed all 2,885 specimens over 22+ hours, only to discover 0% success rate 4 days later. Total wasted: 22 hours compute + 4 days human time.

**User Requirement:** "I'd like your monitoring to improve, so we don't wait days to discover failed work efforts."

## Architectural Shift

### From Batch to Stream

**Old Pattern (Batch):**
```
Process → Collect All Results → Write File → Analyze → Discover Failure
[22 hours] [instant] [instant] [4 days later] [❌]
```

**New Pattern (Stream):**
```
Process → Stream Result → Validate → Alert/Continue
[30s] [instant] [instant] [immediate] [✅ or ❌]
```

## Event Flow Design

### Core Events

```python
# Event Types
class ExtractionEvent:
    STARTED = "extraction.started"          # Pipeline begins
    SPECIMEN_QUEUED = "specimen.queued"     # Image added to queue
    SPECIMEN_PROCESSING = "specimen.processing"  # OCR/extraction starts
    SPECIMEN_COMPLETED = "specimen.completed"    # Result ready
    SPECIMEN_FAILED = "specimen.failed"     # Error occurred
    VALIDATION_CHECKPOINT = "validation.checkpoint"  # Early validation
    EXTRACTION_COMPLETED = "extraction.completed"   # Pipeline done
    EXTRACTION_FAILED = "extraction.failed"  # Critical failure

# Event Data Structure
{
    "event_type": "specimen.completed",
    "timestamp": "2025-10-10T11:53:42.123Z",
    "run_id": "openrouter_run_20251010_115131",
    "specimen_id": "000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84",
    "sequence": 5,  # 5th specimen in run
    "data": {
        "success": true,
        "fields_extracted": 33,
        "confidence": 0.87,
        "processing_time_ms": 30421
    },
    "metrics": {
        "total_processed": 5,
        "success_count": 5,
        "success_rate": 1.0,
        "avg_processing_time_ms": 31245
    }
}
```

### Event Producers

**Extraction Engine (Producer):**
```python
class StreamingExtractor:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.metrics = MetricsAggregator()

    def process_specimen(self, image_path):
        # Emit processing event
        self.event_bus.emit(ExtractionEvent.SPECIMEN_PROCESSING, {
            "image_path": image_path,
            "sequence": self.current_sequence
        })

        # Do extraction
        result = extract_dwc_data(image_path)

        # Update metrics
        self.metrics.add_result(result)

        # Emit completion event with metrics
        self.event_bus.emit(ExtractionEvent.SPECIMEN_COMPLETED, {
            "result": result,
            "metrics": self.metrics.current_snapshot()
        })

        # Stream result immediately
        self.result_sink.write(result)
        self.result_sink.flush()  # Force disk write
```

### Event Consumers

**Real-Time Validator (Consumer):**
```python
class ValidationConsumer:
    def __init__(self, event_bus):
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.on_specimen)

    def on_specimen(self, event):
        metrics = event.data["metrics"]
        sequence = event.data["sequence"]

        # Early validation checkpoint
        if sequence == 5:
            if metrics["success_rate"] < 0.5:
                self.event_bus.emit(ExtractionEvent.EXTRACTION_FAILED, {
                    "reason": "early_validation_failed",
                    "success_rate": metrics["success_rate"],
                    "checkpoint": 5
                })
                raise EarlyValidationError(f"Only {metrics['success_rate']:.0%} success after 5 specimens")
            else:
                self.event_bus.emit(ExtractionEvent.VALIDATION_CHECKPOINT, {
                    "checkpoint": 5,
                    "status": "passed",
                    "success_rate": metrics["success_rate"]
                })

        # Continuous monitoring
        if sequence % 50 == 0:
            if metrics["success_rate"] < 0.7:
                self.event_bus.emit("validation.warning", {
                    "sequence": sequence,
                    "success_rate": metrics["success_rate"]
                })
```

**Metrics Aggregator (Consumer):**
```python
class MetricsConsumer:
    def __init__(self, event_bus):
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.update_metrics)
        self.metrics_sink = MetricsSink()  # Time-series DB or JSONL

    def update_metrics(self, event):
        # Stream metrics to sink
        self.metrics_sink.write({
            "timestamp": event.timestamp,
            "success_rate": event.data["metrics"]["success_rate"],
            "throughput": event.data["metrics"]["specimens_per_minute"],
            "avg_confidence": event.data["metrics"]["avg_confidence"]
        })
        self.metrics_sink.flush()
```

**Dashboard Consumer (Consumer):**
```python
class DashboardConsumer:
    def __init__(self, event_bus):
        event_bus.subscribe(ExtractionEvent.SPECIMEN_COMPLETED, self.update_display)
        self.latest_metrics = None

    def update_display(self, event):
        self.latest_metrics = event.data["metrics"]
        # Web dashboard polls this, or we push via WebSocket

    def get_current_metrics(self):
        return self.latest_metrics
```

## Implementation Options

### Option 1: Simple In-Memory Event Bus (Quick Win)

**Pros:**
- No external dependencies
- Simple to implement
- Works for single-process extraction
- Immediate improvement over current batch approach

**Cons:**
- Not persistent (lost on crash)
- Single process only
- Can't distribute workload

**Implementation:**
```python
class SimpleEventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type, handler):
        self.subscribers[event_type].append(handler)

    def emit(self, event_type, data):
        event = Event(event_type, data, timestamp=datetime.now(UTC))
        for handler in self.subscribers[event_type]:
            handler(event)
```

**Use Case:** Current OpenRouter extraction (single process, immediate feedback)

### Option 2: File-Based Event Log (Persistent)

**Pros:**
- Persistent across restarts
- Simple append-only JSONL
- Easy to replay/analyze
- No external services needed

**Cons:**
- No real-time push notifications
- Requires polling
- Single machine only

**Implementation:**
```python
class FileEventBus:
    def __init__(self, event_log_path):
        self.event_log = open(event_log_path, "a")

    def emit(self, event_type, data):
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data
        }
        self.event_log.write(json.dumps(event) + "\n")
        self.event_log.flush()

    def subscribe(self, event_type, handler):
        # Tail the log file and call handler
        for event in self._tail_events():
            if event["event_type"] == event_type:
                handler(event)
```

**Use Case:** Persistent audit trail, replay failed runs, offline analysis

### Option 3: Redis Pub/Sub (Distributed)

**Pros:**
- Real-time push notifications
- Multiple producers/consumers
- Distributed processing
- Battle-tested

**Cons:**
- External dependency (Redis)
- More operational complexity
- Overkill for single machine

**Implementation:**
```python
import redis

class RedisEventBus:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    def emit(self, event_type, data):
        self.redis.publish(event_type, json.dumps(data))

    def subscribe(self, event_type, handler):
        self.pubsub.subscribe(**{event_type: lambda msg: handler(json.loads(msg["data"]))})
        thread = self.pubsub.run_in_thread()
```

**Use Case:** Future distributed processing, multiple machines, high-throughput

### Option 4: Hybrid (File + In-Memory)

**Pros:**
- Persistent AND real-time
- No external dependencies
- Simple to implement
- Best of both worlds

**Cons:**
- Slightly more complex than Option 1
- Still single process

**Implementation:**
```python
class HybridEventBus:
    def __init__(self, event_log_path):
        self.subscribers = defaultdict(list)
        self.event_log = open(event_log_path, "a")

    def emit(self, event_type, data):
        event = Event(event_type, data, timestamp=datetime.now(UTC))

        # Persist to log
        self.event_log.write(json.dumps(event.to_dict()) + "\n")
        self.event_log.flush()

        # Notify subscribers
        for handler in self.subscribers[event_type]:
            handler(event)

    def subscribe(self, event_type, handler):
        self.subscribers[event_type].append(handler)
```

**Use Case:** Current needs + future flexibility

## Recommended Approach

**Phase 1 (Immediate):** Hybrid Event Bus
- Implement `HybridEventBus` in `src/events/bus.py`
- Modify `scripts/extract_openrouter.py` to emit events
- Add `ValidationConsumer` for early validation
- Add `MetricsConsumer` for streaming metrics

**Phase 2 (Next Session):** Enhanced Monitoring
- Add `DashboardConsumer` for web UI
- Implement event replay for debugging
- Add alerting consumers (email, Slack, etc.)

**Phase 3 (Future):** Distributed Processing
- Evaluate Redis Pub/Sub for multi-machine
- Implement worker pools consuming from queue
- Add load balancing and failover

## Data Flow Example

```
User runs: uv run python scripts/extract_openrouter.py

1. EXTRACTION_STARTED event
   → DashboardConsumer: Update status to "running"
   → MetricsConsumer: Initialize metrics snapshot

2. SPECIMEN_PROCESSING event (image 1/2885)
   → DashboardConsumer: Update current specimen

3. SPECIMEN_COMPLETED event (success, 33 fields)
   → ValidationConsumer: Track success (1/1 = 100%)
   → MetricsConsumer: Update success_rate, avg_time
   → ResultSink: Write result to raw.jsonl

... repeat for specimens 2-4 ...

5. SPECIMEN_COMPLETED event (success, 33 fields)
   → ValidationConsumer: Check early validation (5/5 = 100% ✅)
   → VALIDATION_CHECKPOINT event emitted
   → DashboardConsumer: Show "Early validation PASSED"

... continue for remaining 2,880 specimens ...

N. EXTRACTION_COMPLETED event
   → DashboardConsumer: Show final stats
   → MetricsConsumer: Write final metrics
   → NotificationConsumer: Send completion alert
```

## Implementation Roadmap

### Step 1: Event Bus Foundation
- [ ] Create `src/events/` module
- [ ] Implement `HybridEventBus`
- [ ] Define event types in `events/types.py`
- [ ] Add tests for event bus

### Step 2: Integrate with Extraction
- [ ] Refactor `extract_openrouter.py` to use event bus
- [ ] Emit events at key points
- [ ] Replace print statements with event emissions

### Step 3: Add Consumers
- [ ] `ValidationConsumer` for early validation
- [ ] `MetricsConsumer` for streaming metrics
- [ ] `FileConsumer` for result persistence

### Step 4: Dashboard Integration
- [ ] `DashboardConsumer` for web UI
- [ ] WebSocket support for real-time updates
- [ ] Event log viewer for debugging

### Step 5: Testing & Validation
- [ ] Unit tests for event bus
- [ ] Integration tests with extraction
- [ ] End-to-end test with mock extraction

## Benefits

**Immediate Failure Detection:**
- Early validation checkpoint at 5 specimens (not 2,885)
- Continuous success rate monitoring every 50 specimens
- Alert on degraded performance (<70% success)

**Real-Time Visibility:**
- See results as they stream in
- Monitor throughput and confidence
- Track progress without waiting for completion

**Debuggability:**
- Persistent event log for replay
- Understand exactly when/why failures occurred
- Audit trail for scientific reproducibility

**Extensibility:**
- Add new consumers without changing extraction code
- Multiple dashboards/monitors can subscribe
- Easy to add alerting, logging, analytics

**Future Scalability:**
- Drop-in Redis Pub/Sub for distributed processing
- Worker pools for parallel extraction
- Cloud-native event streaming (SQS, Kafka, etc.)

## Next Steps

1. Implement `HybridEventBus` in new `src/events/` module
2. Refactor current extraction to emit events
3. Add validation consumer for early checkpoint
4. Test with small batch (10 specimens)
5. Deploy to full extraction run

**Estimated Time:** 2-3 hours for Phase 1 implementation

**Value:** Prevents future 4-day delayed failure discoveries, provides real-time extraction visibility.
