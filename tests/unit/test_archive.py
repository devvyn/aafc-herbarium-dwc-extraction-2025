import subprocess
import json
import zipfile
import hashlib
from datetime import datetime, timezone
from unittest.mock import patch
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
    assert manifest["git_commit"] == fake_commit
    assert manifest["filters"] == filters
    assert manifest["timestamp"] == "2024-01-02T03:04:05+00:00"

    filter_hash = hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
    expected_tag = f"v1.0.0_20240102T030405Z_{fake_commit[:7]}_{filter_hash}"
    assert manifest["archive_tag"] == expected_tag
    assert bundle.name == f"dwca_{expected_tag}.zip"

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
        assert {"meta.xml", "manifest.json"} <= names


def test_enhanced_manifest_structure(tmp_path, monkeypatch):
    """Test that enhanced manifest includes all expected fields."""
    fake_commit = "abcdef1234567890"
    fake_branch = "feature-branch"

    def mock_git_command(cmd, text=True):
        if cmd == ["git", "rev-parse", "HEAD"]:
            return fake_commit
        elif cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return fake_branch
        elif cmd == ["git", "status", "--porcelain"]:
            return ""
        return ""

    monkeypatch.setattr(subprocess, "check_output", mock_git_command)

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    monkeypatch.setattr(archive, "datetime", DummyDatetime)

    manifest = archive.build_manifest(
        filters={"basisOfRecord": "specimen"},
        version="1.2.3",
        include_git_info=True,
        include_system_info=True,
    )

    # Test enhanced manifest structure
    assert manifest["format_version"] == "1.1.0"
    assert manifest["export_type"] == "darwin_core_archive"
    assert manifest["timestamp"] == "2024-01-02T03:04:05+00:00"
    assert manifest["version"] == "1.2.3"
    assert manifest["filters"] == {"basisOfRecord": "specimen"}
    assert manifest["git_commit"] == fake_commit
    assert manifest["git_commit_short"] == fake_commit[:7]
    assert manifest["git_branch"] == fake_branch
    assert manifest["git_dirty"] is False
    assert "system_info" in manifest
    assert "platform" in manifest["system_info"]
    assert "python_version" in manifest["system_info"]


def test_manifest_without_git_info(tmp_path, monkeypatch):
    """Test manifest generation when git is not available."""

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "check_output", raise_file_not_found)

    manifest = archive.build_manifest(include_git_info=True, include_system_info=False)

    assert manifest["git_commit"] == "unknown"
    assert "git_branch" not in manifest
    assert "system_info" not in manifest


def test_create_versioned_bundle_with_checksums(tmp_path, monkeypatch):
    """Test versioned bundle creation with file checksums."""
    # Create test CSV files
    (tmp_path / "occurrence.csv").write_text("occurrenceID,scientificName\n1,Test species")
    (tmp_path / "identification_history.csv").write_text(
        "occurrenceID,identifiedBy\n1,Test Identifier"
    )

    fake_commit = "abc1234567890"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: fake_commit)

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    monkeypatch.setattr(archive, "datetime", DummyDatetime)

    bundle = archive.create_versioned_bundle(
        tmp_path, version="2.1.0", bundle_format="rich", include_checksums=True
    )

    assert bundle.exists()
    assert "v2.1.0" in bundle.name
    assert "20240102T030405Z" in bundle.name
    assert "abc1234" in bundle.name

    # Verify manifest includes checksums
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert "file_checksums" in manifest
    assert "occurrence.csv" in manifest["file_checksums"]
    assert "sha256" in manifest["file_checksums"]["occurrence.csv"]
    assert "size_bytes" in manifest["file_checksums"]["occurrence.csv"]

    # Verify actual checksum calculation
    with zipfile.ZipFile(bundle) as zf:
        occurrence_content = zf.read("occurrence.csv")
        expected_hash = hashlib.sha256(occurrence_content).hexdigest()
        assert manifest["file_checksums"]["occurrence.csv"]["sha256"] == expected_hash


def test_create_versioned_bundle_simple_format(tmp_path, monkeypatch):
    """Test versioned bundle creation with simple filename format."""
    # Create test CSV files
    (tmp_path / "occurrence.csv").write_text("occurrenceID\n1")
    (tmp_path / "identification_history.csv").write_text("occurrenceID\n1")

    fake_commit = "def4567890123"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: fake_commit)

    bundle = archive.create_versioned_bundle(
        tmp_path, version="3.0.0", bundle_format="simple", include_checksums=False
    )

    assert bundle.exists()
    assert bundle.name == "dwca_v3.0.0.zip"

    # Verify manifest format
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["bundle_format"] == "simple"
    assert manifest["version"] == "3.0.0"
    assert "file_checksums" not in manifest


