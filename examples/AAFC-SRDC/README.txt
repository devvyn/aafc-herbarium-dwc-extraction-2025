Darwin Core Archive (DwC-A) — DAS pressed plant sheets

This sample uses the legacy code "DAS" (Department of Agriculture Saskatchewan). The canonical institution code is "AAFC-SRDC" — Agriculture and Agri-Food Canada Saskatoon Research and Development Centre.

Files:
  - occurrence.csv (core): one row per sheet (occurrence)
  - identification_history.csv (extension): 0..n rows per sheet, one per identification event
  - meta.xml: archive descriptor mapping columns to Darwin Core terms

Keys:
  - Core ID: occurrenceID (UUID/URI). Keep stable.
  - Extension: identificationID in column "identifier" is unique per identification event.
  - Extension links to core via occurrenceID.

Conventions:
  - basisOfRecord = PreservedSpecimen
  - hasFragmentPacket = TRUE/FALSE
  - identificationVerificationStatus ∈ {verified, provisional, unreviewed}
  - Dates: ISO 8601 (YYYY-MM-DD); ranges allowed in eventDate
  - dynamicProperties: JSON for structured provenance (transfers, OCR flags, etc.)

Load order:
  1) Fill/update occurrence.csv (current official identification lives here).
  2) Append to identification_history.csv for each (re)identification; set isCurrent accordingly.

Validation tips:
  - Exactly one isCurrent=TRUE per occurrence in identification_history.csv.
  - scientificName in core must match the single isCurrent=TRUE row.
  - If catalogNumber (DAS) is blank at intake, populate later without changing occurrenceID.
