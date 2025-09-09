from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

from import_review import import_bundle
from io_utils.candidates import init_db as init_candidate_db
from io_utils.database import fetch_import_audit, init_db as init_app_db
from io_utils.read import compute_sha256


def test_import_bundle_records_audit_in_app_db(tmp_path: Path) -> None:
    src_db = tmp_path / "src_candidates.db"
    src_session = init_candidate_db(src_db)
    src_session.close()

    manifest = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "schema_version": "1.0.0",
    }
    bundle_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.write(src_db, "candidates.db")

    dest_db = tmp_path / "candidates.db"
    app_db = tmp_path / "app.db"
    import_bundle(bundle_path, dest_db, "1.0.0", "alice", app_db)

    conn = init_app_db(app_db)
    bundle_hash = compute_sha256(bundle_path)
    audit = fetch_import_audit(conn, bundle_hash)
    assert audit and audit.user_id == "alice"
    conn.close()
