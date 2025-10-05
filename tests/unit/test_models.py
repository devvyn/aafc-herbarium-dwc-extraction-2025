"""Unit tests for data models."""

import pytest
from datetime import datetime
from src.test_harness.models import (
    TestCommand,
    ValidationResult,
    TestStatus,
    TestReport,
    OutputArtifact,
    OutputFormat
)
from pathlib import Path


class TestTestCommand:
    """Unit tests for TestCommand model."""

    def test_creation(self):
        """Test TestCommand creation."""
        cmd = TestCommand(
            name="/specify",
            parameters=["arg1", "arg2"],
            expected_behavior="Creates spec.md"
        )
        assert cmd.name == "/specify"
        assert cmd.parameters == ["arg1", "arg2"]
        assert cmd.isolation_required is True

    def test_str_representation(self):
        """Test string representation."""
        cmd = TestCommand(
            name="/plan",
            parameters=[],
            expected_behavior="Creates plan"
        )
        assert str(cmd) == "TestCommand(/plan)"


class TestValidationResult:
    """Unit tests for ValidationResult model."""

    def test_passed_property_when_pass(self):
        """Test passed property returns True for PASS status."""
        result = ValidationResult(
            command_name="/specify",
            status=TestStatus.PASS,
            exit_code=0,
            execution_time_seconds=1.5,
            stdout="output",
            stderr="",
            artifacts_created=["spec.md"]
        )
        assert result.passed is True

    def test_passed_property_when_fail(self):
        """Test passed property returns False for FAIL status."""
        result = ValidationResult(
            command_name="/specify",
            status=TestStatus.FAIL,
            exit_code=1,
            execution_time_seconds=1.5,
            stdout="",
            stderr="error",
            artifacts_created=[]
        )
        assert result.passed is False

    def test_default_timestamp(self):
        """Test timestamp defaults to current time."""
        result = ValidationResult(
            command_name="/plan",
            status=TestStatus.PASS,
            exit_code=0,
            execution_time_seconds=2.0,
            stdout="",
            stderr="",
            artifacts_created=[]
        )
        assert isinstance(result.timestamp, datetime)


class TestTestReport:
    """Unit tests for TestReport model."""

    def test_add_result_increments_counters(self):
        """Test adding results updates counters correctly."""
        report = TestReport(suite_name="Test Suite")

        result1 = ValidationResult(
            command_name="/specify",
            status=TestStatus.PASS,
            exit_code=0,
            execution_time_seconds=1.0,
            stdout="",
            stderr="",
            artifacts_created=[]
        )

        result2 = ValidationResult(
            command_name="/plan",
            status=TestStatus.FAIL,
            exit_code=1,
            execution_time_seconds=2.0,
            stdout="",
            stderr="error",
            artifacts_created=[]
        )

        report.add_result(result1)
        report.add_result(result2)

        assert report.total_commands == 2
        assert report.passed_count == 1
        assert report.failed_count == 1
        assert report.total_duration_seconds == 3.0

    def test_pass_rate_calculation(self):
        """Test pass rate percentage calculation."""
        report = TestReport(suite_name="Test Suite")

        # Add 3 passing, 1 failing
        for _ in range(3):
            report.add_result(ValidationResult(
                command_name="/test",
                status=TestStatus.PASS,
                exit_code=0,
                execution_time_seconds=1.0,
                stdout="",
                stderr="",
                artifacts_created=[]
            ))

        report.add_result(ValidationResult(
            command_name="/test",
            status=TestStatus.FAIL,
            exit_code=1,
            execution_time_seconds=1.0,
            stdout="",
            stderr="",
            artifacts_created=[]
        ))

        assert report.pass_rate == 75.0

    def test_pass_rate_empty_report(self):
        """Test pass rate is 0 for empty report."""
        report = TestReport(suite_name="Empty Suite")
        assert report.pass_rate == 0.0


class TestOutputArtifact:
    """Unit tests for OutputArtifact model."""

    def test_creation(self):
        """Test OutputArtifact creation."""
        artifact = OutputArtifact(
            format=OutputFormat.YAML,
            file_path=Path("test.yaml"),
            size_bytes=1024,
            checksum="abc123",
            human_readable=True,
            machine_toolable=True
        )
        assert artifact.format == OutputFormat.YAML
        assert artifact.file_path == Path("test.yaml")
        assert artifact.size_bytes == 1024
        assert artifact.human_readable is True
        assert artifact.machine_toolable is True
