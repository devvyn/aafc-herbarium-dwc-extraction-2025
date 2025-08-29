from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict

# Darwin Core terms supported by this project. These mirror the column order
# used when writing CSV output. The list is based on the AAFC-SRDC example
# dataset and extended with a few project-specific fields at the end.
DWC_TERMS = [
    "occurrenceID",
    "catalogNumber",
    "otherCatalogNumbers",
    "institutionCode",
    "collectionCode",
    "ownerInstitutionCode",
    "basisOfRecord",
    "preparations",
    "hasFragmentPacket",
    "disposition",
    "recordedBy",
    "recordedByID",
    "recordNumber",
    "eventDate",
    "eventTime",
    "country",
    "stateProvince",
    "county",
    "municipality",
    "locality",
    "verbatimLocality",
    "decimalLatitude",
    "decimalLongitude",
    "geodeticDatum",
    "coordinateUncertaintyInMeters",
    "habitat",
    "eventRemarks",
    "scientificName",
    "scientificNameAuthorship",
    "taxonRank",
    "family",
    "genus",
    "specificEpithet",
    "infraspecificEpithet",
    "identificationQualifier",
    "identifiedBy",
    "dateIdentified",
    "identificationRemarks",
    "identificationReferences",
    "identificationVerificationStatus",
    "associatedOccurrences",
    "occurrenceRemarks",
    "dynamicProperties",
    # Project-specific extensions
    "scientificName_verbatim",
    "verbatimEventDate",
    "eventDateUncertaintyInDays",
    "datasetName",
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
