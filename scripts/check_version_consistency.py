#!/usr/bin/env python3
"""
Version Consistency Checker

Validates that all version references in the codebase match the canonical
version defined in pyproject.toml.

Usage:
    python scripts/check_version_consistency.py
    python scripts/check_version_consistency.py --fix

Exit codes:
    0 - All versions consistent
    1 - Inconsistencies found
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple

# Files to check with their version reference patterns
VERSION_CHECKS = [
    # README.md
    {
        "file": "README.md",
        "patterns": [
            (r'version-(\d+\.\d+\.\d+)-blue', "Version badge"),
            (r'## 📦 Current Release: v(\d+\.\d+\.\d+)', "Current Release section"),
            (r'\*\*Current:\*\* v(\d+\.\d+\.\d+)', "Version History section"),
        ]
    },
    # CHANGELOG.md - only check first version header after [Unreleased]
    {
        "file": "CHANGELOG.md",
        "patterns": [
            (r'## \[Unreleased\].*?## \[(\d+\.\d+\.\d+)\]', "Latest version header (first after Unreleased)"),
        ],
        "multiline": True
    },
]

def get_canonical_version() -> str:
    """Read canonical version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]

def check_file(file_path: Path, patterns: List[Tuple[str, str]], canonical_version: str, multiline: bool = False) -> List[str]:
    """Check a file for version inconsistencies.

    Returns list of error messages (empty if all consistent).
    """
    if not file_path.exists():
        return [f"⚠️  File not found: {file_path}"]

    content = file_path.read_text()
    errors = []

    flags = re.DOTALL if multiline else 0

    for pattern, description in patterns:
        matches = re.findall(pattern, content, flags=flags)
        for match in matches:
            if match != canonical_version:
                errors.append(
                    f"❌ {file_path}: {description}\n"
                    f"   Found: {match}\n"
                    f"   Expected: {canonical_version}"
                )

    return errors

def main():
    parser = argparse.ArgumentParser(description="Check version consistency across codebase")
    parser.add_argument("--fix", action="store_true", help="Automatically fix inconsistencies (not implemented)")
    args = parser.parse_args()

    # Get canonical version
    try:
        canonical_version = get_canonical_version()
    except Exception as e:
        print(f"❌ Failed to read version from pyproject.toml: {e}")
        return 1

    print("=" * 70)
    print("VERSION CONSISTENCY CHECK")
    print("=" * 70)
    print(f"Canonical version (pyproject.toml): {canonical_version}")
    print()

    # Check all files
    all_errors = []
    for check in VERSION_CHECKS:
        file_path = Path(check["file"])
        multiline = check.get("multiline", False)
        errors = check_file(file_path, check["patterns"], canonical_version, multiline)
        all_errors.extend(errors)

    # Report results
    if all_errors:
        print("INCONSISTENCIES FOUND:\n")
        for error in all_errors:
            print(error)
            print()
        print("=" * 70)
        print(f"❌ Found {len(all_errors)} version inconsistencies")
        print()
        print("To fix:")
        print("  1. Update all references to match pyproject.toml version")
        print("  2. Run this script again to verify")
        print()
        return 1
    else:
        print("✅ All version references are consistent!")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())
