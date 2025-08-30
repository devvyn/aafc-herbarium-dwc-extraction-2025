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
from typing import Dict

from .schema import DWC_TERMS
from io_utils.write import IDENT_HISTORY_COLUMNS


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
    "identificationVerificationStatus": _dwc_term(
        "identificationVerificationStatus"
    ),
    "isCurrent": "http://rs.gbif.org/terms/1.0/isCurrent",
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


def create_archive(output_dir: Path, *, compress: bool = False) -> Path:
    """Ensure DwC-A sidecar files exist and optionally create a ZIP archive.

    Parameters
    ----------
    output_dir:
        Directory containing DwC CSV exports.
    compress:
        If ``True``, a ``dwca.zip`` file will be created in ``output_dir``
        containing the CSV files and ``meta.xml``.

    Returns
    -------
    Path to ``meta.xml`` if ``compress`` is ``False``; otherwise the path to the
    created ZIP file.
    """

    meta_path = build_meta_xml(output_dir)
    if not compress:
        return meta_path

    archive_path = output_dir / "dwca.zip"
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as zf:
        for name in ["occurrence.csv", "identification_history.csv", "meta.xml"]:
            file_path = output_dir / name
            if file_path.exists():
                zf.write(file_path, arcname=name)
    return archive_path

