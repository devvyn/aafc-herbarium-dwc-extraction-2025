"""Enhanced GPT prompt coverage testing and validation."""

import pytest
from pathlib import Path
from typing import Dict, List, Optional, Set
import re
from dataclasses import dataclass

from engines.gpt.image_to_text import load_messages


@dataclass
class PromptTestResult:
    """Result of prompt validation test."""
    task: str
    missing_placeholders: List[str]
    unexpected_placeholders: List[str]
    content_length: int
    role_coverage: Set[str]
    passed: bool


REQUIRED_PLACEHOLDERS = {
    "image_to_text": ["%LANG%"],
    "text_to_dwc": ["%FIELD%"],
    "image_to_dwc": ["%FIELD%"],
}

# Define expected placeholder patterns
PLACEHOLDER_PATTERNS = {
    "%LANG%": r"%LANG%",
    "%FIELD%": r"%FIELD%",
    "%IMAGE%": r"%IMAGE%",
    "%TEXT%": r"%TEXT%",
    "%CONTEXT%": r"%CONTEXT%",
}

# Minimum content requirements
MIN_CONTENT_LENGTH = {
    "image_to_text": 50,
    "text_to_dwc": 100,
    "image_to_dwc": 150,
}

# Required message roles for each task
REQUIRED_ROLES = {
    "image_to_text": {"user"},
    "text_to_dwc": {"user", "system"},
    "image_to_dwc": {"user", "system"},
}


def extract_placeholders(content: str) -> Set[str]:
    """Extract all placeholders from prompt content."""
    placeholders = set()
    for placeholder_name, pattern in PLACEHOLDER_PATTERNS.items():
        if re.search(pattern, content):
            placeholders.add(placeholder_name)
    return placeholders


def validate_prompt_task(
    task: str,
    prompt_dir: Optional[Path] = None
) -> PromptTestResult:
    """Validate a single prompt task comprehensively."""
    try:
        messages = load_messages(task, prompt_dir)
    except Exception as e:
        return PromptTestResult(
            task=task,
            missing_placeholders=REQUIRED_PLACEHOLDERS.get(task, []),
            unexpected_placeholders=[],
            content_length=0,
            role_coverage=set(),
            passed=False
        )

    # Combine all message content
    content = "\n".join(m["content"] for m in messages)

    # Extract roles
    roles = {m["role"] for m in messages}

    # Find placeholders in content
    found_placeholders = extract_placeholders(content)
    required_placeholders = set(REQUIRED_PLACEHOLDERS.get(task, []))

    # Check for missing and unexpected placeholders
    missing = list(required_placeholders - found_placeholders)
    unexpected = list(found_placeholders - required_placeholders - {"%IMAGE%", "%TEXT%", "%CONTEXT%"})

    # Validate content length
    min_length = MIN_CONTENT_LENGTH.get(task, 0)
    content_valid = len(content) >= min_length

    # Validate role coverage
    required_roles = REQUIRED_ROLES.get(task, set())
    roles_valid = required_roles.issubset(roles)

    # Overall pass/fail
    passed = (
        len(missing) == 0 and
        content_valid and
        roles_valid
    )

    return PromptTestResult(
        task=task,
        missing_placeholders=missing,
        unexpected_placeholders=unexpected,
        content_length=len(content),
        role_coverage=roles,
        passed=passed
    )


def test_prompts_contain_required_placeholders() -> None:
    """Test that all prompts contain required placeholders."""
    for task, placeholders in REQUIRED_PLACEHOLDERS.items():
        messages = load_messages(task)
        content = "\n".join(m["content"] for m in messages)
        for placeholder in placeholders:
            assert placeholder in content, f"{placeholder} missing from {task} prompts"


def test_prompt_comprehensive_validation() -> None:
    """Comprehensive validation of all prompt tasks."""
    results = []

    for task in REQUIRED_PLACEHOLDERS.keys():
        result = validate_prompt_task(task)
        results.append(result)

        # Detailed assertions with helpful error messages
        assert result.passed, (
            f"Task '{task}' failed validation:\n"
            f"  Missing placeholders: {result.missing_placeholders}\n"
            f"  Content length: {result.content_length} (min: {MIN_CONTENT_LENGTH.get(task, 0)})\n"
            f"  Role coverage: {result.role_coverage} (required: {REQUIRED_ROLES.get(task, set())})\n"
        )


