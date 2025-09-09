from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from io_utils.candidates import import_decisions, init_db


def verify_manifest(manifest: dict, expected_version: str) -> None:
    commit = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    )
    if manifest.get("commit") != commit:
        raise RuntimeError("commit hash mismatch")
    if manifest.get("schema_version") != expected_version:
        raise RuntimeError("schema version mismatch")


def import_bundle(bundle: Path, db_path: Path, schema_version: str) -> None:
    with zipfile.ZipFile(bundle) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        verify_manifest(manifest, schema_version)
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extract("candidates.db", tmpdir)
            src_session = init_db(Path(tmpdir) / "candidates.db")
            dest_session = init_db(db_path)
            import_decisions(dest_session, src_session)
            src_session.close()
            dest_session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed decisions")
    parser.add_argument("bundle", type=Path, help="Path to review bundle zip")
    parser.add_argument("db", type=Path, help="Local candidates database")
    parser.add_argument(
        "--schema-version", required=True, help="Expected schema version"
    )
    args = parser.parse_args()
    import_bundle(args.bundle, args.db, args.schema_version)


if __name__ == "__main__":
    main()
