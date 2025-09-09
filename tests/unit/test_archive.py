import subprocess
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
