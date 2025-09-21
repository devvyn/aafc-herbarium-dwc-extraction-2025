#!/usr/bin/env python3
"""Hybrid OCR→GPT Processing Pipeline with Intelligent Triage

This script implements the complete hybrid processing workflow:
1. Analyze images with fast OCR for complexity assessment
2. Route images to optimal processing pipeline based on content
3. Process with appropriate engine (OCR vs GPT)
4. Optimize costs while maximizing extraction quality

Perfect for herbarium digitization where some images need GPT's contextual
understanding while others can be handled efficiently with traditional OCR.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.hybrid_triage import (
    TriageConfig,
    analyze_batch_for_triage,
    get_route_summary
)
from engines import dispatch
from engines.gpt.herbarium_contextual import HerbariumContext
from io_utils.read import iter_images


class HybridProcessingPipeline:
    """Complete hybrid OCR→GPT processing pipeline."""

    def __init__(
        self,
        triage_config: Optional[TriageConfig] = None,
        herbarium_context: Optional[HerbariumContext] = None,
        openai_api_key: Optional[str] = None,
        budget_limit: Optional[float] = None
    ):
        self.triage_config = triage_config or TriageConfig()
        self.herbarium_context = herbarium_context or HerbariumContext()
        self.openai_api_key = openai_api_key
        self.budget_limit = budget_limit
        self.logger = logging.getLogger(__name__)

        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "route_counts": {},
            "total_cost": 0.0,
            "processing_times": {},
            "errors": []
        }

    def process_batch(
        self,
        image_paths: List[Path],
        output_dir: Path,
        dry_run: bool = False,
        save_triage_results: bool = True
    ) -> Dict:
        """Process a batch of images with hybrid triage routing."""

        self.logger.info(f"Processing batch of {len(image_paths)} images")

        # Step 1: Analyze all images for triage routing
        self.logger.info("Step 1: Analyzing images for optimal routing...")
        triage_results = analyze_batch_for_triage(image_paths, self.triage_config)

        # Step 2: Generate processing plan
        processing_plan = self._create_processing_plan(triage_results)
        self.logger.info(f"Processing plan: {processing_plan['summary']}")

        # Check budget constraints
        if self.budget_limit and processing_plan['estimated_cost'] > self.budget_limit:
            self.logger.warning(
                f"Estimated cost ${processing_plan['estimated_cost']:.2f} exceeds "
                f"budget limit ${self.budget_limit:.2f}"
            )
            # Could implement cost reduction strategies here
            processing_plan = self._optimize_for_budget(processing_plan)

        if dry_run:
            self.logger.info("DRY RUN: Would process images according to plan")
            return {
                "dry_run": True,
                "processing_plan": processing_plan,
                "triage_results": [asdict(tr) for tr in triage_results]
            }

        # Step 3: Execute processing according to routes
        output_dir.mkdir(parents=True, exist_ok=True)
        processing_results = self._execute_processing_plan(processing_plan, output_dir)

        # Step 4: Save results and analysis
        if save_triage_results:
            self._save_triage_analysis(triage_results, output_dir)

        final_results = {
            "processing_summary": processing_results,
            "triage_analysis": get_route_summary(triage_results),
            "cost_analysis": self._generate_cost_analysis(),
            "processing_plan": processing_plan
        }

        self._save_batch_results(final_results, output_dir)
        return final_results

    def _create_processing_plan(self, triage_results) -> Dict:
        """Create detailed processing plan based on triage results."""

        plan = {
            "routes": {},
            "estimated_cost": 0.0,
            "estimated_time": 0.0,
            "summary": {}
        }

        for result in triage_results:
            route = result.recommended_route.value
            if route not in plan["routes"]:
                plan["routes"][route] = []

            plan["routes"][route].append({
                "image_path": str(result.image_path),
                "confidence": result.confidence_score,
                "reasoning": result.reasoning,
                "estimated_cost": result.estimated_cost,
                "estimated_quality": result.estimated_quality
            })

            plan["estimated_cost"] += result.estimated_cost or 0.0

        # Generate summary
        for route, items in plan["routes"].items():
            plan["summary"][route] = {
                "count": len(items),
                "total_cost": sum(item["estimated_cost"] for item in items),
                "avg_confidence": sum(item["confidence"] for item in items) / len(items)
            }

        return plan

    def _optimize_for_budget(self, processing_plan: Dict) -> Dict:
        """Optimize processing plan to stay within budget constraints."""

        # Simple strategy: convert some GPT cases to OCR
        gpt_items = processing_plan["routes"].get("gpt_optimal", [])
        if not gpt_items:
            return processing_plan

        # Sort by confidence (keep highest confidence GPT cases)
        gpt_items.sort(key=lambda x: x["confidence"], reverse=True)

        budget_remaining = self.budget_limit
        optimized_gpt = []
        converted_to_ocr = []

        for item in gpt_items:
            if budget_remaining >= item["estimated_cost"]:
                optimized_gpt.append(item)
                budget_remaining -= item["estimated_cost"]
            else:
                # Convert to OCR
                item["original_route"] = "gpt_optimal"
                item["estimated_cost"] = 0.001  # OCR cost
                converted_to_ocr.append(item)

        # Update plan
        processing_plan["routes"]["gpt_optimal"] = optimized_gpt
        if "ocr_sufficient" not in processing_plan["routes"]:
            processing_plan["routes"]["ocr_sufficient"] = []
        processing_plan["routes"]["ocr_sufficient"].extend(converted_to_ocr)

        # Recalculate costs
        processing_plan["estimated_cost"] = sum(
            sum(item["estimated_cost"] for item in items)
            for items in processing_plan["routes"].values()
        )

        self.logger.info(f"Budget optimization: Converted {len(converted_to_ocr)} "
                        f"images from GPT to OCR. New cost: ${processing_plan['estimated_cost']:.2f}")

        return processing_plan

    def _execute_processing_plan(self, processing_plan: Dict, output_dir: Path) -> Dict:
        """Execute the processing plan and generate results."""

        results = {
            "successful": 0,
            "failed": 0,
            "by_route": {},
            "outputs": []
        }

        for route, items in processing_plan["routes"].items():
            self.logger.info(f"Processing {len(items)} images via route: {route}")

            route_results = []
            for item in items:
                image_path = Path(item["image_path"])

                try:
                    start_time = time.time()
                    output = self._process_single_image(image_path, route)
                    processing_time = time.time() - start_time

                    route_results.append({
                        "image_path": str(image_path),
                        "success": True,
                        "processing_time": processing_time,
                        "output": output,
                        "route_used": route
                    })

                    results["successful"] += 1
                    self.stats["total_cost"] += item["estimated_cost"]

                except Exception as e:
                    self.logger.error(f"Failed to process {image_path}: {e}")
                    route_results.append({
                        "image_path": str(image_path),
                        "success": False,
                        "error": str(e),
                        "route_used": route
                    })
                    results["failed"] += 1
                    self.stats["errors"].append(str(e))

            results["by_route"][route] = route_results
            results["outputs"].extend(route_results)

        return results

    def _process_single_image(self, image_path: Path, route: str) -> Dict:
        """Process a single image according to its assigned route."""

        if route == "gpt_optimal":
            # Use contextual GPT processing
            text, confidences = dispatch(
                "image_to_text",
                image=image_path,
                engine="gpt_herbarium",
                api_key=self.openai_api_key,
                context=self.herbarium_context
            )

        elif route == "ocr_sufficient":
            # Use traditional OCR (default to Tesseract)
            text, confidences = dispatch(
                "image_to_text",
                image=image_path,
                engine="tesseract"
            )

        elif route == "preprocess_retry":
            # Apply preprocessing then OCR
            # (Would implement preprocessing here)
            text, confidences = dispatch(
                "image_to_text",
                image=image_path,
                engine="tesseract"
            )

        elif route == "manual_review":
            # Queue for manual review
            return {
                "status": "queued_for_manual_review",
                "text": "",
                "confidence": 0.0,
                "requires_human_attention": True
            }

        else:  # skip_processing
            return {
                "status": "skipped",
                "text": "",
                "confidence": 0.0,
                "reason": "No significant text content detected"
            }

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "status": "processed",
            "text": text,
            "confidence": avg_confidence,
            "token_count": len(confidences),
            "char_count": len(text.strip())
        }

    def _save_triage_analysis(self, triage_results, output_dir: Path):
        """Save detailed triage analysis for review."""

        analysis_path = output_dir / "triage_analysis.json"

        analysis_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_images": len(triage_results),
            "triage_results": [asdict(result) for result in triage_results],
            "route_summary": get_route_summary(triage_results)
        }

        with analysis_path.open('w') as f:
            json.dump(analysis_data, f, indent=2, default=str)

        self.logger.info(f"Triage analysis saved to: {analysis_path}")

    def _generate_cost_analysis(self) -> Dict:
        """Generate cost analysis for the batch."""
        return {
            "total_cost": self.stats["total_cost"],
            "cost_per_image": self.stats["total_cost"] / max(1, self.stats["total_processed"]),
            "budget_limit": self.budget_limit,
            "budget_utilization": (self.stats["total_cost"] / self.budget_limit * 100) if self.budget_limit else None
        }

    def _save_batch_results(self, results: Dict, output_dir: Path):
        """Save comprehensive batch processing results."""

        results_path = output_dir / "batch_results.json"

        with results_path.open('w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"Batch results saved to: {results_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Process herbarium images with hybrid OCR→GPT triage"
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory containing herbarium images"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./hybrid_output"),
        help="Output directory for results"
    )

    parser.add_argument(
        "--budget",
        type=float,
        help="Maximum budget for GPT API calls (USD)"
    )

    parser.add_argument(
        "--openai-api-key",
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )

    parser.add_argument(
        "--gpt-threshold",
        type=float,
        default=0.4,
        help="Proportion of images that can use GPT processing"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and plan without actual processing"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging output"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Find images
    if not args.input.exists():
        logger.error(f"Input directory not found: {args.input}")
        return 1

    image_paths = list(iter_images(args.input))
    if not image_paths:
        logger.error(f"No images found in: {args.input}")
        return 1

    logger.info(f"Found {len(image_paths)} images to process")

    # Configure triage
    triage_config = TriageConfig()
    if args.budget:
        triage_config.max_gpt_budget_per_batch = args.budget

    # Configure herbarium context
    herbarium_context = HerbariumContext()

    # Create pipeline
    pipeline = HybridProcessingPipeline(
        triage_config=triage_config,
        herbarium_context=herbarium_context,
        openai_api_key=args.openai_api_key,
        budget_limit=args.budget
    )

    try:
        # Process batch
        results = pipeline.process_batch(
            image_paths=image_paths,
            output_dir=args.output,
            dry_run=args.dry_run
        )

        # Print summary
        if args.dry_run:
            print("\n🎯 DRY RUN ANALYSIS")
            print(f"Total images: {len(image_paths)}")
            print(f"Estimated cost: ${results['processing_plan']['estimated_cost']:.2f}")
            print("Route distribution:")
            for route, summary in results['processing_plan']['summary'].items():
                print(f"  {route}: {summary['count']} images (${summary['total_cost']:.2f})")

        else:
            print("\n🎉 PROCESSING COMPLETE")
            summary = results["processing_summary"]
            print(f"Successful: {summary['successful']}")
            print(f"Failed: {summary['failed']}")
            print(f"Total cost: ${results['cost_analysis']['total_cost']:.2f}")
            print(f"Results saved to: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())