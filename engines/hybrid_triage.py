"""Hybrid OCR→GPT Triage Pipeline for Herbarium Digitization

This module implements an intelligent routing system that uses fast OCR engines
to analyze image complexity and quality, then routes images to the most appropriate
processing pipeline:

- Simple/clear labels → Traditional OCR (fast, cheap)
- Complex/botanical labels → GPT-4o-mini (contextual, expensive)
- Poor quality → Preprocessing + retry
- Manual cases → Human review queue

The goal is to maximize extraction quality while minimizing GPT API costs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import re
import statistics

from . import dispatch
from .errors import EngineError


class ProcessingRoute(Enum):
    """Available processing routes for herbarium images."""
    OCR_SUFFICIENT = "ocr_sufficient"      # Traditional OCR can handle this
    GPT_OPTIMAL = "gpt_optimal"            # GPT will provide superior results
    PREPROCESS_RETRY = "preprocess_retry"  # Needs image enhancement first
    MANUAL_REVIEW = "manual_review"        # Requires human intervention
    SKIP_PROCESSING = "skip_processing"    # No text content detected


@dataclass
class TriageResult:
    """Result of image triage analysis."""
    image_path: Path
    recommended_route: ProcessingRoute
    confidence_score: float
    reasoning: List[str]
    ocr_preview: Optional[str] = None
    processing_metadata: Optional[Dict] = None
    estimated_cost: Optional[float] = None
    estimated_quality: Optional[float] = None


@dataclass
class TriageConfig:
    """Configuration for hybrid triage pipeline."""

    # OCR confidence thresholds
    high_confidence_threshold: float = 0.85
    low_confidence_threshold: float = 0.30

    # Text complexity indicators
    min_text_length: int = 10
    max_simple_text_length: int = 100

    # Botanical/scientific content indicators
    botanical_keywords: List[str] = None
    scientific_patterns: List[str] = None

    # Cost optimization
    gpt_cost_per_image: float = 0.02  # Estimated cost in USD
    max_gpt_budget_per_batch: float = 5.00

    # Quality expectations
    target_extraction_quality: float = 0.90

    def __post_init__(self):
        if self.botanical_keywords is None:
            self.botanical_keywords = [
                "herbarium", "specimen", "collector", "det.", "determined",
                "family", "genus", "species", "var.", "subspecies", "forma",
                "locality", "habitat", "elevation", "coordinates", "GPS",
                "date collected", "collection date", "leg.", "coll.",
                "verified", "revised", "updated", "annotation"
            ]

        if self.scientific_patterns is None:
            self.scientific_patterns = [
                r'\b[A-Z][a-z]+ [a-z]+\b',  # Binomial nomenclature
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # Dates
                r'\d+°\d+[\'"]\d*[NS]',  # Coordinates
                r'[A-Z]{2,}\s*\d+',  # Herbarium numbers
                r'#\s*\d+',  # Collection numbers
            ]


class HerbatiumTriageEngine:
    """Intelligence engine for routing herbarium images to optimal processing."""

    def __init__(self, config: Optional[TriageConfig] = None):
        self.config = config or TriageConfig()
        self.logger = logging.getLogger(__name__)

    def analyze_image(self, image_path: Path) -> TriageResult:
        """Analyze image and determine optimal processing route."""

        self.logger.info(f"Analyzing image for triage: {image_path}")

        # Step 1: Quick OCR scan with fast engine
        ocr_preview = self._get_ocr_preview(image_path)

        # Step 2: Analyze OCR results for routing decision
        complexity_analysis = self._analyze_text_complexity(ocr_preview)

        # Step 3: Make routing decision
        route_decision = self._determine_route(ocr_preview, complexity_analysis)

        # Step 4: Generate triage result
        return self._create_triage_result(
            image_path, route_decision, ocr_preview, complexity_analysis
        )

    def _get_ocr_preview(self, image_path: Path) -> Dict:
        """Get quick OCR preview using fast engine."""
        try:
            # Use Tesseract for fast preview (could be configurable)
            text, confidences = dispatch(
                "image_to_text",
                image=image_path,
                engine="tesseract"
            )

            avg_confidence = statistics.mean(confidences) if confidences else 0.0

            return {
                "text": text,
                "confidence": avg_confidence,
                "token_count": len(confidences),
                "char_count": len(text.strip()),
                "success": True
            }

        except EngineError as e:
            self.logger.warning(f"OCR preview failed for {image_path}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "token_count": 0,
                "char_count": 0,
                "success": False,
                "error": str(e)
            }

    def _analyze_text_complexity(self, ocr_result: Dict) -> Dict:
        """Analyze text complexity to inform routing decision."""
        text = ocr_result.get("text", "")
        confidence = ocr_result.get("confidence", 0.0)

        analysis = {
            "confidence_level": self._categorize_confidence(confidence),
            "text_length": len(text.strip()),
            "has_botanical_content": self._detect_botanical_content(text),
            "has_scientific_patterns": self._detect_scientific_patterns(text),
            "text_complexity": self._assess_text_complexity(text),
            "label_indicators": self._detect_label_indicators(text),
            "quality_issues": self._detect_quality_issues(ocr_result)
        }

        return analysis

    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize OCR confidence level."""
        if confidence >= self.config.high_confidence_threshold:
            return "high"
        elif confidence >= self.config.low_confidence_threshold:
            return "medium"
        else:
            return "low"

    def _detect_botanical_content(self, text: str) -> bool:
        """Detect botanical/herbarium-specific content."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.config.botanical_keywords)

    def _detect_scientific_patterns(self, text: str) -> List[str]:
        """Detect scientific patterns in text."""
        matches = []
        for pattern in self.config.scientific_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        return matches

    def _assess_text_complexity(self, text: str) -> str:
        """Assess overall text complexity."""
        if len(text.strip()) < self.config.min_text_length:
            return "minimal"
        elif len(text.strip()) > self.config.max_simple_text_length:
            return "complex"
        elif any(char in text for char in "()[]{}\"'"):
            return "structured"
        else:
            return "simple"

    def _detect_label_indicators(self, text: str) -> List[str]:
        """Detect indicators of multiple or complex labels."""
        indicators = []

        # Multiple sections/fields
        if text.count('\n') > 3:
            indicators.append("multi_line")

        # Handwritten annotations
        if any(word in text.lower() for word in ["det.", "rev.", "upd.", "ann."]):
            indicators.append("annotations")

        # Multiple dates
        date_count = len(re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text))
        if date_count > 1:
            indicators.append("multiple_dates")

        # Abbreviations (common in botanical labels)
        abbrev_count = len(re.findall(r'\b[A-Z]{2,}\b', text))
        if abbrev_count > 2:
            indicators.append("heavy_abbreviations")

        return indicators

    def _detect_quality_issues(self, ocr_result: Dict) -> List[str]:
        """Detect quality issues that might affect processing."""
        issues = []

        if not ocr_result.get("success", True):
            issues.append("ocr_failure")

        confidence = ocr_result.get("confidence", 0.0)
        if confidence < self.config.low_confidence_threshold:
            issues.append("low_confidence")

        char_count = ocr_result.get("char_count", 0)
        if char_count < self.config.min_text_length:
            issues.append("insufficient_text")

        # Check for garbled text patterns
        text = ocr_result.get("text", "")
        if re.search(r'[^\w\s]{3,}', text):  # Multiple consecutive special chars
            issues.append("garbled_text")

        return issues

    def _determine_route(self, ocr_result: Dict, complexity_analysis: Dict) -> ProcessingRoute:
        """Determine optimal processing route based on analysis."""

        # Check for immediate disqualifiers
        if not ocr_result.get("success", True):
            return ProcessingRoute.PREPROCESS_RETRY

        if complexity_analysis["text_length"] < self.config.min_text_length:
            return ProcessingRoute.SKIP_PROCESSING

        # Analyze complexity factors
        confidence_level = complexity_analysis["confidence_level"]
        has_botanical = complexity_analysis["has_botanical_content"]
        has_scientific = bool(complexity_analysis["has_scientific_patterns"])
        text_complexity = complexity_analysis["text_complexity"]
        label_indicators = complexity_analysis["label_indicators"]
        quality_issues = complexity_analysis["quality_issues"]

        # Decision matrix

        # High confidence + simple content → OCR sufficient
        if (confidence_level == "high" and
            text_complexity in ["simple", "minimal"] and
            not has_botanical and
            not label_indicators):
            return ProcessingRoute.OCR_SUFFICIENT

        # Quality issues → Preprocess first
        if "low_confidence" in quality_issues or "garbled_text" in quality_issues:
            return ProcessingRoute.PREPROCESS_RETRY

        # Botanical/scientific content → GPT optimal
        if (has_botanical or has_scientific or
            text_complexity in ["complex", "structured"] or
            label_indicators):
            return ProcessingRoute.GPT_OPTIMAL

        # Medium confidence, simple content → OCR sufficient
        if confidence_level in ["medium", "high"] and text_complexity == "simple":
            return ProcessingRoute.OCR_SUFFICIENT

        # Default to manual review for ambiguous cases
        return ProcessingRoute.MANUAL_REVIEW

    def _create_triage_result(
        self,
        image_path: Path,
        route: ProcessingRoute,
        ocr_result: Dict,
        analysis: Dict
    ) -> TriageResult:
        """Create comprehensive triage result."""

        # Generate reasoning
        reasoning = self._generate_reasoning(route, analysis)

        # Calculate confidence in routing decision
        confidence_score = self._calculate_routing_confidence(route, analysis)

        # Estimate costs and quality
        estimated_cost = self._estimate_processing_cost(route)
        estimated_quality = self._estimate_extraction_quality(route, analysis)

        return TriageResult(
            image_path=image_path,
            recommended_route=route,
            confidence_score=confidence_score,
            reasoning=reasoning,
            ocr_preview=ocr_result.get("text", ""),
            processing_metadata={
                "ocr_confidence": ocr_result.get("confidence", 0.0),
                "analysis": analysis,
                "route_factors": self._get_route_factors(analysis)
            },
            estimated_cost=estimated_cost,
            estimated_quality=estimated_quality
        )

    def _generate_reasoning(self, route: ProcessingRoute, analysis: Dict) -> List[str]:
        """Generate human-readable reasoning for routing decision."""
        reasoning = []

        confidence = analysis["confidence_level"]
        complexity = analysis["text_complexity"]
        botanical = analysis["has_botanical_content"]
        scientific = analysis["has_scientific_patterns"]
        indicators = analysis["label_indicators"]
        issues = analysis["quality_issues"]

        if route == ProcessingRoute.OCR_SUFFICIENT:
            reasoning.append(f"High OCR confidence ({confidence}) with simple text structure")
            if not botanical:
                reasoning.append("No complex botanical terminology detected")

        elif route == ProcessingRoute.GPT_OPTIMAL:
            if botanical:
                reasoning.append("Botanical/herbarium terminology detected")
            if scientific:
                reasoning.append("Scientific patterns (nomenclature, coordinates) found")
            if complexity in ["complex", "structured"]:
                reasoning.append(f"Complex text structure: {complexity}")
            if indicators:
                reasoning.append(f"Label complexity indicators: {', '.join(indicators)}")

        elif route == ProcessingRoute.PREPROCESS_RETRY:
            if issues:
                reasoning.append(f"Quality issues detected: {', '.join(issues)}")
            reasoning.append("Image preprocessing may improve results")

        elif route == ProcessingRoute.MANUAL_REVIEW:
            reasoning.append("Ambiguous case requiring human assessment")

        elif route == ProcessingRoute.SKIP_PROCESSING:
            reasoning.append("Insufficient text content detected")

        return reasoning

    def _calculate_routing_confidence(self, route: ProcessingRoute, analysis: Dict) -> float:
        """Calculate confidence in the routing decision."""
        confidence_factors = []

        # OCR confidence factor
        ocr_conf = analysis.get("ocr_confidence", 0.0)
        confidence_factors.append(min(ocr_conf, 1.0))

        # Text length factor
        text_len = analysis.get("text_length", 0)
        length_factor = min(text_len / 50.0, 1.0)  # Normalize to 50 chars
        confidence_factors.append(length_factor)

        # Route-specific adjustments
        if route == ProcessingRoute.GPT_OPTIMAL:
            # Higher confidence for clear botanical indicators
            if analysis["has_botanical_content"]:
                confidence_factors.append(0.9)
            if analysis["has_scientific_patterns"]:
                confidence_factors.append(0.8)

        elif route == ProcessingRoute.OCR_SUFFICIENT:
            # Higher confidence for simple, clear cases
            if analysis["text_complexity"] == "simple":
                confidence_factors.append(0.9)

        return statistics.mean(confidence_factors) if confidence_factors else 0.5

    def _estimate_processing_cost(self, route: ProcessingRoute) -> float:
        """Estimate processing cost for the route."""
        costs = {
            ProcessingRoute.OCR_SUFFICIENT: 0.001,  # Very cheap
            ProcessingRoute.GPT_OPTIMAL: self.config.gpt_cost_per_image,
            ProcessingRoute.PREPROCESS_RETRY: 0.005,  # OCR + preprocessing
            ProcessingRoute.MANUAL_REVIEW: 0.50,  # Human time
            ProcessingRoute.SKIP_PROCESSING: 0.0
        }
        return costs.get(route, 0.0)

    def _estimate_extraction_quality(self, route: ProcessingRoute, analysis: Dict) -> float:
        """Estimate expected extraction quality for the route."""
        base_quality = {
            ProcessingRoute.OCR_SUFFICIENT: 0.80,
            ProcessingRoute.GPT_OPTIMAL: 0.95,
            ProcessingRoute.PREPROCESS_RETRY: 0.70,
            ProcessingRoute.MANUAL_REVIEW: 0.98,
            ProcessingRoute.SKIP_PROCESSING: 0.0
        }

        quality = base_quality.get(route, 0.5)

        # Adjust based on complexity
        if analysis["text_complexity"] == "complex" and route != ProcessingRoute.GPT_OPTIMAL:
            quality -= 0.15
        elif analysis["has_botanical_content"] and route != ProcessingRoute.GPT_OPTIMAL:
            quality -= 0.20

        return max(0.0, min(1.0, quality))

    def _get_route_factors(self, analysis: Dict) -> Dict:
        """Extract key factors that influenced routing decision."""
        return {
            "confidence_level": analysis["confidence_level"],
            "text_complexity": analysis["text_complexity"],
            "botanical_content": analysis["has_botanical_content"],
            "scientific_patterns": len(analysis["has_scientific_patterns"]),
            "label_indicators": len(analysis["label_indicators"]),
            "quality_issues": len(analysis["quality_issues"])
        }


def analyze_batch_for_triage(
    image_paths: List[Path],
    config: Optional[TriageConfig] = None
) -> List[TriageResult]:
    """Analyze a batch of images for optimal processing routing."""

    engine = HerbatiumTriageEngine(config)
    results = []

    for image_path in image_paths:
        try:
            result = engine.analyze_image(image_path)
            results.append(result)
        except Exception as e:
            logging.error(f"Triage analysis failed for {image_path}: {e}")
            # Create a fallback result
            results.append(TriageResult(
                image_path=image_path,
                recommended_route=ProcessingRoute.MANUAL_REVIEW,
                confidence_score=0.0,
                reasoning=[f"Analysis failed: {str(e)}"],
                estimated_cost=0.0,
                estimated_quality=0.0
            ))

    return results


def get_route_summary(results: List[TriageResult]) -> Dict:
    """Summarize triage results for batch processing decisions."""

    route_counts = {}
    total_cost = 0.0
    avg_quality = 0.0

    for result in results:
        route = result.recommended_route
        route_counts[route.value] = route_counts.get(route.value, 0) + 1
        total_cost += result.estimated_cost or 0.0
        avg_quality += result.estimated_quality or 0.0

    return {
        "total_images": len(results),
        "route_distribution": route_counts,
        "estimated_total_cost": total_cost,
        "estimated_avg_quality": avg_quality / len(results) if results else 0.0,
        "gpt_percentage": route_counts.get("gpt_optimal", 0) / len(results) * 100,
        "cost_per_image": total_cost / len(results) if results else 0.0
    }