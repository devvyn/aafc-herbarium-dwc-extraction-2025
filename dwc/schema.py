from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

from pydantic import BaseModel, ConfigDict

DEFAULT_SCHEMA_URI = "http://rs.tdwg.org/dwc/terms/"

# Project-specific terms appended after schema loading
PROJECT_TERMS = [
    "scientificName_verbatim",
    "verbatimEventDate",
    "eventDateUncertaintyInDays",
    "datasetName",
    "verbatimLabel",
    "flags",
]


def resolve_term(term: str) -> str:
    """Return the local Darwin Core term from a URI or prefixed name."""

    if term.startswith("http://") or term.startswith("https://"):
        term = term.rstrip("/").split("/")[-1]
    if ":" in term:
        term = term.split(":", 1)[1]
    return term


def _parse_schema(path: Path) -> List[str]:
    terms: List[str] = []
    try:
        tree = ET.parse(path)
    except Exception:  # pragma: no cover - malformed schemas
        return terms
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    for elem in tree.findall(".//xs:element", ns):
        name = elem.get("name")
        if name:
            terms.append(name)
    return terms


def load_schema_terms(schema_files: Optional[Iterable[Path]] = None) -> List[str]:
    """Load Darwin Core/ABCD terms from the given schema files."""

    if not schema_files:
        base = resources.files("config").joinpath("schemas")
        schema_files = [base / "dwc.xsd", base / "abcd.xsd"]
    terms: List[str] = []
    for path in schema_files:
        if path.exists():
            terms.extend(_parse_schema(path))
    return terms + PROJECT_TERMS

# Darwin Core terms supported by this project.  These mirror the column order
# used when writing CSV output.  The list is based on the AAFC-SRDC example
# dataset and extended with a few project-specific fields at the end.
DWC_TERMS = load_schema_terms()


def configure_terms(schema_files: Iterable[Path]) -> None:
    """Override ``DWC_TERMS`` using alternative schema files."""

    global DWC_TERMS
    DWC_TERMS = load_schema_terms(schema_files)


class DwcRecord(BaseModel):
    """Pydantic model representing a single Darwin Core record.

    All fields are optional strings.  When serialised via :meth:`to_dict`
    missing values are converted to empty strings so that CSV output is
    consistent.
    """

    model_config = ConfigDict(extra="allow")

    occurrenceID: Optional[str] = None
    catalogNumber: Optional[str] = None
    otherCatalogNumbers: Optional[str] = None
    institutionCode: Optional[str] = None
    collectionCode: Optional[str] = None
    ownerInstitutionCode: Optional[str] = None
    basisOfRecord: Optional[str] = None
    preparations: Optional[str] = None
    hasFragmentPacket: Optional[str] = None
    disposition: Optional[str] = None
    recordedBy: Optional[str] = None
    recordedByID: Optional[str] = None
    recordNumber: Optional[str] = None
    eventDate: Optional[str] = None
    eventTime: Optional[str] = None
    country: Optional[str] = None
    stateProvince: Optional[str] = None
    county: Optional[str] = None
    municipality: Optional[str] = None
    locality: Optional[str] = None
    verbatimLocality: Optional[str] = None
    decimalLatitude: Optional[str] = None
    decimalLongitude: Optional[str] = None
    geodeticDatum: Optional[str] = None
    coordinateUncertaintyInMeters: Optional[str] = None
    habitat: Optional[str] = None
    eventRemarks: Optional[str] = None
    scientificName: Optional[str] = None
    scientificNameAuthorship: Optional[str] = None
    taxonRank: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    specificEpithet: Optional[str] = None
    infraspecificEpithet: Optional[str] = None
    identificationQualifier: Optional[str] = None
    identifiedBy: Optional[str] = None
    dateIdentified: Optional[str] = None
    identificationRemarks: Optional[str] = None
    identificationReferences: Optional[str] = None
    identificationVerificationStatus: Optional[str] = None
    associatedOccurrences: Optional[str] = None
    occurrenceRemarks: Optional[str] = None
    dynamicProperties: Optional[str] = None
    scientificName_verbatim: Optional[str] = None
    verbatimEventDate: Optional[str] = None
    eventDateUncertaintyInDays: Optional[str] = None
    datasetName: Optional[str] = None
    verbatimLabel: Optional[str] = None
    flags: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Return a dictionary representation suitable for CSV writing.

        Any ``None`` values are converted to empty strings and only known
        Darwin Core terms are returned.
        """

        return {term: getattr(self, term) or "" for term in DWC_TERMS}
