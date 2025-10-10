"""Pipeline Composer Agent - "Consider All Means Accessible"

This module implements intelligent pipeline composition based on constraints:
- Budget (USD available for processing)
- Deadline (immediate/overnight/flexible)
- Quality (baseline/high/research-grade)

The composer evaluates all available extraction engines and selects the optimal
combination to meet requirements while minimizing cost.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class Deadline(str, Enum):
    """Timeline constraint for extraction."""

    IMMEDIATE = "immediate"  # < 2 hours
    OVERNIGHT = "overnight"  # 12-20 hours OK
    FLEXIBLE = "flexible"  # No time constraint


class Quality(str, Enum):
    """Quality target for extraction."""

    BASELINE = "baseline"  # Free engines, 7 fields, acceptable accuracy
    HIGH = "high"  # Paid engines, 16 fields, layout-aware
    RESEARCH_GRADE = "research-grade"  # Ensemble voting, maximum accuracy


@dataclass
class EngineCapability:
    """Metadata about an extraction engine's capabilities."""

    name: str
    cost_per_specimen: float  # USD per image processed
    fields_extracted: int  # Number of Darwin Core fields
    quality_score: float  # 0.0-1.0 benchmark accuracy
    speed_specimens_per_hour: int  # Processing throughput
    requires_payment: bool  # Requires billing setup
    notes: str


# Engine capability registry
# Based on empirical data from v1.0 baseline and GPT-4o-mini testing
ENGINE_CAPABILITIES: Dict[str, EngineCapability] = {
    "vision": EngineCapability(
        name="Apple Vision API",
        cost_per_specimen=0.0,
        fields_extracted=7,
        quality_score=0.15,  # ~5% scientificName, ~15% partial matches
        speed_specimens_per_hour=2000,
        requires_payment=False,
        notes="FREE, struggles with handwriting, no spatial layout awareness",
    ),
    "gpt_free_tier": EngineCapability(
        name="GPT-4o-mini (Free Tier)",
        cost_per_specimen=0.0,
        fields_extracted=16,
        quality_score=0.70,  # Estimated based on layout-aware prompts
        speed_specimens_per_hour=180,  # ~3 RPM
        requires_payment=False,
        notes="FREE but slow, layout-aware, comprehensive field coverage",
    ),
    "gpt": EngineCapability(
        name="GPT-4o-mini (Paid)",
        cost_per_specimen=0.000555,  # $1.60 / 2885 specimens
        fields_extracted=16,
        quality_score=0.70,
        speed_specimens_per_hour=1400,
        requires_payment=True,
        notes="Fast with billing, layout-aware, 16 fields, batch API available",
    ),
    "gpt4o": EngineCapability(
        name="GPT-4o",
        cost_per_specimen=0.003,  # ~5x more expensive than mini
        fields_extracted=16,
        quality_score=0.85,
        speed_specimens_per_hour=1400,
        requires_payment=True,
        notes="Premium quality, higher cost, best for critical specimens",
    ),
    "tesseract": EngineCapability(
        name="Tesseract OCR",
        cost_per_specimen=0.0,
        fields_extracted=0,  # Produces text, not DWC
        quality_score=0.40,
        speed_specimens_per_hour=1000,
        requires_payment=False,
        notes="FREE OCR fallback, produces raw text for rules engine",
    ),
    "rules": EngineCapability(
        name="Rules Engine",
        cost_per_specimen=0.0,
        fields_extracted=7,
        quality_score=0.50,  # Depends on OCR quality
        speed_specimens_per_hour=10000,
        requires_payment=False,
        notes="FREE, maps text → DWC, works with any OCR output",
    ),
}


@dataclass
class PipelineStrategy:
    """A composed pipeline strategy with cost/quality estimates."""

    steps: List[str]  # Pipeline steps to execute
    estimated_cost: float  # Total USD for full dataset
    estimated_time_hours: float  # Wall clock time
    expected_quality: float  # 0.0-1.0 accuracy estimate
    fields_extracted: int  # Number of DWC fields
    description: str  # Human-readable strategy explanation


