"""Environment snapshot utilities for reproducibility tracking.

Extract Docker wisdom (declarative environments) without the baggage (daemon, containers).
"""

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def get_git_info() -> dict[str, Any]:
    """Get git repository information for provenance."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()

        # Check if working directory is dirty
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = bool(status)

        # Get branch name
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        return {"commit": commit, "branch": branch, "dirty": dirty}
    except subprocess.CalledProcessError:
        return {"commit": None, "branch": None, "dirty": None}


def get_python_packages() -> dict[str, str]:
    """Get installed Python packages with versions."""
    try:
        # Try uv pip list first (project uses uv)
        output = subprocess.check_output(["uv", "pip", "list", "--format", "json"], text=True)
        packages = json.loads(output)
        return {pkg["name"]: pkg["version"] for pkg in packages}
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        # Fallback to pip if uv not available
        try:
            output = subprocess.check_output(["pip", "list", "--format", "json"], text=True)
            packages = json.loads(output)
            return {pkg["name"]: pkg["version"] for pkg in packages}
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return {}


def capture_environment(run_id: str | None = None, command: str | None = None) -> dict[str, Any]:
    """
    Capture complete environment snapshot for reproducibility.

    Args:
        run_id: Optional run identifier
        command: Optional command that was executed

    Returns:
        Dictionary with environment information
    """
    git_info = get_git_info()
    packages = get_python_packages()

    snapshot = {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "python": {
            "version": sys.version,
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro,
            },
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "git": git_info,
        "dependencies": packages,
        "command": command,
    }

    return snapshot


def save_environment_snapshot(
    output_dir: Path, run_id: str | None = None, command: str | None = None
) -> Path:
    """
    Capture and save environment snapshot to file.

    Args:
        output_dir: Directory to save snapshot
        run_id: Optional run identifier
        command: Optional command that was executed

    Returns:
        Path to saved snapshot file
    """
    snapshot = capture_environment(run_id=run_id, command=command)

    output_file = output_dir / "environment.json"
    output_file.write_text(json.dumps(snapshot, indent=2))

    return output_file


def load_environment_snapshot(snapshot_file: Path) -> dict[str, Any]:
    """Load environment snapshot from file."""
    return json.loads(snapshot_file.read_text())


def compare_environments(env1: dict[str, Any], env2: dict[str, Any]) -> dict[str, Any]:
    """
    Compare two environment snapshots.

    Returns:
        Dictionary with differences
    """
    differences = {}

    # Compare Python versions
    if env1["python"]["version"] != env2["python"]["version"]:
        differences["python_version"] = {
            "env1": env1["python"]["version"],
            "env2": env2["python"]["version"],
        }

    # Compare git commits
    if env1["git"]["commit"] != env2["git"]["commit"]:
        differences["git_commit"] = {
            "env1": env1["git"]["commit"],
            "env2": env2["git"]["commit"],
        }

    # Compare platform
    if env1["platform"]["platform"] != env2["platform"]["platform"]:
        differences["platform"] = {
            "env1": env1["platform"]["platform"],
            "env2": env2["platform"]["platform"],
        }

    # Compare key dependencies
    deps1 = env1.get("dependencies", {})
    deps2 = env2.get("dependencies", {})

    changed_deps = {}
    for pkg, version in deps1.items():
        if pkg in deps2 and deps2[pkg] != version:
            changed_deps[pkg] = {"env1": version, "env2": deps2[pkg]}

    if changed_deps:
        differences["dependencies"] = changed_deps

    return differences
