#!/usr/bin/env python3
"""
Event Bus Demonstration

Shows how the event-driven architecture works for real-time extraction monitoring.

Usage:
    python examples/event_bus_demo.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from events import (
    HybridEventBus,
    ExtractionEvent,
    ValidationConsumer,
    MetricsConsumer,
    LoggingConsumer,
)


def simulate_extraction():
    """Simulate an extraction run with event emission."""

    # Create event bus with persistent log
    output_dir = Path("demo_event_output")
    output_dir.mkdir(exist_ok=True)
    event_log = output_dir / "events.jsonl"

    with HybridEventBus(event_log_path=event_log) as bus:
        # Initialize consumers (they work via event subscriptions)
        _validator = ValidationConsumer(
            bus, early_checkpoint=5, early_threshold=0.5, warning_interval=10
        )
        _metrics = MetricsConsumer(bus)
        _logger = LoggingConsumer(bus, verbose=False)

        print("🚀 Starting simulated extraction...\n")

        # Emit extraction started event
        bus.emit(
            ExtractionEvent.STARTED,
            {"run_id": "demo_run_001", "total_specimens": 25, "model": "demo-model"},
        )

        # Simulate processing 25 specimens
        successful = 0
        failed = 0

        for i in range(1, 26):
            specimen_id = f"specimen_{i:03d}"

            # Emit processing event
            bus.emit(
                ExtractionEvent.SPECIMEN_PROCESSING,
                {"specimen_id": specimen_id, "sequence": i},
            )

            # Simulate processing time
            time.sleep(0.1)

            # Simulate success/failure (90% success rate)
            import random

            is_success = random.random() < 0.9

            if is_success:
                successful += 1
                fields_extracted = random.randint(25, 33)

                # Emit success event with metrics
                bus.emit(
                    ExtractionEvent.SPECIMEN_COMPLETED,
                    {
                        "specimen_id": specimen_id,
                        "sequence": i,
                        "result": {
                            "success": True,
                            "fields_extracted": fields_extracted,
                            "confidence": random.uniform(0.7, 0.95),
                        },
                        "metrics": {
                            "total_processed": i,
                            "success_count": successful,
                            "failed_count": failed,
                            "success_rate": successful / i,
                            "specimens_per_minute": 60 / 0.1,  # Simulated
                        },
                    },
                )
                print(f"✅ {specimen_id}: {fields_extracted} fields extracted")
            else:
                failed += 1

                # Emit failure event
                bus.emit(
                    ExtractionEvent.SPECIMEN_FAILED,
                    {
                        "specimen_id": specimen_id,
                        "sequence": i,
                        "error": "Simulated failure",
                        "metrics": {
                            "total_processed": i,
                            "success_count": successful,
                            "failed_count": failed,
                            "success_rate": successful / i,
                        },
                    },
                )
                print(f"❌ {specimen_id}: extraction failed")

        # Emit completion event
        bus.emit(
            ExtractionEvent.EXTRACTION_COMPLETED,
            {
                "run_id": "demo_run_001",
                "total_processed": 25,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / 25,
            },
        )

        print(f"\n✅ Extraction completed: {successful}/25 successful ({successful/25:.0%})")
        print(f"\n📝 Event log written to: {event_log}")
        print(f"   Total events logged: {sum(1 for _ in open(event_log))}")


def simulate_early_failure():
    """Simulate an extraction that fails early validation."""

    output_dir = Path("demo_event_output")
    output_dir.mkdir(exist_ok=True)
    event_log = output_dir / "events_early_failure.jsonl"

    with HybridEventBus(event_log_path=event_log) as bus:
        # Initialize consumers (they work via event subscriptions)
        _validator = ValidationConsumer(bus, early_checkpoint=5, early_threshold=0.5)
        _metrics = MetricsConsumer(bus)

        print("\n🔴 Simulating early validation failure...\n")

        # Emit extraction started event
        bus.emit(
            ExtractionEvent.STARTED,
            {"run_id": "demo_run_002", "total_specimens": 25, "model": "broken-model"},
        )

        # Simulate processing with low success rate (30%)
        successful = 0
        failed = 0

        try:
            for i in range(1, 26):
                specimen_id = f"specimen_{i:03d}"

                # Simulate mostly failures
                is_success = i % 3 == 0  # Only 33% success

                if is_success:
                    successful += 1
                    bus.emit(
                        ExtractionEvent.SPECIMEN_COMPLETED,
                        {
                            "specimen_id": specimen_id,
                            "sequence": i,
                            "result": {"success": True, "fields_extracted": 30},
                            "metrics": {
                                "total_processed": i,
                                "success_count": successful,
                                "success_rate": successful / i,
                            },
                        },
                    )
                    print(f"✅ {specimen_id}: extraction succeeded")
                else:
                    failed += 1
                    bus.emit(
                        ExtractionEvent.SPECIMEN_COMPLETED,
                        {
                            "specimen_id": specimen_id,
                            "sequence": i,
                            "result": {"success": False},
                            "metrics": {
                                "total_processed": i,
                                "success_count": successful,
                                "success_rate": successful / i,
                            },
                        },
                    )
                    print(f"❌ {specimen_id}: extraction failed")

                time.sleep(0.05)

        except Exception as e:
            print(f"\n🛑 Extraction stopped: {e}")
            print(f"   After processing {i} specimens")
            print(f"   Success rate: {successful}/{i} = {successful/i:.0%}")

        print(f"\n📝 Event log written to: {event_log}")


if __name__ == "__main__":
    print("=" * 60)
    print("EVENT BUS DEMONSTRATION")
    print("=" * 60)

    # Demo 1: Successful extraction
    simulate_extraction()

    # Demo 2: Early validation failure
    simulate_early_failure()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("1. ✅ Events are emitted in real-time as processing occurs")
    print("2. ✅ Validation consumer monitors success rate at checkpoints")
    print("3. ✅ Early failure detection stops wasted processing")
    print("4. ✅ All events are logged persistently to JSONL file")
    print("5. ✅ Multiple consumers can subscribe to same events")
    print("\nNext step: Integrate event bus into scripts/extract_openrouter.py")
