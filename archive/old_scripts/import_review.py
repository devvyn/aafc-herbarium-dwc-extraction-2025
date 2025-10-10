from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from io_utils.candidates import import_decisions, init_db as init_candidate_db
from io_utils.database import insert_import_audit, init_db as init_app_db
from io_utils.read import compute_sha256


def verify_manifest(manifest: dict, expected_version: str) -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if manifest.get("commit") != commit:
        raise RuntimeError("commit hash mismatch")
    if manifest.get("schema_version") != expected_version:
        raise RuntimeError("schema version mismatch")


def import_bundle(
    bundle: Path,
    candidates_db: Path,
    schema_version: str,
    user: str,
    app_db: Path | None = None,
) -> None:
    bundle_hash = compute_sha256(bundle)
    with zipfile.ZipFile(bundle) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        verify_manifest(manifest, schema_version)
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extract("candidates.db", tmpdir)
            src_session = init_candidate_db(Path(tmpdir) / "candidates.db")
            dest_session = init_candidate_db(candidates_db)
            import_decisions(dest_session, src_session)
            src_session.close()
            dest_session.close()
    app_db_path = app_db or candidates_db.with_name("app.db")
    audit_session = init_app_db(app_db_path)
    insert_import_audit(audit_session, user, bundle_hash)
    audit_session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed decisions")
    parser.add_argument("bundle", type=Path, help="Path to review bundle zip")
    parser.add_argument("db", type=Path, help="Local candidates database")
    parser.add_argument("--schema-version", required=True, help="Expected schema version")
    parser.add_argument("--user", required=True, help="User ID for auditing")
    parser.add_argument(
        "--app-db",
        type=Path,
        help="Application database (defaults to app.db next to candidates.db)",
    )
    args = parser.parse_args()
    import_bundle(args.bundle, args.db, args.schema_version, args.user, args.app_db)


if __name__ == "__main__":
    main()
