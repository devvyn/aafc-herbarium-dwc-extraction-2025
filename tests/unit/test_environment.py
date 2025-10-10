"""Unit tests for environment snapshot utilities."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch


from src.utils.environment import (
    capture_environment,
    compare_environments,
    get_git_info,
    get_python_packages,
    load_environment_snapshot,
    save_environment_snapshot,
)


class TestGetGitInfo:
    """Test git information extraction."""

    def test_get_git_info_success(self):
        """Test successful git info extraction."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = [
                "abc123def456\n",  # commit hash
                "M file.py\n",  # dirty status
                "main\n",  # branch
            ]

            result = get_git_info()

            assert result == {"commit": "abc123def456", "branch": "main", "dirty": True}

    def test_get_git_info_clean_repo(self):
        """Test git info with clean working directory."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = [
                "abc123def456\n",
                "",  # Empty status = clean
                "feature-branch\n",
            ]

            result = get_git_info()

            assert result == {"commit": "abc123def456", "branch": "feature-branch", "dirty": False}

    def test_get_git_info_not_a_repo(self):
        """Test git info when not in a git repository."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(128, "git")

            result = get_git_info()

            assert result == {"commit": None, "branch": None, "dirty": None}


class TestGetPythonPackages:
    """Test Python package listing."""

    def test_get_python_packages_with_uv(self):
        """Test package listing using uv (preferred)."""
        mock_output = json.dumps(
            [{"name": "requests", "version": "2.31.0"}, {"name": "pytest", "version": "8.0.0"}]
        )

        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = mock_output

            result = get_python_packages()

            assert result == {"requests": "2.31.0", "pytest": "8.0.0"}
            mock_check_output.assert_called_once_with(
                ["uv", "pip", "list", "--format", "json"], text=True
            )

    def test_get_python_packages_fallback_to_pip(self):
        """Test package listing fallback to pip when uv unavailable."""
        mock_output = json.dumps([{"name": "requests", "version": "2.31.0"}])

        with patch("subprocess.check_output") as mock_check_output:
            # First call (uv) fails, second call (pip) succeeds
            mock_check_output.side_effect = [FileNotFoundError(), mock_output]

            result = get_python_packages()

            assert result == {"requests": "2.31.0"}
            assert mock_check_output.call_count == 2

    def test_get_python_packages_both_fail(self):
        """Test package listing when both uv and pip fail."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = FileNotFoundError()

            result = get_python_packages()

            assert result == {}


class TestCaptureEnvironment:
    """Test environment snapshot capture."""

    @patch("src.utils.environment.get_python_packages")
    @patch("src.utils.environment.get_git_info")
    def test_capture_environment_basic(self, mock_git_info, mock_packages):
        """Test basic environment capture."""
        mock_git_info.return_value = {"commit": "abc123", "branch": "main", "dirty": False}
        mock_packages.return_value = {"requests": "2.31.0"}

        result = capture_environment(run_id="test-run", command="python script.py")

        assert result["run_id"] == "test-run"
        assert result["command"] == "python script.py"
        assert "timestamp" in result
        assert result["git"] == {"commit": "abc123", "branch": "main", "dirty": False}
        assert result["dependencies"] == {"requests": "2.31.0"}
        assert "python" in result
        assert "version" in result["python"]
        assert "platform" in result

    @patch("src.utils.environment.get_python_packages")
    @patch("src.utils.environment.get_git_info")
    def test_capture_environment_optional_params(self, mock_git_info, mock_packages):
        """Test environment capture without optional parameters."""
        mock_git_info.return_value = {"commit": "abc123", "branch": "main", "dirty": False}
        mock_packages.return_value = {}

        result = capture_environment()

        assert result["run_id"] is None
        assert result["command"] is None


class TestSaveAndLoadSnapshot:
    """Test environment snapshot file I/O."""

    @patch("src.utils.environment.capture_environment")
    def test_save_environment_snapshot(self, mock_capture, tmp_path: Path):
        """Test saving environment snapshot to file."""
        mock_snapshot = {
            "run_id": "test-run",
            "timestamp": "2025-10-10T12:00:00Z",
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
        }
        mock_capture.return_value = mock_snapshot

        output_file = save_environment_snapshot(tmp_path, run_id="test-run", command="test command")

        assert output_file == tmp_path / "environment.json"
        assert output_file.exists()

        # Verify file contents
        saved_data = json.loads(output_file.read_text())
        assert saved_data == mock_snapshot

        # Verify capture was called with correct params
        mock_capture.assert_called_once_with(run_id="test-run", command="test command")

    def test_load_environment_snapshot(self, tmp_path: Path):
        """Test loading environment snapshot from file."""
        snapshot_data = {
            "run_id": "test-run",
            "timestamp": "2025-10-10T12:00:00Z",
            "python": {"version": "3.11.0"},
        }

        snapshot_file = tmp_path / "environment.json"
        snapshot_file.write_text(json.dumps(snapshot_data))

        result = load_environment_snapshot(snapshot_file)

        assert result == snapshot_data


class TestCompareEnvironments:
    """Test environment comparison logic."""

    def test_compare_identical_environments(self):
        """Test comparison of identical environments."""
        env = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux-x86_64"},
            "dependencies": {"requests": "2.31.0"},
        }

        result = compare_environments(env, env)

        assert result == {}

    def test_compare_different_python_versions(self):
        """Test detection of Python version differences."""
        env1 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {},
        }
        env2 = {
            "python": {"version": "3.12.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {},
        }

        result = compare_environments(env1, env2)

        assert "python_version" in result
        assert result["python_version"] == {"env1": "3.11.0", "env2": "3.12.0"}

    def test_compare_different_git_commits(self):
        """Test detection of git commit differences."""
        env1 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {},
        }
        env2 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "def456"},
            "platform": {"platform": "Linux"},
            "dependencies": {},
        }

        result = compare_environments(env1, env2)

        assert "git_commit" in result
        assert result["git_commit"] == {"env1": "abc123", "env2": "def456"}

    def test_compare_different_platforms(self):
        """Test detection of platform differences."""
        env1 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux-x86_64"},
            "dependencies": {},
        }
        env2 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Darwin-arm64"},
            "dependencies": {},
        }

        result = compare_environments(env1, env2)

        assert "platform" in result
        assert result["platform"] == {"env1": "Linux-x86_64", "env2": "Darwin-arm64"}

    def test_compare_different_dependencies(self):
        """Test detection of dependency version differences."""
        env1 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {"requests": "2.31.0", "pytest": "8.0.0", "numpy": "1.24.0"},
        }
        env2 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {"requests": "2.32.0", "pytest": "8.0.0", "pandas": "2.0.0"},
        }

        result = compare_environments(env1, env2)

        assert "dependencies" in result
        # Only changed packages reported (pytest unchanged, pandas is new)
        assert result["dependencies"] == {"requests": {"env1": "2.31.0", "env2": "2.32.0"}}

    def test_compare_multiple_differences(self):
        """Test detection of multiple environment differences."""
        env1 = {
            "python": {"version": "3.11.0"},
            "git": {"commit": "abc123"},
            "platform": {"platform": "Linux"},
            "dependencies": {"requests": "2.31.0"},
        }
        env2 = {
            "python": {"version": "3.12.0"},
            "git": {"commit": "def456"},
            "platform": {"platform": "Darwin"},
            "dependencies": {"requests": "2.32.0"},
        }

        result = compare_environments(env1, env2)

        assert len(result) == 4  # All categories differ
        assert "python_version" in result
        assert "git_commit" in result
        assert "platform" in result
        assert "dependencies" in result


class TestIntegration:
    """Integration tests for full workflow."""

    @patch("subprocess.check_output")
    def test_full_snapshot_workflow(self, mock_subprocess, tmp_path: Path):
        """Test complete snapshot save/load/compare workflow."""
        # Mock git and package commands
        mock_subprocess.side_effect = [
            "abc123\n",  # git commit
            "",  # git status (clean)
            "main\n",  # git branch
            json.dumps([{"name": "requests", "version": "2.31.0"}]),  # uv pip list
        ]

        # Save snapshot
        snapshot_file = save_environment_snapshot(
            tmp_path, run_id="integration-test", command="pytest"
        )

        # Verify file exists
        assert snapshot_file.exists()

        # Load snapshot
        loaded = load_environment_snapshot(snapshot_file)

        # Verify contents
        assert loaded["run_id"] == "integration-test"
        assert loaded["command"] == "pytest"
        assert loaded["git"]["commit"] == "abc123"
        assert loaded["git"]["branch"] == "main"
        assert loaded["git"]["dirty"] is False
        assert loaded["dependencies"]["requests"] == "2.31.0"

        # Compare with itself (should be identical)
        differences = compare_environments(loaded, loaded)
        assert differences == {}
