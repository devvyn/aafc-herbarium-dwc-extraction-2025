from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.skip(
    reason="import_review module not yet implemented - placeholder test for future feature"
)
def test_import_bundle_records_audit_in_app_db(tmp_path: Path) -> None:
    """
    Placeholder test for future import_bundle functionality.

    TODO: Implement import_bundle() function in import_review module
    Expected behavior:
    - Load bundle.zip containing candidates.db + manifest.json
    - Verify schema version compatibility
    - Import candidates into destination database
    - Record audit trail in app.db with bundle hash and user
    """
    pass  # Test skipped until import_review module is implemented