class PipelineComposer:
    """Agent that composes optimal extraction pipelines based on constraints."""

    def __init__(self, dataset_size: int = 2885):
        """Initialize composer.

        Args:
            dataset_size: Number of specimens to process (default: AAFC dataset)
        """
        self.dataset_size = dataset_size

    def compose(
        self,
        budget: float,
        deadline: Deadline,
        quality: Quality,
    ) -> PipelineStrategy:
        """Compose optimal pipeline for given constraints.

        Args:
            budget: Available budget in USD (0 = free only)
            deadline: Timeline constraint
            quality: Quality target

        Returns:
            PipelineStrategy with steps and estimates
        """
        # FREE-only constraint
        if budget == 0:
            return self._compose_free(deadline, quality)

        # Paid options available
        if quality == Quality.RESEARCH_GRADE:
            return self._compose_research_grade(budget, deadline)

        if quality == Quality.HIGH:
            return self._compose_high_quality(budget, deadline)

        # Baseline quality - use free path even if budget available
        return self._compose_free(deadline, quality)

    def _compose_free(self, deadline: Deadline, quality: Quality) -> PipelineStrategy:
        """Compose pipeline using only FREE engines.

        Args:
            deadline: Timeline constraint
            quality: Quality target

        Returns:
            PipelineStrategy using free engines
        """
        if deadline == Deadline.IMMEDIATE:
            # Vision API is fastest free option
            return PipelineStrategy(
                steps=["image_to_text", "text_to_dwc"],
                estimated_cost=0.0,
                estimated_time_hours=1.5,
                expected_quality=0.15,
                fields_extracted=7,
                description="Vision API → Rules Engine (FREE, fast, baseline quality)",
            )

        if deadline == Deadline.OVERNIGHT or deadline == Deadline.FLEXIBLE:
            # Use free tier GPT for better quality if time allows
            return PipelineStrategy(
                steps=["image_to_dwc"],  # GPT free tier direct extraction
                estimated_cost=0.0,
                estimated_time_hours=16.0,  # 2885 / 180 per hour
                expected_quality=0.70,
                fields_extracted=16,
                description="GPT-4o-mini FREE tier (slow, high quality, 16 fields)",
            )

        # Default free path
        return PipelineStrategy(
            steps=["image_to_text", "text_to_dwc"],
            estimated_cost=0.0,
            estimated_time_hours=1.5,
            expected_quality=0.15,
            fields_extracted=7,
            description="Vision API → Rules Engine (FREE baseline)",
        )

    def _compose_high_quality(self, budget: float, deadline: Deadline) -> PipelineStrategy:
        """Compose pipeline for HIGH quality target.

        Args:
            budget: Available budget
            deadline: Timeline constraint

        Returns:
            PipelineStrategy optimized for quality
        """
        gpt_cost = self.dataset_size * ENGINE_CAPABILITIES["gpt"].cost_per_specimen

        if budget >= gpt_cost:
            # Can afford paid GPT
            if deadline == Deadline.IMMEDIATE:
                # Use standard API (fast)
                return PipelineStrategy(
                    steps=["image_to_dwc"],
                    estimated_cost=gpt_cost,
                    estimated_time_hours=2.0,
                    expected_quality=0.70,
                    fields_extracted=16,
                    description=f"GPT-4o-mini direct extraction (${gpt_cost:.2f}, 2 hours, 16 fields)",
                )
            else:
                # Use batch API for 50% discount
                batch_cost = gpt_cost * 0.5
                return PipelineStrategy(
                    steps=["image_to_dwc"],  # TODO: Add batch mode flag
                    estimated_cost=batch_cost,
                    estimated_time_hours=24.0,
                    expected_quality=0.70,
                    fields_extracted=16,
                    description=f"GPT-4o-mini batch API (${batch_cost:.2f}, 24 hours, 50% discount)",
                )

        # Budget insufficient for full paid extraction
        # Use progressive enhancement: free baseline + selective paid
        selective_cost = min(budget, gpt_cost)
        selective_fraction = selective_cost / gpt_cost

        return PipelineStrategy(
            steps=[
                "image_to_text",  # Free Vision API
                "text_to_dwc",  # Free rules
                # TODO: Add "validate_confidence" step
                # TODO: Add "gpt_if_needed" for low-confidence specimens
            ],
            estimated_cost=selective_cost,
            estimated_time_hours=3.0,
            expected_quality=0.15 + (0.55 * selective_fraction),  # Blend free + paid
            fields_extracted=7,  # TODO: Selective 16-field extraction
            description=f"Progressive: Vision baseline + GPT for {selective_fraction:.0%} of specimens (${selective_cost:.2f})",
        )

    def _compose_research_grade(self, budget: float, deadline: Deadline) -> PipelineStrategy:
        """Compose pipeline for RESEARCH_GRADE quality (ensemble).

        Args:
            budget: Available budget
            deadline: Timeline constraint

        Returns:
            PipelineStrategy with ensemble voting
        """
        # Ensemble: Vision + GPT + Claude → Vote
        vision_cost = 0.0
        gpt_cost = self.dataset_size * ENGINE_CAPABILITIES["gpt"].cost_per_specimen
        # Assume Claude similar to GPT-4o pricing
        claude_cost = self.dataset_size * 0.003

        total_cost = vision_cost + gpt_cost + claude_cost  # ~$10.25

        if budget >= total_cost:
            return PipelineStrategy(
                steps=[
                    "image_to_text",  # Vision API
                    "image_to_dwc",  # GPT extraction
                    # TODO: "image_to_dwc_claude",  # Claude extraction
                    # TODO: "ensemble_vote",  # Consensus voting
                ],
                estimated_cost=total_cost,
                estimated_time_hours=3.0,
                expected_quality=0.90,  # Ensemble consensus
                fields_extracted=16,
                description=f"Ensemble voting: Vision + GPT + Claude (${total_cost:.2f}, maximum accuracy)",
            )

        # Budget insufficient for full ensemble
        # Use dual-engine voting: Vision + GPT
        dual_cost = vision_cost + gpt_cost

        if budget >= dual_cost:
            return PipelineStrategy(
                steps=[
                    "image_to_text",  # Vision API
                    "image_to_dwc",  # GPT extraction
                    # TODO: "dual_vote",  # Two-engine consensus
                ],
                estimated_cost=dual_cost,
                estimated_time_hours=2.5,
                expected_quality=0.80,
                fields_extracted=16,
                description=f"Dual voting: Vision + GPT (${dual_cost:.2f}, high accuracy)",
            )

        # Fall back to high quality path
        return self._compose_high_quality(budget, deadline)

    def evaluate_all_strategies(self, budget: float, deadline: Deadline) -> List[PipelineStrategy]:
        """Evaluate all viable strategies for given constraints.

        Useful for presenting options to user or meta-project decision agent.

        Args:
            budget: Available budget
            deadline: Timeline constraint

        Returns:
            List of viable PipelineStrategy options, sorted by quality
        """
        strategies = []

        # Always include free baseline
        strategies.append(self._compose_free(deadline, Quality.BASELINE))

        # Free overnight option if time allows
        if deadline != Deadline.IMMEDIATE:
            strategies.append(self._compose_free(deadline, Quality.HIGH))

        # Paid options if budget available
        if budget > 0:
            strategies.append(self._compose_high_quality(budget, deadline))

        # Research-grade if significant budget
        if budget >= 5.0:
            strategies.append(self._compose_research_grade(budget, deadline))

        # Sort by expected quality (descending)
        strategies.sort(key=lambda s: s.expected_quality, reverse=True)

        return strategies


