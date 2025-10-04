"""Data models for slash command validation testing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List


# T004: TestCommand Model
@dataclass
class TestCommand:
    """Represents a slash command to be tested."""

    name: str
    parameters: List[str]
    expected_behavior: str
    isolation_required: bool = True

    def __str__(self) -> str:
        return f"TestCommand({self.name})"


# T005: ValidationResult Model
class TestStatus(Enum):
    """Test execution status."""

    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    """Results from executing a test command."""

    command_name: str
    status: TestStatus
    exit_code: int
    execution_time_seconds: float
    stdout: str
    stderr: str
    artifacts_created: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    environment: str = ""

    @property
    def passed(self) -> bool:
        """Check if validation passed."""
        return self.status == TestStatus.PASS


# T006: TestReport Model
@dataclass
class TestReport:
    """Aggregated test results for a suite."""

    suite_name: str
    execution_date: datetime = field(default_factory=datetime.utcnow)
    total_commands: int = 0
    passed_count: int = 0
    failed_count: int = 0
    total_duration_seconds: float = 0.0
    environment: str = ""
    results: List[ValidationResult] = field(default_factory=list)

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report."""
        self.results.append(result)
        self.total_commands += 1
        if result.passed:
            self.passed_count += 1
        else:
            self.failed_count += 1
        self.total_duration_seconds += result.execution_time_seconds

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        return (self.passed_count / self.total_commands * 100) if self.total_commands > 0 else 0.0


# T007: OutputArtifact Model
class OutputFormat(Enum):
    """Output file format types."""

    MARKDOWN = "MARKDOWN"
    YAML = "YAML"
    DATABASE = "DATABASE"


@dataclass
class OutputArtifact:
    """Metadata for test report output files."""

    format: OutputFormat
    file_path: Path
    size_bytes: int
    checksum: str
    human_readable: bool
    machine_toolable: bool
