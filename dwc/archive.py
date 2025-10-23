"""Utilities for creating Darwin Core Archives.

This module builds a ``meta.xml`` descriptor based on the project's
``DWC_TERMS`` and the identification history schema used elsewhere in the
codebase.  The ``meta.xml`` file is written alongside ``occurrence.csv`` and
``identification_history.csv`` and can optionally be bundled into a ZIP file to
form a complete Darwin Core Archive (DwC-A).
"""

from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from zipfile import ZipFile, ZIP_DEFLATED
from typing import Any, Dict, List
from datetime import datetime, timezone
import subprocess
import re
import json
import hashlib
import logging

from .schema import DWC_TERMS


def _dwc_term(term: str) -> str:
    """Return the full Darwin Core URI for a term."""

    return f"http://rs.tdwg.org/dwc/terms/{term}"


IDENT_HISTORY_URIS: Dict[str, str] = {
    "occurrenceID": _dwc_term("occurrenceID"),
    "identificationID": "http://purl.org/dc/terms/identifier",
    "identifiedBy": _dwc_term("identifiedBy"),
    "dateIdentified": _dwc_term("dateIdentified"),
    "scientificName": _dwc_term("scientificName"),
    "scientificNameAuthorship": _dwc_term("scientificNameAuthorship"),
    "taxonRank": _dwc_term("taxonRank"),
    "identificationQualifier": _dwc_term("identificationQualifier"),
    "identificationRemarks": _dwc_term("identificationRemarks"),
    "identificationReferences": _dwc_term("identificationReferences"),
    "identificationVerificationStatus": _dwc_term("identificationVerificationStatus"),
    "isCurrent": "http://rs.gbif.org/terms/1.0/isCurrent",
}


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def build_manifest(
    filters: Dict[str, Any] | None = None,
    version: str | None = None,
    include_git_info: bool = True,
    include_system_info: bool = True,
) -> Dict[str, Any]:
    """Return enhanced run metadata for archive exports.

    Parameters
    ----------
    filters:
        Export filter criteria applied to the data.
    version:
        Semantic version string for the export.
    include_git_info:
        Whether to include git repository information.
    include_system_info:
        Whether to include system and environment information.

    Returns
    -------
    Dict containing comprehensive export metadata.
    """
    logger = logging.getLogger(__name__)

    manifest = {
        "format_version": "1.1.0",  # Schema version for this manifest format
        "export_type": "darwin_core_archive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filters": filters or {},
    }

    if version:
        if not SEMVER_RE.match(version):
            logger.warning(f"Version '{version}' does not follow semantic versioning")
        manifest["version"] = version

    if include_git_info:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            manifest["git_commit"] = commit
            manifest["git_commit_short"] = commit[:7]

            # Try to get branch information
            try:
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
                ).strip()
                if branch != "HEAD":  # Not in detached HEAD state
                    manifest["git_branch"] = branch
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            # Check for uncommitted changes
            try:
                result = subprocess.check_output(
                    ["git", "status", "--porcelain"], text=True
                ).strip()
                manifest["git_dirty"] = bool(result)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Git information not available")
            manifest["git_commit"] = "unknown"

    if include_system_info:
        import platform
        import sys

        manifest["system_info"] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
        }

        # Add package version if available
        try:
            import importlib.metadata

            manifest["package_version"] = importlib.metadata.version(
                "aafc-herbarium-dwc-extraction"
            )
        except (importlib.metadata.PackageNotFoundError, ModuleNotFoundError):
            pass

    return manifest


def build_meta_xml(output_dir: Path) -> Path:
    """Create ``meta.xml`` for a Darwin Core Archive.

    Parameters
    ----------
    output_dir:
        Directory containing ``occurrence.csv`` and ``identification_history.csv``.

    Returns
    -------
    Path to the written ``meta.xml`` file.
    """
    from io_utils.write import IDENT_HISTORY_COLUMNS

    output_dir.mkdir(parents=True, exist_ok=True)
    root = Element("meta", xmlns="http://rs.tdwg.org/dwc/text/")

    core = SubElement(
        root,
        "core",
        {
            "encoding": "UTF-8",
            "linesTerminatedBy": "\n",
            "fieldsTerminatedBy": ",",
            "fieldsEnclosedBy": '"',
            "ignoreHeaderLines": "1",
            "rowType": _dwc_term("Occurrence"),
        },
    )
    files_el = SubElement(core, "files")
    SubElement(files_el, "location").text = "occurrence.csv"
    SubElement(core, "id", index="0")
    for idx, term in enumerate(DWC_TERMS):
        SubElement(core, "field", index=str(idx), term=_dwc_term(term))

    ext = SubElement(
        root,
        "extension",
        {
            "encoding": "UTF-8",
            "linesTerminatedBy": "\n",
            "fieldsTerminatedBy": ",",
            "fieldsEnclosedBy": '"',
            "ignoreHeaderLines": "1",
            "rowType": "http://rs.gbif.org/terms/1.0/Identification",
        },
    )
    files_el = SubElement(ext, "files")
    SubElement(files_el, "location").text = "identification_history.csv"
    SubElement(ext, "coreid", index="0")
    for idx, col in enumerate(IDENT_HISTORY_COLUMNS):
        uri = IDENT_HISTORY_URIS.get(col, _dwc_term(col))
        SubElement(ext, "field", index=str(idx), term=uri)

    xml_bytes = tostring(root, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="UTF-8")
    meta_path = output_dir / "meta.xml"
    meta_path.write_bytes(pretty)
    return meta_path


