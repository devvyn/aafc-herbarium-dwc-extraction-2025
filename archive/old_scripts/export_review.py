from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def build_manifest(schema_version: str) -> dict[str, str]:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": timestamp,
        "commit": commit,
        "schema_version": schema_version,
    }


def package_review(db_path: Path, images_dir: Path, schema_version: str) -> Path:
    """Create a review bundle containing images, database, and manifest."""
    if not SEMVER_RE.match(schema_version):
        raise ValueError("schema version must follow semantic versioning")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    bundle_name = f"review_v{schema_version}.zip"
    bundle_path = output_dir / bundle_name
    manifest = build_manifest(schema_version)
    with zipfile.ZipFile(bundle_path, "w") as zf:
        zf.write(db_path, "candidates.db")
        for img in images_dir.rglob("*"):
            if img.is_file():
                zf.write(img, Path("images") / img.relative_to(images_dir))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    return bundle_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Package review bundle")
    parser.add_argument("db", type=Path, help="Path to candidates database")
    parser.add_argument("images", type=Path, help="Directory of source images")
    parser.add_argument("--schema-version", required=True, help="Schema version (e.g. 1.2.0)")
    args = parser.parse_args()
    package_review(args.db, args.images, args.schema_version)


if __name__ == "__main__":
    main()
