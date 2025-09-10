import subprocess
import json
import zipfile
import hashlib
from datetime import datetime, timezone
import pytest

from dwc import archive


@pytest.mark.parametrize(
    "exception",
    [subprocess.CalledProcessError(1, "git"), FileNotFoundError()],
)
def test_build_manifest_handles_missing_git(monkeypatch, exception):
    def _raise(*args, **kwargs):
        raise exception

    monkeypatch.setattr(subprocess, "check_output", _raise)
    manifest = archive.build_manifest()
    assert manifest["commit"] == "unknown"


def test_create_versioned_bundle_generates_tags(tmp_path, monkeypatch):
    fake_commit = "abcdef1234567890"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: fake_commit)

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    monkeypatch.setattr(archive, "datetime", DummyDatetime)

    filters = {"basisOfRecord": "specimen"}
    bundle = archive.create_versioned_bundle(tmp_path, version="1.0.0", filters=filters)
    assert bundle.exists()

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["commit"] == fake_commit
    assert manifest["filters"] == filters
    assert manifest["timestamp"] == "2024-01-02T03:04:05+00:00"

    filter_hash = hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
    expected_tag = f"v1.0.0_20240102T030405Z_{fake_commit[:7]}_{filter_hash}"
    assert manifest["version"] == expected_tag
    assert bundle.name == f"dwca_{expected_tag}.zip"

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
        assert {"meta.xml", "manifest.json"} <= names