def create_archive(
    output_dir: Path,
    *,
    compress: bool = False,
    version: str | None = None,
    filters: Dict[str, Any] | None = None,
    bundle_format: str = "simple",
    include_checksums: bool = False,
    additional_files: List[str] | None = None,
) -> Path:
    """Ensure DwC-A sidecar files exist and optionally create a ZIP archive.

    Parameters
    ----------
    output_dir:
        Directory containing DwC CSV exports.
    compress:
        If ``True``, a versioned ``dwca`` bundle will be created in ``output_dir``
        containing the CSV files, ``meta.xml`` and ``manifest.json``.
    version:
        Semantic version string for the bundle when ``compress`` is ``True``.
    filters:
        Criteria used for the export; recorded in the manifest.
    bundle_format:
        Bundle filename format: "rich" (with full metadata) or "simple" (version only).
    include_checksums:
        Whether to include file checksums in the manifest.
    additional_files:
        Additional files to include in the archive beyond the standard set.

    Returns
    -------
    Path to ``meta.xml`` if ``compress`` is ``False``; otherwise the path to the
    created ZIP file.
    """

    from io_utils.write import write_manifest

    manifest = build_manifest(filters, version=version)
    write_manifest(output_dir, manifest)
    meta_path = build_meta_xml(output_dir)
    if not compress:
        return meta_path

    if version is None or not SEMVER_RE.match(version):
        raise ValueError("version must be provided and follow semantic versioning")

    return create_versioned_bundle(
        output_dir=output_dir,
        version=version,
        filters=filters,
        bundle_format=bundle_format,
        include_checksums=include_checksums,
        additional_files=additional_files,
    )


def create_versioned_bundle(
    output_dir: Path,
    version: str,
    filters: Dict[str, Any] | None = None,
    bundle_format: str = "rich",
    include_checksums: bool = True,
    additional_files: List[str] | None = None,
) -> Path:
    """Create a semantically versioned DwC-A bundle with rich provenance tags.

    The resulting archive filename incorporates the provided semantic version,
    the export timestamp, the current commit hash, and a hash of any filter
    criteria. The same information is stored in ``manifest.json``.

    Parameters
    ----------
    output_dir:
        Directory where the bundle should be created.
    version:
        Semantic version of the export (e.g. ``"1.0.0"``).
    filters:
        Optional criteria used for the export.
    bundle_format:
        Bundle filename format: "rich" (with full metadata) or "simple" (version only).
    include_checksums:
        Whether to include file checksums in the manifest.
    additional_files:
        Additional files to include in the archive beyond the standard set.

    Returns
    -------
    Path
        Path to the created ZIP bundle.
    """
    logger = logging.getLogger(__name__)

    if not SEMVER_RE.match(version):
        raise ValueError("version must follow semantic versioning")

    manifest = build_manifest(filters, version=version)

    # Build archive filename based on format preference
    if bundle_format == "simple":
        archive_name = f"dwca_v{version}.zip"
        manifest["bundle_format"] = "simple"
    else:  # rich format
        # Construct a compact timestamp tag like YYYYMMDDTHHMMSSZ
        ts_tag = manifest["timestamp"].replace("+00:00", "Z").replace("-", "").replace(":", "")

        # Stable hash of filters for the filename; empty if no filters provided
        filter_hash = ""
        if filters:
            filters_json = json.dumps(filters, sort_keys=True)
            filter_hash = hashlib.sha256(filters_json.encode()).hexdigest()[:8]

        tag_parts = [f"v{version}", ts_tag]
        if manifest.get("git_commit_short"):
            tag_parts.append(manifest["git_commit_short"])
        if filter_hash:
            tag_parts.append(filter_hash)

        archive_tag = "_".join(tag_parts)
        archive_name = f"dwca_{archive_tag}.zip"
        manifest["bundle_format"] = "rich"
        manifest["archive_tag"] = archive_tag

    # Standard files to include
    standard_files = [
        "occurrence.csv",
        "identification_history.csv",
        "meta.xml",
        "manifest.json",
    ]

    # Add any additional files requested
    files_to_include = standard_files.copy()
    if additional_files:
        files_to_include.extend(additional_files)

    # Calculate checksums if requested
    if include_checksums:
        file_checksums = {}
        for name in files_to_include:
            file_path = output_dir / name
            if file_path.exists():
                with open(file_path, "rb") as f:
                    content = f.read()
                    file_checksums[name] = {
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "size_bytes": len(content),
                    }
        manifest["file_checksums"] = file_checksums

    # Write the enhanced manifest
    from io_utils.write import write_manifest

    write_manifest(output_dir, manifest)
    build_meta_xml(output_dir)

    archive_path = output_dir / archive_name
    logger.info(f"Creating archive: {archive_path.name}")

    with ZipFile(archive_path, "w", ZIP_DEFLATED) as zf:
        files_added = []
        for name in files_to_include:
            file_path = output_dir / name
            if file_path.exists():
                zf.write(file_path, arcname=name)
                files_added.append(name)
            else:
                logger.warning(f"Requested file {name} not found, skipping")

        logger.info(f"Archive created with {len(files_added)} files: {', '.join(files_added)}")

    return archive_path