def test_prompt_role_coverage() -> None:
    """Test that prompts have appropriate role coverage."""
    for task, required_roles in REQUIRED_ROLES.items():
        messages = load_messages(task)
        found_roles = {m["role"] for m in messages}

        missing_roles = required_roles - found_roles
        assert len(missing_roles) == 0, (
            f"Task '{task}' missing required roles: {missing_roles}\n"
            f"Found roles: {found_roles}\n"
            f"Required roles: {required_roles}"
        )


def test_prompt_content_quality() -> None:
    """Test prompt content meets quality standards."""
    for task in REQUIRED_PLACEHOLDERS.keys():
        messages = load_messages(task)
        content = "\n".join(m["content"] for m in messages)

        # Check minimum content length
        min_length = MIN_CONTENT_LENGTH.get(task, 0)
        assert len(content) >= min_length, (
            f"Task '{task}' content too short: {len(content)} < {min_length}"
        )

        # Check for empty messages
        for i, message in enumerate(messages):
            assert message["content"].strip(), (
                f"Task '{task}' message {i} ({message['role']}) is empty"
            )


def test_custom_prompt_directory() -> None:
    """Test validation works with custom prompt directories."""
    # Test with test resources directory
    test_prompts = Path(__file__).parent.parent / "resources" / "gpt_prompts" / "custom"

    if test_prompts.exists():
        result = validate_prompt_task("text_to_dwc", test_prompts)
        # Custom prompts may have different requirements, so just check basic structure
        assert len(result.role_coverage) > 0, "Custom prompts should have at least one role"
        assert result.content_length > 0, "Custom prompts should have content"


@pytest.mark.parametrize("task", REQUIRED_PLACEHOLDERS.keys())
def test_individual_prompt_tasks(task: str) -> None:
    """Test each prompt task individually with detailed reporting."""
    result = validate_prompt_task(task)

    # Create detailed assertion message
    if not result.passed:
        error_details = []

        if result.missing_placeholders:
            error_details.append(f"Missing placeholders: {result.missing_placeholders}")

        if result.content_length < MIN_CONTENT_LENGTH.get(task, 0):
            error_details.append(f"Content too short: {result.content_length}")

        required_roles = REQUIRED_ROLES.get(task, set())
        if not required_roles.issubset(result.role_coverage):
            missing_roles = required_roles - result.role_coverage
            error_details.append(f"Missing roles: {missing_roles}")

        pytest.fail(f"Task '{task}' validation failed: {'; '.join(error_details)}")


# Coverage harness functions for external use
def run_prompt_coverage_analysis() -> Dict[str, PromptTestResult]:
    """Run comprehensive prompt coverage analysis."""
    results = {}
    for task in REQUIRED_PLACEHOLDERS.keys():
        results[task] = validate_prompt_task(task)
    return results


def generate_coverage_report(results: Dict[str, PromptTestResult]) -> str:
    """Generate a human-readable coverage report."""
    report_lines = ["GPT Prompt Coverage Report", "=" * 30, ""]

    total_tasks = len(results)
    passed_tasks = sum(1 for r in results.values() if r.passed)

    report_lines.append(f"Overall Status: {passed_tasks}/{total_tasks} tasks passed")
    report_lines.append("")

    for task, result in results.items():
        status = "✓ PASS" if result.passed else "✗ FAIL"
        report_lines.append(f"{task}: {status}")

        if not result.passed:
            if result.missing_placeholders:
                report_lines.append(f"  Missing placeholders: {result.missing_placeholders}")
            if result.unexpected_placeholders:
                report_lines.append(f"  Unexpected placeholders: {result.unexpected_placeholders}")
            if result.content_length < MIN_CONTENT_LENGTH.get(task, 0):
                report_lines.append(f"  Content too short: {result.content_length}")

        report_lines.append(f"  Roles: {sorted(result.role_coverage)}")
        report_lines.append(f"  Content length: {result.content_length}")
        report_lines.append("")

    return "\n".join(report_lines)