def format_strategy(strategy: PipelineStrategy) -> str:
    """Format pipeline strategy for display.

    Args:
        strategy: PipelineStrategy to format

    Returns:
        Human-readable string representation
    """
    return f"""
Pipeline Strategy
────────────────────────────────────────
{strategy.description}

Steps: {' → '.join(strategy.steps)}
Cost: ${strategy.estimated_cost:.2f}
Time: {strategy.estimated_time_hours:.1f} hours
Quality: {strategy.expected_quality:.0%}
Fields: {strategy.fields_extracted}
"""


# Example usage
if __name__ == "__main__":
    composer = PipelineComposer(dataset_size=2885)

    # Scenario 1: Zero budget, overnight deadline
    print("═" * 60)
    print("SCENARIO 1: Zero Budget, Overnight")
    print("═" * 60)
    strategy = composer.compose(budget=0.0, deadline=Deadline.OVERNIGHT, quality=Quality.HIGH)
    print(format_strategy(strategy))

    # Scenario 2: $1.60 budget, immediate deadline
    print("═" * 60)
    print("SCENARIO 2: $1.60 Budget, Immediate Delivery")
    print("═" * 60)
    strategy = composer.compose(budget=1.60, deadline=Deadline.IMMEDIATE, quality=Quality.HIGH)
    print(format_strategy(strategy))

    # Scenario 3: Research-grade, flexible timeline
    print("═" * 60)
    print("SCENARIO 3: Research-Grade Quality, Flexible Timeline")
    print("═" * 60)
    strategy = composer.compose(
        budget=20.0, deadline=Deadline.FLEXIBLE, quality=Quality.RESEARCH_GRADE
    )
    print(format_strategy(strategy))

    # Show all options for $5 budget
    print("═" * 60)
    print("ALL VIABLE STRATEGIES ($5 budget, overnight)")
    print("═" * 60)
    strategies = composer.evaluate_all_strategies(budget=5.0, deadline=Deadline.OVERNIGHT)
    for i, s in enumerate(strategies, 1):
        print(f"\n{'─' * 60}")
        print(f"Option {i}:")
        print(format_strategy(s))
