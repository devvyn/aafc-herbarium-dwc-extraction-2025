from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict

# Darwin Core terms supported by this project.  These mirror the
# column order used when writing CSV output.  Centralising the list here
# allows other modules to refer to it and keeps the schema and output in
# sync.
DWC_TERMS = [
    "catalogNumber",
    "collectionCode",
    "institutionCode",
    "ownerInstitutionCode",
    "scientificName",
    "scientificNameAuthorship",
    "scientificName_verbatim",
    "recordedBy",
    "recordNumber",
    "eventDate",
    "verbatimEventDate",
    "eventDateUncertaintyInDays",
    "locality",
    "country",
    "stateProvince",
    "municipality",
    "identifiedBy",
    "dateIdentified",
    "identificationRemarks",
    "basisOfRecord",
    "datasetName",
    "occurrenceRemarks",
    "verbatimLabel",
    "flags",
]


class DwcRecord(BaseModel):
    """Pydantic model representing a single Darwin Core record.

    All fields are optional strings.  When serialised via :meth:`to_dict`
    missing values are converted to empty strings so that CSV output is
    consistent.
    """

    model_config = ConfigDict(extra="allow")

    catalogNumber: Optional[str] = None
    collectionCode: Optional[str] = None
    institutionCode: Optional[str] = None
    ownerInstitutionCode: Optional[str] = None
    scientificName: Optional[str] = None
    scientificNameAuthorship: Optional[str] = None
    scientificName_verbatim: Optional[str] = None
    recordedBy: Optional[str] = None
    recordNumber: Optional[str] = None
    eventDate: Optional[str] = None
    verbatimEventDate: Optional[str] = None
    eventDateUncertaintyInDays: Optional[str] = None
    locality: Optional[str] = None
    country: Optional[str] = None
    stateProvince: Optional[str] = None
    municipality: Optional[str] = None
    identifiedBy: Optional[str] = None
    dateIdentified: Optional[str] = None
    identificationRemarks: Optional[str] = None
    basisOfRecord: Optional[str] = None
    datasetName: Optional[str] = None
    occurrenceRemarks: Optional[str] = None
    verbatimLabel: Optional[str] = None
    flags: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Return a dictionary representation suitable for CSV writing.

        Any ``None`` values are converted to empty strings and only known
        Darwin Core terms are returned.
        """

        return {term: getattr(self, term) or "" for term in DWC_TERMS}
