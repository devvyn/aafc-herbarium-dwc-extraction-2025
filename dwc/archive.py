from __future__ import annotations

from pathlib import Path
from typing import Dict
from xml.etree.ElementTree import Element, SubElement, ElementTree
import zipfile

from dwc.schema import DWC_TERMS
from io_utils.write import IDENT_HISTORY_COLUMNS

DWC_NS = "http://rs.tdwg.org/dwc/terms/"
DC_NS = "http://purl.org/dc/terms/"
GBIF_NS = "http://rs.gbif.org/terms/1.0/"
TEXT_NS = "http://rs.tdwg.org/dwc/text/"

IDENT_HISTORY_TERMS: Dict[str, str] = {
    "occurrenceID": DWC_NS + "occurrenceID",
    "identificationID": DC_NS + "identifier",
    "identifiedBy": DWC_NS + "identifiedBy",
    "dateIdentified": DWC_NS + "dateIdentified",
    "scientificName": DWC_NS + "scientificName",
    "scientificNameAuthorship": DWC_NS + "scientificNameAuthorship",
    "taxonRank": DWC_NS + "taxonRank",
    "identificationQualifier": DWC_NS + "identificationQualifier",
    "identificationRemarks": DWC_NS + "identificationRemarks",
    "identificationReferences": DWC_NS + "identificationReferences",
    "identificationVerificationStatus": DWC_NS + "identificationVerificationStatus",
    "isCurrent": GBIF_NS + "isCurrent",
}


def build_meta_xml() -> ElementTree:
    """Return an :class:`ElementTree` representing Darwin Core meta.xml."""
    root = Element("meta", xmlns=TEXT_NS)

    core = SubElement(
        root,
        "core",
        encoding="UTF-8",
        linesTerminatedBy="\n",
        fieldsTerminatedBy=",",
        fieldsEnclosedBy='"',
        ignoreHeaderLines="1",
        rowType=DWC_NS + "Occurrence",
    )
    files = SubElement(core, "files")
    SubElement(files, "location").text = "occurrence.csv"
    SubElement(core, "id", index="0")
    for idx, term in enumerate(DWC_TERMS):
        SubElement(core, "field", index=str(idx), term=DWC_NS + term)

    ext = SubElement(
        root,
        "extension",
        encoding="UTF-8",
        linesTerminatedBy="\n",
        fieldsTerminatedBy=",",
        fieldsEnclosedBy='"',
        ignoreHeaderLines="1",
        rowType=GBIF_NS + "Identification",
    )
    files = SubElement(ext, "files")
    SubElement(files, "location").text = "identification_history.csv"
    SubElement(ext, "coreid", index="0")
    for idx, col in enumerate(IDENT_HISTORY_COLUMNS):
        term = IDENT_HISTORY_TERMS[col]
        SubElement(ext, "field", index=str(idx), term=term)

    return ElementTree(root)


def write_meta_xml(output_dir: Path) -> Path:
    """Serialize ``meta.xml`` to ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / "meta.xml"
    tree = build_meta_xml()
    tree.write(meta_path, encoding="UTF-8", xml_declaration=True)
    return meta_path


def build_dwca(output_dir: Path, compress: bool = False) -> Path:
    """Write ``meta.xml`` and optionally zip into a Darwin Core Archive.

    Parameters
    ----------
    output_dir:
        Directory containing ``occurrence.csv`` and ``identification_history.csv``.
    compress:
        If ``True``, produce ``dwca.zip`` containing all components.

    Returns
    -------
    Path
        Path to ``meta.xml`` or the generated zip archive when ``compress`` is
        ``True``.
    """
    meta_path = write_meta_xml(output_dir)
    if not compress:
        return meta_path

    archive_path = output_dir / "dwca.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ["occurrence.csv", "identification_history.csv", "meta.xml"]:
            zf.write(output_dir / name, arcname=name)
    return archive_path
