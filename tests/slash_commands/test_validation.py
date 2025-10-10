"""Main integration test suite for slash command validation."""

import pytest
from pathlib import Path
from src.test_harness.command_executor import CommandExecutor
from src.test_harness.models import TestCommand, TestReport
from src.test_harness.report_generator import ReportGenerator


@pytest.fixture
def executor():
    """Create CommandExecutor instance for testing."""
    repo_root = Path(__file__).parent.parent.parent
    return CommandExecutor(repo_root)


@pytest.fixture
def report_generator(tmp_path):
    """Create ReportGenerator instance for testing."""
    return ReportGenerator(tmp_path)


@pytest.fixture(scope="session")
def test_report():
    """Create shared test report for session."""
    return TestReport(suite_name="Slash Command Validation Suite", environment="test")


@pytest.mark.specify
@pytest.mark.skip(
    reason="Slash commands require Claude Code agent execution - use manual validation (see MANUAL_VALIDATION.md)"
)
def test_specify_command(executor, test_report):
    """Test /specify command completes without errors.

    MANUAL TEST PROCEDURE:
    1. Run: /specify "Test validation feature"
    2. Verify: specs/[branch]/spec.md created
    3. Verify: No errors in output
    4. Verify: spec.md contains valid markdown
    """
    command = TestCommand(
        name="/specify",
        parameters=["Test validation feature"],
        expected_behavior="Creates spec.md file",
    )

    result = executor.execute_command(command)
    test_report.add_result(result)

    assert result.status.value == "PASS", f"Command failed: {result.stderr}"
    assert result.exit_code == 0


@pytest.mark.plan
@pytest.mark.skip(
    reason="Slash commands require Claude Code agent execution - use manual validation (see MANUAL_VALIDATION.md)"
)
def test_plan_command(executor, test_report):
    """Test /plan command completes without errors.

    MANUAL TEST PROCEDURE:
    1. Run: /plan
    2. Verify: specs/[branch]/plan.md created
    3. Verify: Design artifacts created (research.md, data-model.md, contracts/)
    4. Verify: No errors in output
    """
    command = TestCommand(
        name="/plan", parameters=[], expected_behavior="Creates plan.md and design docs"
    )

    result = executor.execute_command(command)
    test_report.add_result(result)

    assert result.status.value == "PASS", f"Command failed: {result.stderr}"
    assert result.exit_code == 0


@pytest.mark.tasks
@pytest.mark.skip(
    reason="Slash commands require Claude Code agent execution - use manual validation (see MANUAL_VALIDATION.md)"
)
def test_tasks_command(executor, test_report):
    """Test /tasks command completes without errors.

    MANUAL TEST PROCEDURE:
    1. Run: /tasks
    2. Verify: specs/[branch]/tasks.md created
    3. Verify: Tasks are properly formatted
    4. Verify: No errors in output
    """
    command = TestCommand(name="/tasks", parameters=[], expected_behavior="Creates tasks.md")

    result = executor.execute_command(command)
    test_report.add_result(result)

    assert result.status.value == "PASS", f"Command failed: {result.stderr}"
    assert result.exit_code == 0


@pytest.mark.implement
@pytest.mark.skip(
    reason="Slash commands require Claude Code agent execution - use manual validation (see MANUAL_VALIDATION.md)"
)
def test_implement_command(executor, test_report):
    """Test /implement command completes without errors.

    MANUAL TEST PROCEDURE:
    1. Run: /implement
    2. Verify: Tasks are executed in order
    3. Verify: Implementation completes
    4. Verify: No errors in output
    """
    command = TestCommand(
        name="/implement", parameters=[], expected_behavior="Tracks implementation progress"
    )

    result = executor.execute_command(command)
    test_report.add_result(result)

    assert result.status.value == "PASS", f"Command failed: {result.stderr}"
    assert result.exit_code == 0


def test_report_generation(report_generator, test_report):
    """Test that reports are generated correctly."""
    if test_report.total_commands == 0:
        pytest.skip("No test results to report")

    yaml_path, md_path = report_generator.generate_report(test_report)

    assert Path(yaml_path).exists(), "YAML report not created"
    assert Path(md_path).exists(), "Markdown report not created"

    # Verify YAML is valid
    import yaml

    with open(yaml_path) as f:
        data = yaml.safe_load(f)
        assert data["suite_name"] == test_report.suite_name
        assert data["total_commands"] == test_report.total_commands

    # Verify Markdown has content
    with open(md_path) as f:
        content = f.read()
        assert "Slash Command Validation Report" in content
        assert test_report.suite_name in content
