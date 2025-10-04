"""pytest fixtures for slash command validation tests."""

import pytest
from pathlib import Path


@pytest.fixture
def repo_root():
    """Return the repository root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def test_results_dir(repo_root):
    """Return the test results directory."""
    return repo_root / "test-results"
