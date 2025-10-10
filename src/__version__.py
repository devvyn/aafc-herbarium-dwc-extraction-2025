"""Single source of truth for package version.

This version is automatically read from pyproject.toml.
"""

import tomllib
from pathlib import Path


def get_version() -> str:
    """Read version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


__version__ = get_version()
