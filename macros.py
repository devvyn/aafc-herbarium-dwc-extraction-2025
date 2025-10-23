"""
MkDocs macros for dynamic content generation.

This module provides dynamic variables pulled from project metadata,
enabling single source of truth for version numbers and other metadata.
"""

import toml
from pathlib import Path


def define_env(env):
    """
    Define dynamic variables and macros available in all markdown files.

    Usage in markdown:
        Current version: {{ version }}
        Project name: {{ project_name }}
    """
    # Load project metadata from pyproject.toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path) as f:
        pyproject = toml.load(f)

    # Extract project metadata
    project = pyproject.get("project", {})

    # Make variables available to all markdown files
    version = project.get("version", "unknown")
    env.variables["version"] = version
    env.variables["project_name"] = project.get("name", "herbarium-dwc")
    env.variables["description"] = project.get("description", "")

    # Clean up python version for badge display (remove >= prefix)
    python_req = project.get("requires-python", ">=3.11")
    env.variables["python_version"] = python_req.replace(">=", "")

    # Computed values
    env.variables["release_tag"] = f"v{version}"
    env.variables["github_release_url"] = (
        f"https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v{version}"
    )
