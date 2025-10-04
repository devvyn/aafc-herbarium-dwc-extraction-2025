"""CommandExecutor for executing slash commands in test environment.

IMPORTANT LIMITATION:
Slash commands (/specify, /plan, /tasks, /implement) are Claude Code agent
commands executed via the SlashCommand tool. They cannot be executed programmatically
via subprocess because they are not shell executables.

Current implementation attempts subprocess execution but will fail for slash commands.
For manual validation procedures, see: tests/slash_commands/MANUAL_VALIDATION.md

Future enhancement: Implement Claude Code CLI wrapper for programmatic execution.
"""

import subprocess
import time
from pathlib import Path
from typing import List
from src.test_harness.models import TestCommand, ValidationResult, TestStatus


class CommandExecutor:
    """Executes test commands and captures validation results.

    NOTE: This executor uses subprocess.run() which works for shell commands
    but NOT for Claude Code slash commands (/specify, /plan, /tasks, /implement).

    For slash command validation, use manual testing procedures documented in:
    tests/slash_commands/MANUAL_VALIDATION.md
    """

    def __init__(self, repo_root: Path):
        """Initialize executor with repository root path.

        Args:
            repo_root: Path to the repository root directory
        """
        self.repo_root = repo_root

    def execute_command(self, command: TestCommand) -> ValidationResult:
        """Execute a test command and return validation results.

        Args:
            command: TestCommand to execute

        Returns:
            ValidationResult with execution details
        """
        start_time = time.time()

        try:
            # Execute command via subprocess with timeout
            result = subprocess.run(
                [command.name] + command.parameters,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            execution_time = time.time() - start_time

            # Determine status based on exit code
            status = TestStatus.PASS if result.returncode == 0 else TestStatus.FAIL

            # Check for artifacts (simplified - looks for common output patterns)
            artifacts = self._find_artifacts(command)

            return ValidationResult(
                command_name=command.name,
                status=status,
                exit_code=result.returncode,
                execution_time_seconds=execution_time,
                stdout=result.stdout,
                stderr=result.stderr,
                artifacts_created=artifacts,
                environment="test"
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ValidationResult(
                command_name=command.name,
                status=TestStatus.FAIL,
                exit_code=-1,
                execution_time_seconds=execution_time,
                stdout="",
                stderr="Command timed out after 60 seconds",
                artifacts_created=[],
                environment="test"
            )

        except FileNotFoundError:
            execution_time = time.time() - start_time
            return ValidationResult(
                command_name=command.name,
                status=TestStatus.FAIL,
                exit_code=-1,
                execution_time_seconds=execution_time,
                stdout="",
                stderr=f"Command not found: {command.name}",
                artifacts_created=[],
                environment="test"
            )

    def _find_artifacts(self, command: TestCommand) -> List[str]:
        """Find artifacts created by command execution.

        Args:
            command: The executed command

        Returns:
            List of artifact file paths (relative to repo root)
        """
        artifacts = []

        # Map commands to their expected artifacts
        artifact_patterns = {
            "/specify": ["spec.md"],
            "/plan": ["plan.md", "research.md", "data-model.md", "contracts/"],
            "/tasks": ["tasks.md"],
            "/implement": []  # Implementation creates various files
        }

        expected = artifact_patterns.get(command.name, [])

        # Check if expected artifacts exist (simplified check)
        for pattern in expected:
            # This is a simplified check - real implementation would
            # look in the appropriate spec directory
            artifacts.append(pattern)

        return artifacts
