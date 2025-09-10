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
from typing import Any, Dict
from datetime import datetime, timezone
import subprocess
import re
import json
import hashlib

from .schema import DWC_TERMS
from io_utils.write import IDENT_HISTORY_COLUMNS, write_manifest


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


def build_manifest(filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return run metadata for archive exports."""
    commit = "unknown"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": timestamp,
        "commit": commit,
        "filters": filters or {},
    }


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

    Returns
    -------
    Path to ``meta.xml`` if ``compress`` is ``False``; otherwise the path to the
    created ZIP file.
    """

    manifest = build_manifest(filters)
    write_manifest(output_dir, manifest)
    meta_path = build_meta_xml(output_dir)
    if not compress:
        return meta_path

    if version is None or not SEMVER_RE.match(version):
        raise ValueError("version must be provided and follow semantic versioning")

    archive_path = output_dir / f"dwca_v{version}.zip"
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as zf:
        for name in [
            "occurrence.csv",
            "identification_history.csv",
            "meta.xml",
            "manifest.json",
        ]:
            file_path = output_dir / name
            if file_path.exists():
                zf.write(file_path, arcname=name)
    return archive_path


def create_versioned_bundle(
    output_dir: Path, version: str, filters: Dict[str, Any] | None = None
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

    Returns
    -------
    Path
        Path to the created ZIP bundle.
    """

    if not SEMVER_RE.match(version):
        raise ValueError("version must follow semantic versioning")

    manifest = build_manifest(filters)
    # Construct a compact timestamp tag like YYYYMMDDTHHMMSSZ
    ts_tag = manifest["timestamp"].replace("+00:00", "Z").replace("-", "").replace(":", "")
    # Stable hash of filters for the filename; empty if no filters provided
    filter_hash = ""
    if filters:
        filters_json = json.dumps(filters, sort_keys=True)
        filter_hash = hashlib.sha256(filters_json.encode()).hexdigest()[:8]

    tag_parts = [f"v{version}", ts_tag, manifest["commit"][:7]]
    if filter_hash:
        tag_parts.append(filter_hash)
    tag = "_".join(tag_parts)
    manifest["version"] = tag

    write_manifest(output_dir, manifest)
    build_meta_xml(output_dir)

    archive_path = output_dir / f"dwca_{tag}.zip"
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as zf:
        for name in [
            "occurrence.csv",
            "identification_history.csv",
            "meta.xml",
            "manifest.json",
        ]:
            file_path = output_dir / name
            if file_path.exists():
                zf.write(file_path, arcname=name)
    return archive_path
