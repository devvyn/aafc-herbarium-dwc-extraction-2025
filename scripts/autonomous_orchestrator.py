#!/usr/bin/env python3
"""
Autonomous Progressive Balancer for Multi-Provider Herbarium Extraction

Implements feedback-driven budget allocation across multiple AI providers:
- Real-time quality/cost monitoring
- Autonomous provider selection
- Progressive rebalancing every N specimens
- Ensemble voting for uncertain cases

Usage:
    python scripts/autonomous_orchestrator.py \\
        --input /tmp/imgcache \\
        --output full_dataset_processing/autonomous_run \\
        --budget 150 \\
        --quality-floor 0.90

"""

import argparse
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


# Provider configurations
class Provider(str, Enum):
    GPT4O_MINI = "gpt-4o-mini"
    GPT4O = "gpt-4o"
    GEMINI_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_FLASH = "gemini-2.5-flash"
    CLAUDE_SONNET = "claude-sonnet-4.5"


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    name: Provider
    cost_per_specimen: float
    batch_api_available: bool
    speed_per_hour: int  # specimens per hour
    proven_quality: Optional[float] = None  # 0.0-1.0, None if untested
    api_key_env: str = ""
    notes: str = ""


# Provider registry with current pricing
PROVIDERS = {
    Provider.GPT4O_MINI: ProviderConfig(
        name=Provider.GPT4O_MINI,
        cost_per_specimen=0.0037,
        batch_api_available=True,
        speed_per_hour=1400,
        proven_quality=0.95,
        api_key_env="OPENAI_API_KEY",
        notes="Proven baseline, 95%+ quality",
    ),
    Provider.GPT4O: ProviderConfig(
        name=Provider.GPT4O,
        cost_per_specimen=0.0722,
        batch_api_available=True,
        speed_per_hour=1400,
        proven_quality=None,
        api_key_env="OPENAI_API_KEY",
        notes="Premium quality, 20× cost",
    ),
    Provider.GEMINI_FLASH_LITE: ProviderConfig(
        name=Provider.GEMINI_FLASH_LITE,
        cost_per_specimen=0.0049,
        batch_api_available=False,
        speed_per_hour=600,
        proven_quality=None,
        api_key_env="GOOGLE_API_KEY",
        notes="Cheapest cross-provider option",
    ),
}


@dataclass
class ExtractionMetrics:
    """Metrics collected from extraction batch."""

    specimens_processed: int
    success_rate: float
    field_coverage: Dict[str, float]
    average_confidence: Dict[str, float]
    cost_spent: float
    time_elapsed: float
    provider: Provider
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Decision:
    """Autonomous decision made by orchestrator."""

    decision_id: str
    timestamp: datetime
    trigger: str
    metrics_considered: Dict[str, any]
    decision: str
    provider_selected: Provider
    specimens_affected: int
    estimated_cost: float
    rationale: str


