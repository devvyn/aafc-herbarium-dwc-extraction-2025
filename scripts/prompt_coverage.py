"""Enhanced GPT prompt template coverage evaluation and testing harness."""

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.unit.test_prompt_coverage import (
    run_prompt_coverage_analysis,
    generate_coverage_report,
    validate_prompt_task,
    REQUIRED_PLACEHOLDERS,
)


def evaluate_basic() -> int:
    """Basic evaluation for backward compatibility. Return 0 if all required placeholders are present."""
    from engines.gpt.image_to_text import load_messages

    missing: list[str] = []
    for task, placeholders in REQUIRED_PLACEHOLDERS.items():
        messages = load_messages(task)
        content = "\n".join(m["content"] for m in messages)
        for token in placeholders:
            if token not in content:
                missing.append(f"{task}: {token}")
    if missing:
        for m in missing:
            print(f"missing placeholder {m}")
        return 1
    print("all prompts contain required placeholders")
    return 0


def evaluate_comprehensive(prompt_dir: Optional[Path] = None, output_format: str = "text") -> int:
    """Comprehensive evaluation using the enhanced testing harness."""
    results = run_prompt_coverage_analysis()

    # Check if custom prompt directory specified
    if prompt_dir:
        custom_results = {}
        for task in REQUIRED_PLACEHOLDERS.keys():
            custom_results[task] = validate_prompt_task(task, prompt_dir)
        results = custom_results

    # Output results in requested format
    if output_format == "json":
        # Convert results to JSON-serializable format
        json_results = {}
        for task, result in results.items():
            json_results[task] = {
                "task": result.task,
                "missing_placeholders": result.missing_placeholders,
                "unexpected_placeholders": result.unexpected_placeholders,
                "content_length": result.content_length,
                "role_coverage": list(result.role_coverage),
                "passed": result.passed,
            }
        print(json.dumps(json_results, indent=2))
    elif output_format == "report":
        print(generate_coverage_report(results))
    else:  # text format
        passed_count = sum(1 for r in results.values() if r.passed)
        total_count = len(results)

        print(f"Prompt Coverage Analysis: {passed_count}/{total_count} tasks passed")
        print()

        for task, result in results.items():
            status = "✓" if result.passed else "✗"
            print(f"{status} {task}")

            if not result.passed:
                if result.missing_placeholders:
                    print(f"    Missing placeholders: {result.missing_placeholders}")
                if result.unexpected_placeholders:
                    print(f"    Unexpected placeholders: {result.unexpected_placeholders}")
                if result.content_length == 0:
                    print("    No content found")

    # Return appropriate exit code
    all_passed = all(r.passed for r in results.values())
    return 0 if all_passed else 1


def validate_custom_prompts(prompt_dir: Path) -> int:
    """Validate prompts in a custom directory."""
    if not prompt_dir.exists():
        print(f"Error: Prompt directory {prompt_dir} does not exist")
        return 1

    print(f"Validating prompts in: {prompt_dir}")
    return evaluate_comprehensive(prompt_dir=prompt_dir)


def benchmark_prompt_effectiveness(prompt_dir: Optional[Path] = None) -> int:
    """Benchmark prompt effectiveness using test data."""
    print("Prompt Effectiveness Benchmark")
    print("=" * 40)

    # This could be extended to run prompts against test images
    # and measure actual OCR accuracy, not just placeholder coverage
    results = (
        run_prompt_coverage_analysis()
        if not prompt_dir
        else {task: validate_prompt_task(task, prompt_dir) for task in REQUIRED_PLACEHOLDERS.keys()}
    )

    effectiveness_scores = {}
    for task, result in results.items():
        # Simple effectiveness score based on completeness
        score = 0.0
        if result.passed:
            score += 50.0  # Base score for passing validation

        # Content quality scoring
        content_score = min(result.content_length / 200.0, 1.0) * 30.0  # Max 30 points
        score += content_score

        # Role coverage scoring
        role_score = len(result.role_coverage) * 10.0  # 10 points per role
        score += role_score

        effectiveness_scores[task] = min(score, 100.0)

    print("\nEffectiveness Scores (0-100):")
    for task, score in effectiveness_scores.items():
        print(f"  {task}: {score:.1f}")

    avg_score = sum(effectiveness_scores.values()) / len(effectiveness_scores)
    print(f"\nAverage Effectiveness: {avg_score:.1f}")

    return 0 if avg_score >= 70.0 else 1


def main():
    """Main CLI interface for prompt coverage evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate GPT prompt template coverage and effectiveness"
    )
    parser.add_argument(
        "--mode",
        choices=["basic", "comprehensive", "custom", "benchmark"],
        default="basic",
        help="Evaluation mode",
    )
    parser.add_argument("--prompt-dir", type=Path, help="Custom prompt directory to validate")
    parser.add_argument(
        "--output-format", choices=["text", "json", "report"], default="text", help="Output format"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Running in {args.mode} mode...")
        if args.prompt_dir:
            print(f"Using custom prompt directory: {args.prompt_dir}")

    try:
        if args.mode == "basic":
            return evaluate_basic()
        elif args.mode == "comprehensive":
            return evaluate_comprehensive(args.prompt_dir, args.output_format)
        elif args.mode == "custom":
            if not args.prompt_dir:
                print("Error: --prompt-dir required for custom mode")
                return 1
            return validate_custom_prompts(args.prompt_dir)
        elif args.mode == "benchmark":
            return benchmark_prompt_effectiveness(args.prompt_dir)
    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    # Backward compatibility: if no arguments, run basic evaluation
    if len(sys.argv) == 1:
        raise SystemExit(evaluate_basic())
    else:
        raise SystemExit(main())
