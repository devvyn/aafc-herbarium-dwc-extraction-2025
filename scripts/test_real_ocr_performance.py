#!/usr/bin/env python3
"""Practical OCR effectiveness testing for real herbarium specimen labels.

This script tests OCR performance on actual specimen images to identify
workflow gaps and measure real-world effectiveness for research assistants.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List
import re

# Try to import OCR engines
ocr_engines = {}
try:
    import pytesseract
    from PIL import Image

    ocr_engines["tesseract"] = True
except ImportError:
    ocr_engines["tesseract"] = False

try:
    import subprocess
    import json
    from pathlib import Path

    # Test if Apple Vision Swift is available
    pkg_dir = Path(__file__).resolve().parent.parent / "engines" / "vision_swift"
    if pkg_dir.exists():
        ocr_engines["vision_swift"] = True
    else:
        ocr_engines["vision_swift"] = False
except ImportError:
    ocr_engines["vision_swift"] = False

try:
    from engines.gpt.herbarium_contextual import HerbariumGPTEngine

    ocr_engines["gpt_herbarium"] = True
except ImportError:
    ocr_engines["gpt_herbarium"] = False


class RealWorldOCRTester:
    """Tests OCR engines on real herbarium specimens for practical effectiveness."""

    def __init__(self):
        self.results = []
        self.critical_fields = {
            "scientific_name": r"[A-Z][a-z]+ [a-z]+",
            "collector": r"[A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+",
            "collection_number": r"\d+",
            "date": r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}",
            "location": r"[A-Z][a-z]+(?:, [A-Z][a-z]+)*",
        }

    def test_tesseract_basic(self, image_path: Path) -> Dict:
        """Test basic Tesseract OCR."""
        if not ocr_engines["tesseract"]:
            return {"error": "Tesseract not available"}

        start_time = time.time()
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            processing_time = time.time() - start_time

            return {
                "engine": "tesseract_basic",
                "text": text.strip(),
                "processing_time": processing_time,
                "text_length": len(text.strip()),
                "line_count": len([line for line in text.split("\n") if line.strip()]),
            }
        except Exception as e:
            return {"error": str(e), "engine": "tesseract_basic"}

    def test_vision_swift(self, image_path: Path) -> Dict:
        """Test Apple Vision Swift OCR."""
        if not ocr_engines["vision_swift"]:
            return {"error": "Vision Swift not available"}

        start_time = time.time()
        try:
            # Run Apple Vision Swift directly
            pkg_dir = image_path.parent.parent / "engines" / "vision_swift"
            cmd = ["swift", "run", "--package-path", str(pkg_dir), "vision_swift", str(image_path)]

            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            results = json.loads(proc.stdout)

            # Extract text and calculate confidence
            tokens = [r["text"] for r in results]
            confidences = [r["confidence"] for r in results]
            text = " ".join(tokens)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            processing_time = time.time() - start_time

            return {
                "engine": "vision_swift",
                "text": text,
                "confidence": avg_confidence,
                "processing_time": processing_time,
                "text_length": len(text),
                "line_count": len([line for line in text.split("\n") if line.strip()]),
                "tokens_detected": len(tokens),
                "raw_results": results[:5],  # First 5 results for inspection
            }
        except Exception as e:
            return {"error": str(e), "engine": "vision_swift"}

    def test_gpt_herbarium(self, image_path: Path) -> Dict:
        """Test GPT herbarium-specific processing."""
        if not ocr_engines["gpt_herbarium"]:
            return {"error": "GPT Herbarium engine not available"}

        time.time()
        try:
            # This would require API key setup
            return {
                "engine": "gpt_herbarium",
                "error": "Requires OpenAI API key setup",
                "processing_time": 0,
            }
        except Exception as e:
            return {"error": str(e), "engine": "gpt_herbarium"}

    def extract_critical_fields(self, text: str) -> Dict:
        """Extract critical botanical fields from OCR text."""
        fields_found = {}

        for field, pattern in self.critical_fields.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                fields_found[field] = matches

        return fields_found

    def assess_readability(self, text: str) -> Dict:
        """Assess how readable the extracted text is for a research assistant."""
        assessment = {
            "has_text": len(text.strip()) > 0,
            "readable_lines": 0,
            "gibberish_lines": 0,
            "empty_lines": 0,
            "contains_numbers": bool(re.search(r"\d+", text)),
            "contains_dates": bool(re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", text)),
            "contains_scientific_names": bool(re.search(r"[A-Z][a-z]+ [a-z]+", text)),
            "readability_score": 0,
        }

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            if len(line) < 3:
                assessment["empty_lines"] += 1
            elif len([c for c in line if c.isalpha()]) / len(line) < 0.5:
                assessment["gibberish_lines"] += 1
            else:
                assessment["readable_lines"] += 1

        # Simple readability score
        total_lines = len(lines) if lines else 1
        assessment["readability_score"] = assessment["readable_lines"] / total_lines

        return assessment

    def test_image(self, image_path: Path) -> Dict:
        """Test all available OCR engines on a single image."""
        print(f"\n🔍 Testing: {image_path.name}")

        image_result = {
            "image_path": str(image_path),
            "image_name": image_path.name,
            "engines": {},
            "timestamp": time.time(),
        }

        # Test each available engine
        for engine_name, available in ocr_engines.items():
            if not available:
                print(f"  ⚠️  {engine_name}: Not available")
                continue

            print(f"  🔄 Testing {engine_name}...")

            if engine_name == "tesseract":
                result = self.test_tesseract_basic(image_path)
            elif engine_name == "vision_swift":
                result = self.test_vision_swift(image_path)
            elif engine_name == "gpt_herbarium":
                result = self.test_gpt_herbarium(image_path)
            else:
                continue

            if "error" in result:
                print(f"    ❌ Error: {result['error']}")
                image_result["engines"][engine_name] = result
                continue

            # Analyze the results
            text = result.get("text", "")
            critical_fields = self.extract_critical_fields(text)
            readability = self.assess_readability(text)

            result.update(
                {
                    "critical_fields_found": critical_fields,
                    "field_count": len(critical_fields),
                    "readability": readability,
                }
            )

            print(f"    ✅ {result['processing_time']:.2f}s, {result['text_length']} chars")
            print(f"    📊 Fields found: {list(critical_fields.keys())}")
            print(f"    📈 Readability: {readability['readability_score']:.2f}")

            image_result["engines"][engine_name] = result

        return image_result

    def run_batch_test(self, image_directory: Path, output_file: Path = None) -> List[Dict]:
        """Run tests on all images in a directory."""
        if not image_directory.exists():
            raise FileNotFoundError(f"Directory not found: {image_directory}")

        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
        image_files = [
            f
            for f in image_directory.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        if not image_files:
            print(f"No image files found in {image_directory}")
            return []

        print(f"🚀 Testing {len(image_files)} images...")
        print(f"📋 Available engines: {[k for k, v in ocr_engines.items() if v]}")

        results = []
        for image_file in image_files[:5]:  # Limit to 5 for initial testing
            try:
                result = self.test_image(image_file)
                results.append(result)
            except Exception as e:
                print(f"❌ Failed to process {image_file}: {e}")
                results.append(
                    {"image_path": str(image_file), "error": str(e), "timestamp": time.time()}
                )

        # Save results
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📁 Results saved to: {output_file}")

        return results

    def generate_summary(self, results: List[Dict]) -> Dict:
        """Generate a summary report for stakeholders."""
        summary = {
            "total_images_tested": len(results),
            "successful_tests": 0,
            "failed_tests": 0,
            "engine_performance": {},
            "critical_insights": [],
        }

        for result in results:
            if "error" in result:
                summary["failed_tests"] += 1
                continue

            summary["successful_tests"] += 1

            for engine_name, engine_result in result.get("engines", {}).items():
                if engine_name not in summary["engine_performance"]:
                    summary["engine_performance"][engine_name] = {
                        "tests_run": 0,
                        "avg_processing_time": 0,
                        "avg_text_length": 0,
                        "avg_field_count": 0,
                        "avg_readability": 0,
                        "success_rate": 0,
                    }

                perf = summary["engine_performance"][engine_name]
                perf["tests_run"] += 1

                if "error" not in engine_result:
                    perf["avg_processing_time"] += engine_result.get("processing_time", 0)
                    perf["avg_text_length"] += engine_result.get("text_length", 0)
                    perf["avg_field_count"] += engine_result.get("field_count", 0)
                    readability_score = engine_result.get("readability", {}).get(
                        "readability_score", 0
                    )
                    perf["avg_readability"] += readability_score

        # Calculate averages
        for engine_name, perf in summary["engine_performance"].items():
            if perf["tests_run"] > 0:
                perf["avg_processing_time"] /= perf["tests_run"]
                perf["avg_text_length"] /= perf["tests_run"]
                perf["avg_field_count"] /= perf["tests_run"]
                perf["avg_readability"] /= perf["tests_run"]
                perf["success_rate"] = perf["tests_run"] / summary["successful_tests"]

        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Test OCR effectiveness on real herbarium specimens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single image
  python test_real_ocr_performance.py single specimen_001.jpg

  # Test all images in a directory
  python test_real_ocr_performance.py batch ./herbarium_images/

  # Test and save results
  python test_real_ocr_performance.py batch ./images/ --output results.json

Research Context:
  This tool helps identify gaps between OCR code performance and
  real-world usability for research assistants reading specimen labels.
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Testing modes")

    # Single image test
    single_parser = subparsers.add_parser("single", help="Test a single image")
    single_parser.add_argument("image", type=Path, help="Path to image file")

    # Batch test
    batch_parser = subparsers.add_parser("batch", help="Test multiple images")
    batch_parser.add_argument("directory", type=Path, help="Directory containing images")
    batch_parser.add_argument("--output", type=Path, help="Save results to JSON file")
    batch_parser.add_argument("--summary", action="store_true", help="Print summary report")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    tester = RealWorldOCRTester()

    try:
        if args.command == "single":
            if not args.image.exists():
                print(f"Image not found: {args.image}")
                return 1

            result = tester.test_image(args.image)
            print(f"\n📋 Results for {args.image.name}:")
            print(json.dumps(result, indent=2, default=str))

        elif args.command == "batch":
            results = tester.run_batch_test(args.directory, args.output)

            if args.summary:
                summary = tester.generate_summary(results)
                print("\n📊 SUMMARY REPORT:")
                print(json.dumps(summary, indent=2, default=str))

                print("\n🎯 KEY INSIGHTS:")
                print(f"  • Tested {summary['total_images_tested']} images")
                print(
                    f"  • Success rate: {summary['successful_tests']}/{summary['total_images_tested']}"
                )

                for engine, perf in summary["engine_performance"].items():
                    if perf["tests_run"] > 0:
                        print(
                            f"  • {engine}: {perf['avg_readability']:.2f} readability, "
                            f"{perf['avg_field_count']:.1f} fields avg"
                        )

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