def test_create_versioned_bundle_with_additional_files(tmp_path, monkeypatch):
    """Test versioned bundle creation with additional files."""
    # Create test files
    (tmp_path / "occurrence.csv").write_text("occurrenceID\n1")
    (tmp_path / "identification_history.csv").write_text("occurrenceID\n1")
    (tmp_path / "README.txt").write_text("This is a readme file")
    (tmp_path / "processing_log.txt").write_text("Processing completed successfully")

    fake_commit = "ghi7890123456"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: fake_commit)

    bundle = archive.create_versioned_bundle(
        tmp_path,
        version="1.5.0",
        additional_files=["README.txt", "processing_log.txt", "nonexistent.txt"],
    )

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
        assert "README.txt" in names
        assert "processing_log.txt" in names
        assert "nonexistent.txt" not in names  # Should be skipped
        assert len(names) == 6  # 4 standard + 2 additional files


def test_create_archive_integration_with_versioned_bundle(tmp_path, monkeypatch):
    """Test that create_archive properly delegates to create_versioned_bundle."""
    # Create test CSV files
    (tmp_path / "occurrence.csv").write_text("occurrenceID\n1")
    (tmp_path / "identification_history.csv").write_text("occurrenceID\n1")

    fake_commit = "jkl0123456789"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: fake_commit)

    archive_path = archive.create_archive(
        tmp_path,
        compress=True,
        version="2.3.1",
        bundle_format="rich",
        include_checksums=True,
        additional_files=[],
    )

    assert archive_path.exists()
    assert "v2.3.1" in archive_path.name
    assert "jkl0123" in archive_path.name

    # Verify the ZIP contains expected files
    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
        expected_files = {
            "occurrence.csv",
            "identification_history.csv",
            "meta.xml",
            "manifest.json",
        }
        assert expected_files <= names

        # Verify enhanced manifest
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["format_version"] == "1.1.0"
        assert manifest["version"] == "2.3.1"
        assert manifest["bundle_format"] == "rich"
        assert "file_checksums" in manifest


def test_invalid_version_handling():
    """Test that invalid version strings are properly rejected."""
    with pytest.raises(ValueError, match="version must follow semantic versioning"):
        archive.create_versioned_bundle(Path("/tmp"), version="invalid-version")

    with pytest.raises(ValueError, match="version must follow semantic versioning"):
        archive.create_versioned_bundle(Path("/tmp"), version="1.0")

    with pytest.raises(ValueError, match="version must follow semantic versioning"):
        archive.create_versioned_bundle(Path("/tmp"), version="v1.0.0")


def test_manifest_git_dirty_detection(tmp_path, monkeypatch):
    """Test detection of uncommitted git changes."""
    fake_commit = "mno3456789012"

    def mock_git_command(cmd, text=True):
        if cmd == ["git", "rev-parse", "HEAD"]:
            return fake_commit
        elif cmd == ["git", "status", "--porcelain"]:
            return "M  modified_file.py\n?? untracked_file.txt"
        elif cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "dirty-branch"
        return ""

    monkeypatch.setattr(subprocess, "check_output", mock_git_command)

    manifest = archive.build_manifest(include_git_info=True)

    assert manifest["git_dirty"] is True
    assert manifest["git_branch"] == "dirty-branch"


def test_bundle_without_git_in_filename(tmp_path, monkeypatch):
    """Test bundle creation when git info is unavailable."""
    # Create test CSV files
    (tmp_path / "occurrence.csv").write_text("occurrenceID\n1")
    (tmp_path / "identification_history.csv").write_text("occurrenceID\n1")

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "check_output", raise_file_not_found)

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2024, 5, 15, 10, 30, 45, tzinfo=timezone.utc)

    monkeypatch.setattr(archive, "datetime", DummyDatetime)

    bundle = archive.create_versioned_bundle(tmp_path, version="1.8.2", bundle_format="rich")

    # Should still create bundle, but without git hash in filename
    assert bundle.exists()
    assert "v1.8.2" in bundle.name
    assert "20240515T103045Z" in bundle.name
    # Should not contain git hash since it's unavailable
    assert bundle.name.count("_") >= 2  # version_timestamp_...


@patch("dwc.archive.importlib.metadata.version")
def test_manifest_package_version_detection(mock_version, tmp_path):
    """Test detection of package version in manifest."""
    mock_version.return_value = "0.1.4"

    manifest = archive.build_manifest(include_system_info=True)

    assert "package_version" in manifest
    assert manifest["package_version"] == "0.1.4"
