"""Rule-based Darwin Core field extraction from OCR text.

Extracts key Darwin Core fields using regex patterns and heuristics.
No external API calls required - completely free tier compatible.
"""

import re
from typing import Dict, Tuple, List

# Pattern library for Darwin Core field extraction
PATTERNS = {
    "catalogNumber": [
        r"(?:No|#|Number)[\s.:]*([A-Z0-9\-]+)",  # "No. 12345", "Number: ABC-123"
        r"AAFC[\s#:]*(\d+)",  # "AAFC 12345", "AAFC#12345"
        r"(?:DAS|DAO)[\s#:]*(\d+)",  # "DAS 9270"
        r"(?:Specimen|Spec)[\s#:]*([A-Z0-9\-]+)",  # "Specimen: ABC-123"
    ],
    "scientificName": [
        r"\n([A-Z][a-z]+\s+[a-z]+(?:\s+(?:var|subsp|f)\.\s+[a-z]+)?)\s+L\.",  # "Plantago major L."
        r"\n([A-Z][a-z]+\s+[a-z]+)\s*$",  # "Plantago major" on its own line
        r"(?:Species|Sp\.)[\s:]*([A-Z][a-z]+\s+[a-z]+)",  # "Species: Plantago major"
    ],
    "eventDate": [
        r"(?:Date|Collected)[\s:]*(\d{1,2}[\s\-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/]\d{2,4})",  # "Date: 15 July 2023"
        r"(?:Date|Collected)[\s:]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4})",  # "Date: Sept. 8, 1984"
        r"(\d{4}-\d{2}-\d{2})",  # "2023-07-15"
        r"(\d{1,2}/\d{1,2}/\d{2,4})",  # "7/15/2023"
    ],
    "recordedBy": [
        r"(?:Collector|Coll\.|Leg\.|Det\.)[\s:]*([A-Z][^,;\n]{2,40})",  # "Collector: John Smith"
        r"(?:by|BY)[\s:]+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",  # "by J. Smith"
    ],
    "locality": [
        r"(?:Locality|Location)[\s:]*([A-Z][^;\n]+(?:,\s*[A-Z][a-z]+)?)",  # "Locality: Regina, Saskatchewan"
        r"\n([A-Z][a-z]+,\s*[A-Z][a-z]+)",  # "Regina, Saskatchewan" on its own line
    ],
    "stateProvince": [
        r"(Saskatchewan|Alberta|Manitoba|Ontario|Quebec|British Columbia|Yukon|Northwest Territories|Nunavut)",
        r",\s*(SK|AB|MB|ON|QC|BC|YT|NT|NU)\b",  # Province abbreviations
    ],
    "country": [
        r"\b(Canada|United States|USA|Mexico)\b",
    ],
}


def text_to_dwc(text: str, **kwargs) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Extract Darwin Core fields from OCR text using pattern matching.

    Parameters
    ----------
    text : str
        Raw OCR text from specimen label
    **kwargs
        Additional arguments (ignored for rule-based extraction)

    Returns
    -------
    Tuple[Dict[str, str], Dict[str, float]]
        Tuple of (Darwin Core field dict, confidence scores dict)

    Notes
    -----
    - Pattern-based extraction, no external API calls
    - Free tier compatible
    - Confidence scores: 0.8 for pattern match, 0.0 for no match
    - Missing fields return empty string (graceful degradation)
    """
    dwc_data = {}
    confidences = {}

    # Try each field's patterns in order
    for field, patterns in PATTERNS.items():
        matched = False
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up extracted value
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                value = value.rstrip('.,;:')  # Remove trailing punctuation
                value = value.strip()  # Remove leading/trailing whitespace

                dwc_data[field] = value
                confidences[field] = 0.8  # Pattern match confidence
                matched = True
                break

        # Set empty string for missing fields
        if not matched:
            dwc_data[field] = ""
            confidences[field] = 0.0

    # Post-processing: Derive country from province if not found
    if not dwc_data.get("country") and dwc_data.get("stateProvince"):
        canadian_provinces = ["Saskatchewan", "Alberta", "Manitoba", "Ontario", "Quebec",
                             "British Columbia", "Yukon", "Northwest Territories", "Nunavut",
                             "SK", "AB", "MB", "ON", "QC", "BC", "YT", "NT", "NU"]
        if any(prov in dwc_data["stateProvince"] for prov in canadian_provinces):
            dwc_data["country"] = "Canada"
            confidences["country"] = 0.7  # Derived confidence slightly lower

    return dwc_data, confidences


__all__ = ["text_to_dwc"]