class AutonomousOrchestrator:
    """
    Orchestrates multi-provider extraction with autonomous decision-making.
    """

    def __init__(
        self,
        budget: float,
        quality_floor: float = 0.90,
        confidence_floor: float = 0.70,
        rebalance_interval: int = 500,
        research_reserve: float = 0.30,  # 30% of budget reserved for experiments
    ):
        """
        Initialize orchestrator.

        Args:
            budget: Total budget in USD
            quality_floor: Minimum acceptable field coverage (0.0-1.0)
            confidence_floor: Minimum acceptable confidence (0.0-1.0)
            rebalance_interval: Specimens between rebalancing decisions
            research_reserve: Fraction of budget reserved for experiments
        """
        self.budget = budget
        self.budget_main = budget * (1 - research_reserve)
        self.budget_research = budget * research_reserve
        self.quality_floor = quality_floor
        self.confidence_floor = confidence_floor
        self.rebalance_interval = rebalance_interval

        self.spent_main = 0.0
        self.spent_research = 0.0
        self.specimens_processed = 0

        self.metrics_history: List[ExtractionMetrics] = []
        self.decisions: List[Decision] = []

    def get_provider_quality(self, provider: Provider) -> Optional[float]:
        """Get proven quality for provider, or None if untested."""
        config = PROVIDERS.get(provider)
        if not config:
            return None
        return config.proven_quality

    def update_provider_quality(self, provider: Provider, quality: float):
        """Update proven quality based on observed performance."""
        config = PROVIDERS.get(provider)
        if config:
            config.proven_quality = quality
            print(f"✅ Updated {provider} proven quality: {quality:.1%}")

    def record_metrics(self, metrics: ExtractionMetrics):
        """Record metrics from completed extraction."""
        self.metrics_history.append(metrics)
        self.specimens_processed += metrics.specimens_processed

        # Update spent budget
        if self.specimens_processed <= self.rebalance_interval:
            # Phase 1 baseline comes from main budget
            self.spent_main += metrics.cost_spent
        else:
            # Later phases may use research budget
            self.spent_research += metrics.cost_spent

    def make_decision(self, specimens_remaining: int, trigger: str) -> Decision:
        """
        Make autonomous decision about next extraction batch.

        Args:
            specimens_remaining: Number of specimens left to process
            trigger: What triggered this decision

        Returns:
            Decision object with provider selection and rationale
        """
        # Get latest metrics
        if not self.metrics_history:
            # No metrics yet, use proven baseline
            provider = Provider.GPT4O_MINI
            rationale = "Initial baseline extraction with proven provider"
        else:
            latest = self.metrics_history[-1]

            # Calculate average field coverage
            avg_coverage = sum(latest.field_coverage.values()) / len(latest.field_coverage)
            avg_confidence = sum(latest.average_confidence.values()) / len(
                latest.average_confidence
            )

            # Decision logic
            if avg_coverage >= 0.95 and avg_confidence >= self.confidence_floor:
                # Quality excellent, continue with current provider
                provider = latest.provider
                rationale = (
                    f"Quality excellent ({avg_coverage:.1%} coverage), continuing with {provider}"
                )

            elif avg_coverage < self.quality_floor:
                # Quality below floor, try alternative provider
                if latest.provider == Provider.GPT4O_MINI:
                    provider = Provider.GEMINI_FLASH_LITE
                    rationale = (
                        f"Quality below floor ({avg_coverage:.1%}), testing Gemini alternative"
                    )
                else:
                    provider = Provider.GPT4O
                    rationale = "Quality issues persist, escalating to premium GPT-4o"

            elif avg_confidence < self.confidence_floor:
                # Low confidence, use premium for selective extraction
                provider = Provider.GPT4O
                rationale = (
                    f"Low confidence ({avg_confidence:.2f}), using premium model selectively"
                )

            else:
                # Quality acceptable, continue
                provider = latest.provider
                rationale = f"Quality acceptable ({avg_coverage:.1%}), continuing {provider}"

        # Calculate specimens for this batch
        config = PROVIDERS[provider]
        batch_size = min(specimens_remaining, self.rebalance_interval)
        estimated_cost = batch_size * config.cost_per_specimen

        # Create decision record
        decision = Decision(
            decision_id=f"decision-{len(self.decisions) + 1:03d}",
            timestamp=datetime.now(),
            trigger=trigger,
            metrics_considered={
                "specimens_processed": self.specimens_processed,
                "budget_spent": self.spent_main + self.spent_research,
                "budget_remaining": self.budget - (self.spent_main + self.spent_research),
                "latest_quality": self.metrics_history[-1].field_coverage
                if self.metrics_history
                else None,
            },
            decision=f"Extract {batch_size} specimens with {provider}",
            provider_selected=provider,
            specimens_affected=batch_size,
            estimated_cost=estimated_cost,
            rationale=rationale,
        )

        self.decisions.append(decision)
        return decision

    def should_enable_ensemble(self) -> bool:
        """Check if ensemble voting should be enabled."""
        if len(self.metrics_history) < 2:
            return False

        # Check if we have extractions from multiple providers on overlapping specimens
        providers_used = set(m.provider for m in self.metrics_history)

        if len(providers_used) >= 2:
            # Compare quality metrics - if high disagreement, enable ensemble
            # (Simplified check - real implementation would compare actual specimen-level results)
            return True

        return False

    def generate_report(self, output_dir: Path):
        """Generate orchestration report with all decisions and outcomes."""
        report = {
            "orchestrator_config": {
                "budget_total": self.budget,
                "budget_main": self.budget_main,
                "budget_research": self.budget_research,
                "quality_floor": self.quality_floor,
                "confidence_floor": self.confidence_floor,
                "rebalance_interval": self.rebalance_interval,
            },
            "execution_summary": {
                "specimens_processed": self.specimens_processed,
                "spent_main": self.spent_main,
                "spent_research": self.spent_research,
                "spent_total": self.spent_main + self.spent_research,
                "budget_utilization": (self.spent_main + self.spent_research) / self.budget,
                "decisions_made": len(self.decisions),
            },
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "decisions": [asdict(d) for d in self.decisions],
            "providers_used": list(set(m.provider for m in self.metrics_history)),
        }

        report_path = output_dir / "orchestration_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📊 Orchestration report saved: {report_path}")
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous progressive balancer for multi-provider extraction"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input directory containing specimen images"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output directory for extraction results"
    )
    parser.add_argument(
        "--budget", type=float, default=150.0, help="Total budget in USD (default: 150)"
    )
    parser.add_argument(
        "--quality-floor",
        type=float,
        default=0.90,
        help="Minimum acceptable field coverage (default: 0.90)",
    )
    parser.add_argument(
        "--confidence-floor",
        type=float,
        default=0.70,
        help="Minimum acceptable confidence (default: 0.70)",
    )
    parser.add_argument(
        "--rebalance-interval",
        type=int,
        default=500,
        help="Specimens between rebalancing decisions (default: 500)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate decisions without executing extractions"
    )

    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Initialize orchestrator
    orchestrator = AutonomousOrchestrator(
        budget=args.budget,
        quality_floor=args.quality_floor,
        confidence_floor=args.confidence_floor,
        rebalance_interval=args.rebalance_interval,
    )

    print("=" * 80)
    print("AUTONOMOUS PROGRESSIVE BALANCER")
    print("=" * 80)
    print(f"Budget: ${args.budget:.2f}")
    print(f"  Main allocation: ${orchestrator.budget_main:.2f}")
    print(f"  Research reserve: ${orchestrator.budget_research:.2f}")
    print(f"Quality floor: {args.quality_floor:.1%}")
    print(f"Confidence floor: {args.confidence_floor:.2f}")
    print(f"Rebalance interval: {args.rebalance_interval} specimens")
    print()

    # Count specimens
    specimens_total = len(list(args.input.glob("*.jpg")))
    specimens_remaining = specimens_total

    print(f"📊 Total specimens: {specimens_total:,}")
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - Simulating decisions only")
        print()

        # Simulate decision-making
        while specimens_remaining > 0:
            decision = orchestrator.make_decision(
                specimens_remaining=specimens_remaining,
                trigger=f"rebalance_at_{orchestrator.specimens_processed}",
            )

            print(f"Decision {decision.decision_id}:")
            print(f"  Trigger: {decision.trigger}")
            print(f"  Decision: {decision.decision}")
            print(f"  Provider: {decision.provider_selected}")
            print(f"  Specimens: {decision.specimens_affected}")
            print(f"  Cost: ${decision.estimated_cost:.2f}")
            print(f"  Rationale: {decision.rationale}")
            print()

            # Simulate metrics (placeholder - would come from actual extraction)
            simulated_metrics = ExtractionMetrics(
                specimens_processed=decision.specimens_affected,
                success_rate=0.98,
                field_coverage={"catalogNumber": 0.95, "scientificName": 0.98},
                average_confidence={"catalogNumber": 0.85, "scientificName": 0.88},
                cost_spent=decision.estimated_cost,
                time_elapsed=decision.specimens_affected
                / PROVIDERS[decision.provider_selected].speed_per_hour
                * 3600,
                provider=decision.provider_selected,
            )

            orchestrator.record_metrics(simulated_metrics)
            specimens_remaining -= decision.specimens_affected

        # Generate report
        orchestrator.generate_report(args.output)

        print("✅ Dry run complete")
        print(f"Total cost: ${orchestrator.spent_main + orchestrator.spent_research:.2f}")
        print(f"Decisions made: {len(orchestrator.decisions)}")

    else:
        print("⚠️  LIVE MODE not yet implemented")
        print("Use --dry-run to simulate autonomous decision-making")
        print()
        print("Next steps:")
        print("1. Review dry-run output")
        print("2. Implement live extraction integration")
        print("3. Add real-time metrics collection")
        print("4. Enable autonomous execution")


if __name__ == "__main__":
    main()
