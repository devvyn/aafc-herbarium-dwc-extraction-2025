"""Scientific provenance utilities for AAFC research workflows.

This module provides standardized tools for capturing version metadata
in scientific data outputs, enabling reproducibility and forensic analysis.

Usage:
    from provenance import capture_git_provenance, create_manifest

    # Capture at processing start
    git_info = capture_git_provenance()

    # Create export manifest
    manifest = create_manifest(
        version="1.0.0",
        git_info=git_info,
        custom_metadata={"specimen_count": 2885}
    )
"""

import json
import logging
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def capture_git_provenance() -> dict:
    """Capture current git repository state.

    Returns dict with git_commit, git_branch, git_dirty flags.
    Fails gracefully if git is unavailable.

    Returns:
        {
            "git_commit": "a1b2c3d...",
            "git_commit_short": "a1b2c3d",
            "git_branch": "main",
            "git_dirty": false
        }

        Returns {"git_commit": "unknown"} if git unavailable.

    Example:
        >>> git_info = capture_git_provenance()
        >>> if git_info.get("git_dirty"):
        ...     print("Warning: uncommitted changes present!")
    """
    git_info = {}

    try:
        # Capture commit hash (primary identifier)
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        git_info["git_commit"] = commit
        git_info["git_commit_short"] = commit[:7]

        # Capture branch (context)
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            if branch != "HEAD":  # Not in detached HEAD state
                git_info["git_branch"] = branch
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Flag uncommitted changes (critical for reproducibility!)
        try:
            result = subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            git_info["git_dirty"] = bool(result)

            if git_info["git_dirty"]:
                logger.warning(
                    "Processing with uncommitted changes! Consider committing for reproducibility."
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Git information not available")
        git_info["git_commit"] = "unknown"

    return git_info


def capture_system_info() -> dict:
    """Capture system environment information.

    Returns:
        {
            "platform": "macOS-14.0-arm64",
            "python_version": "3.11.5",
            "hostname": "aafc-workstation-01"
        }

    Example:
        >>> system_info = capture_system_info()
        >>> print(f"Running on {system_info['platform']}")
    """
    return {
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "hostname": platform.node(),
    }


def create_manifest(
    version: str,
    git_info: Optional[dict] = None,
    system_info: Optional[dict] = None,
    custom_metadata: Optional[dict] = None,
) -> dict:
    """Create standardized manifest with provenance metadata.

    Args:
        version: Semantic version string (e.g., "1.0.0")
        git_info: Git provenance from capture_git_provenance() (auto-captured if None)
        system_info: System info from capture_system_info() (auto-captured if None)
        custom_metadata: Additional domain-specific metadata

    Returns:
        Standardized manifest dict

    Example:
        >>> manifest = create_manifest(
        ...     version="1.0.0",
        ...     custom_metadata={"specimen_count": 2885, "export_type": "DwC"}
        ... )
        >>> manifest["provenance"]["git_commit"]
        'a1b2c3d4...'
    """
    # Auto-capture if not provided
    if git_info is None:
        git_info = capture_git_provenance()
    if system_info is None:
        system_info = capture_system_info()

    manifest = {
        "provenance": {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **git_info,
        },
        "system": system_info,
    }

    if custom_metadata:
        manifest.update(custom_metadata)

    return manifest


def save_manifest(manifest: dict, output_path: Path) -> None:
    """Save manifest to JSON file.

    Args:
        manifest: Manifest dict from create_manifest()
        output_path: Path to write manifest.json

    Example:
        >>> manifest = create_manifest("1.0.0")
        >>> save_manifest(manifest, Path("results/manifest.json"))
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {output_path}")


def validate_reproducibility(manifest_path: Path) -> tuple[bool, list[str]]:
    """Validate that current environment matches manifest provenance.

    Checks if current git state matches manifest for reproducibility.

    Args:
        manifest_path: Path to manifest.json

    Returns:
        (is_valid, warnings) tuple

    Example:
        >>> valid, warnings = validate_reproducibility(Path("results/manifest.json"))
        >>> if not valid:
        ...     for warning in warnings:
        ...         print(f"Warning: {warning}")
    """
    warnings = []

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except Exception as e:
        return False, [f"Could not load manifest: {e}"]

    # Check git commit
    current_git = capture_git_provenance()
    manifest_commit = manifest.get("provenance", {}).get("git_commit")

    if manifest_commit and manifest_commit != "unknown":
        if current_git.get("git_commit") != manifest_commit:
            warnings.append(
                f"Git commit mismatch: "
                f"current={current_git.get('git_commit', 'unknown')[:7]}, "
                f"manifest={manifest_commit[:7]}"
            )

    # Check dirty flag
    if current_git.get("git_dirty"):
        warnings.append("Uncommitted changes present in current working tree")

    manifest_dirty = manifest.get("provenance", {}).get("git_dirty")
    if manifest_dirty:
        warnings.append("Original export had uncommitted changes (git_dirty=true)")

    # Check Python version
    current_python = sys.version.split()[0]
    manifest_python = manifest.get("system", {}).get("python_version")
    if manifest_python and manifest_python != current_python:
        warnings.append(
            f"Python version mismatch: current={current_python}, manifest={manifest_python}"
        )

    is_valid = len(warnings) == 0
    return is_valid, warnings


# Convenience decorator for processing functions
def track_provenance(version: str):
    """Decorator to automatically track provenance for processing functions.

    Args:
        version: Semantic version string

    Example:
        @track_provenance(version="1.0.0")
        def process_specimens(input_dir: Path, output_dir: Path):
            # Git info captured automatically at function entry
            # Accessible via function.git_info attribute
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Capture provenance at entry
            git_info = capture_git_provenance()
            system_info = capture_system_info()

            # Attach to function for access
            func.git_info = git_info
            func.system_info = system_info

            # Execute function
            result = func(*args, **kwargs)

            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


if __name__ == "__main__":
    # Demo usage
    import sys

    print("=== Git Provenance ===")
    git_info = capture_git_provenance()
    print(json.dumps(git_info, indent=2))

    print("\n=== System Info ===")
    system_info = capture_system_info()
    print(json.dumps(system_info, indent=2))

    print("\n=== Full Manifest ===")
    manifest = create_manifest(
        version="1.0.0",
        custom_metadata={"specimen_count": 2885, "export_type": "Darwin Core Archive"},
    )
    print(json.dumps(manifest, indent=2))

    # Check dirty flag
    if git_info.get("git_dirty"):
        print("\n⚠️  Warning: Uncommitted changes detected!")
        print("Consider committing for reproducibility.")
        sys.exit(1)
    else:
        print("\n✅ Clean working tree - reproducible state")
