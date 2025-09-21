#!/usr/bin/env python3
"""OCR Validation Test Runner

This script provides a convenient interface for running OCR validation tests
with different engines, configurations, and sample sets.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import time

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_validation_config(config_path: Path) -> Dict:
    """Load validation configuration from TOML file."""
    with config_path.open("rb") as f:
        return tomllib.load(f)


def run_pytest_tests(
    test_file: Path,
    engines: List[str],
    bundle_path: Optional[Path] = None,
    verbose: bool = False,
    save_output: bool = True
) -> Dict[str, Dict]:
    """Run pytest validation tests and collect results."""
    results = {}

    for engine in engines:
        print(f"\n🔍 Running validation tests for {engine}...")

        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            f"--engine={engine}",
            "--tb=short"
        ]

        if verbose:
            cmd.append("-v")

        if bundle_path:
            cmd.extend(["--bundle-path", str(bundle_path)])

        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            execution_time = time.time() - start_time

            results[engine] = {
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

            if result.returncode == 0:
                print(f"✅ {engine} tests passed ({execution_time:.1f}s)")
            else:
                print(f"❌ {engine} tests failed ({execution_time:.1f}s)")
                if verbose:
                    print(f"Error output: {result.stderr}")

        except subprocess.TimeoutExpired:
            results[engine] = {
                "success": False,
                "execution_time": 300,
                "error": "Test execution timed out",
                "return_code": -1
            }
            print(f"⏱️  {engine} tests timed out")

        except Exception as e:
            results[engine] = {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "return_code": -1
            }
            print(f"💥 {engine} tests crashed: {e}")

    return results


def generate_report(results: Dict[str, Dict], config: Dict, output_path: Path):
    """Generate a comprehensive test report."""

    report = {
        "test_execution": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_engines": len(results),
            "successful_engines": sum(1 for r in results.values() if r["success"]),
        },
        "engine_results": results,
        "configuration": {
            "test_categories": list(config.get("test_categories", {}).keys()),
            "engines_tested": list(results.keys()),
        },
        "summary": {}
    }

    # Calculate summary statistics
    execution_times = [r["execution_time"] for r in results.values() if r["success"]]
    if execution_times:
        report["summary"]["avg_execution_time"] = sum(execution_times) / len(execution_times)
        report["summary"]["max_execution_time"] = max(execution_times)
        report["summary"]["min_execution_time"] = min(execution_times)

    # Save report
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Test report saved to: {output_path}")

    # Print summary
    print("\n📈 Test Summary:")
    print(f"   Engines tested: {len(results)}")
    print(f"   Successful: {report['test_execution']['successful_engines']}")
    print(f"   Failed: {len(results) - report['test_execution']['successful_engines']}")

    if execution_times:
        print(f"   Avg execution time: {report['summary']['avg_execution_time']:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="Run OCR validation tests with stratified image samples"
    )

    parser.add_argument(
        "--engines",
        nargs="+",
        default=["tesseract", "vision_swift", "multilingual"],
        help="OCR engines to test"
    )

    parser.add_argument(
        "--bundle-path",
        type=Path,
        help="Path to test sample bundle (auto-detected if not specified)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/test_validation.toml"),
        help="Path to validation configuration file"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_outputs"),
        help="Directory to save test outputs and reports"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose test output"
    )

    parser.add_argument(
        "--create-bundle",
        action="store_true",
        help="Create test bundle before running tests"
    )

    parser.add_argument(
        "--bucket",
        help="S3 bucket name (required if --create-bundle is used)"
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Sample size for test bundle creation"
    )

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Only create bundle, skip running tests"
    )

    args = parser.parse_args()

    # Load configuration
    if not args.config.exists():
        print(f"❌ Configuration file not found: {args.config}")
        return 1

    config = load_validation_config(args.config)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Create test bundle if requested
    if args.create_bundle:
        if not args.bucket:
            print("❌ --bucket is required when using --create-bundle")
            return 1

        print(f"📦 Creating test sample bundle from S3 bucket: {args.bucket}")

        bundle_cmd = [
            sys.executable,
            "scripts/create_test_sample_bundle.py",
            "--bucket", args.bucket,
            "--sample-size", str(args.sample_size),
            "--output", "test_sample_bundle"
        ]

        try:
            subprocess.run(bundle_cmd, check=True)
            print("✅ Test bundle created successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create test bundle: {e}")
            return 1

    if args.skip_tests:
        print("🚀 Bundle creation complete. Skipping tests as requested.")
        return 0

    # Find test bundle
    bundle_path = args.bundle_path
    if not bundle_path:
        # Auto-detect bundle
        for candidate in [Path("test_sample_bundle"), Path("./test_sample_bundle")]:
            if candidate.exists():
                bundle_path = candidate
                break

        if not bundle_path:
            print("❌ Test bundle not found. Use --create-bundle or --bundle-path")
            return 1

    if not bundle_path.exists():
        print(f"❌ Test bundle not found: {bundle_path}")
        return 1

    print(f"🎯 Using test bundle: {bundle_path}")

    # Find test file
    test_file = Path("tests/integration/test_ocr_sample_validation.py")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1

    # Filter engines based on configuration
    available_engines = set()
    for engine_config in config.get("engines", {}).values():
        available_engines.update(engine_config.get("supported_categories", []))

    if available_engines:
        engines = [e for e in args.engines if e in config.get("engines", {})]
    else:
        engines = args.engines

    if not engines:
        print("❌ No valid engines specified")
        return 1

    print(f"🚀 Running validation tests for engines: {', '.join(engines)}")

    # Run tests
    results = run_pytest_tests(
        test_file=test_file,
        engines=engines,
        bundle_path=bundle_path,
        verbose=args.verbose
    )

    # Generate report
    report_path = args.output_dir / f"validation_report_{int(time.time())}.json"
    generate_report(results, config, report_path)

    # Return appropriate exit code
    if all(r["success"] for r in results.values()):
        print("\n🎉 All validation tests passed!")
        return 0
    else:
        print("\n⚠️  Some validation tests failed. Check the report for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())