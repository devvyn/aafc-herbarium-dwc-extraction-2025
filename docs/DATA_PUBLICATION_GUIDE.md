# Data Publication Guide: GBIF/Canadensys Strategy

**Project:** AAFC Herbarium Darwin Core Extraction
**Dataset:** 2,885 herbarium specimen images + metadata
**Status:** v1.0 Complete, v2.0 In Progress
**Date:** October 6, 2025

## Executive Summary

This guide outlines the strategy for publishing the AAFC herbarium dataset to the Global Biodiversity Information Facility (GBIF) via Canadensys, following established AAFC protocols from the BioMob digitization initiative.

## Publication Platforms

### Primary: GBIF via Canadensys

**Recommendation:** Canadensys IPT (Integrated Publishing Toolkit)

**Rationale:**
- AAFC already uses Canadensys for herbarium data
- BioMob initiative published 3.5M records via this route (2016-2022)
- Direct integration with GBIF (world's largest biodiversity database)
- DOI assignment for citations
- CC0 license support (public domain dedication)

**Canadensys Portal:** https://data.canadensys.net/ipt/

### Secondary: Open Government Portal

**Canada Open Data Portal:** https://open.canada.ca/

**Benefits:**
- Government mandate for open science
- Canadian public access priority
- Complements international GBIF publication
- No DOI required (optional dataset registration)

## Data Format: Darwin Core Archive (DwC-A)

### Structure

Darwin Core Archive is a ZIP file containing:

```
dwc-a.zip
├── meta.xml                    # Archive metadata descriptor
├── eml.xml                     # Ecological Metadata Language (dataset info)
├── occurrence.txt              # Darwin Core occurrence records (CSV)
└── images/                     # Optional: specimen images
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```

### Occurrence Records Format

Tab-delimited text file with Darwin Core terms:

```csv
catalogNumber\tscientificName\teventDate\trecordedBy\tlocality\tstateProvince\tcountry
019121\tBouteloua gracilis (HBK.) Lag.\t1969-08-14\tJ. Looman\tBeaver River crossing; hiway 26\tSaskatchewan\tCanada
```

**v1.0 Fields (7):**
- catalogNumber
- scientificName
- eventDate
- recordedBy
- locality
- stateProvince
- country

**v2.0 Fields (16):** *All of above plus:*
- habitat
- minimumElevationInMeters
- recordNumber
- identifiedBy
- dateIdentified
- verbatimLocality
- verbatimEventDate
- verbatimElevation
- associatedTaxa

### Metadata (EML) Requirements

```xml
<eml>
  <dataset>
    <title>AAFC Herbarium Specimen Collection - Saskatchewan</title>
    <creator>
      <organizationName>Agriculture and Agri-Food Canada</organizationName>
      <address>
        <deliveryPoint>Saskatoon Research and Development Centre</deliveryPoint>
        <city>Saskatoon</city>
        <administrativeArea>Saskatchewan</administrativeArea>
        <country>Canada</country>
      </address>
    </creator>
    <abstract>
      Digital herbarium specimens from AAFC collection, focusing on
      Saskatchewan grassland flora. Extracted via Vision API + GPT-4o-mini
      with layout-aware Darwin Core mapping.
    </abstract>
    <intellectualRights>
      <para>
        This work is licensed under CC0 1.0 Universal (Public Domain Dedication).
        To the extent possible under law, Agriculture and Agri-Food Canada has
        waived all copyright and related rights to this dataset.
      </para>
    </intellectualRights>
    <coverage>
      <geographicCoverage>
        <geographicDescription>Saskatchewan, Canada</geographicDescription>
        <boundingCoordinates>
          <westBoundingCoordinate>-110</westBoundingCoordinate>
          <eastBoundingCoordinate>-101</eastBoundingCoordinate>
          <northBoundingCoordinate>60</northBoundingCoordinate>
          <southBoundingCoordinate>49</southBoundingCoordinate>
        </boundingCoordinates>
      </geographicCoverage>
      <temporalCoverage>
        <rangeOfDates>
          <beginDate>
            <calendarDate>1960</calendarDate>
          </beginDate>
          <endDate>
            <calendarDate>2000</calendarDate>
          </endDate>
        </rangeOfDates>
      </temporalCoverage>
    </coverage>
  </dataset>
</eml>
```

## Licensing Strategy

### Recommended: CC0 1.0 Universal

**Public Domain Dedication**

**Rationale:**
- Standard for scientific biodiversity data
- Maximum reusability (no attribution required, though encouraged)
- GBIF recommendation for occurrence data
- Aligns with open science principles
- Simplifies derivative use (education, research, conservation)

**Legal Text:** https://creativecommons.org/publicdomain/zero/1.0/

### Alternative: CC BY 4.0

**Attribution Required**

**Considerations:**
- Requires attribution in all uses
- Slightly reduced reusability (some platforms avoid BY licensing)
- Appropriate if institutional credit is priority

**Recommendation:** Use CC0 unless institutional policy requires BY

## Publication Workflow

### Phase 1: Prepare Darwin Core Archive

**Tools:**
- Python script to convert JSONL → DwC CSV
- EML generator for dataset metadata
- IPT web interface (Canadensys hosted)

**Steps:**
1. Convert extraction results to occurrence.txt
   ```python
   # Convert v1.0 baseline (2,885 specimens)
   python scripts/export_dwc_archive.py \
     --input deliverables/v1.0_vision_api_baseline.jsonl \
     --output dwc-archive/occurrence.txt
   ```

2. Generate EML metadata
   ```python
   python scripts/generate_eml.py \
     --title "AAFC Herbarium - Saskatchewan Flora" \
     --creator "Agriculture and Agri-Food Canada" \
     --license CC0 \
     --output dwc-archive/eml.xml
   ```

3. Package images (optional, if sharing originals)
   ```bash
   mkdir dwc-archive/images
   cp /tmp/imgcache/*.jpg dwc-archive/images/
   ```

4. Create meta.xml descriptor
   ```xml
   <archive>
     <core rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
       <files>
         <location>occurrence.txt</location>
       </files>
       <field index="0" term="http://rs.tdwg.org/dwc/terms/catalogNumber"/>
       <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
       <!-- ... additional fields ... -->
     </core>
   </archive>
   ```

5. ZIP the archive
   ```bash
   cd dwc-archive && zip -r aafc-herbarium-dwc-a.zip *
   ```

### Phase 2: Upload to Canadensys IPT

**Access:** Requires Canadensys account (coordinate with AAFC IT)

**IPT Workflow:**
1. Log in to https://data.canadensys.net/ipt/
2. Create new resource: "AAFC Herbarium - Saskatchewan"
3. Upload occurrence.txt
4. Map columns to Darwin Core terms
5. Upload EML metadata
6. Set license: CC0
7. Validate dataset (IPT checks DwC compliance)
8. Preview publication
9. **Submit for review** (Canadensys moderators)

**Timeline:** 1-2 weeks for review and publication

### Phase 3: Obtain DOI

**Automatic via IPT:**
- DOI assigned upon publication
- Minted through DataCite registry
- Permanent identifier for citations

**Example DOI:** `10.5886/aafc.herbarium.2025`

### Phase 4: Register with GBIF

**Automatic via Canadensys:**
- IPT automatically syncs to GBIF
- Dataset appears in GBIF portal within 24-48 hours
- Searchable by species, location, date

**GBIF Portal:** https://www.gbif.org/dataset/[auto-generated-uuid]

## Institutional Approval

### AAFC Requirements

**Check with:**
- AAFC SRDC Research Data Management team
- BioMob initiative contacts (if still active)
- Institutional repository coordinators

**Questions to clarify:**
1. Is AAFC pre-approval needed for public data release?
2. Which license does AAFC prefer (CC0 vs CC BY)?
3. Should images be included or metadata only?
4. Any sensitive locality data restrictions? (rare/endangered species)

**Precedent:** BioMob published 3.5M records openly (2016-2022), suggesting institutional support for open biodiversity data.

## Image Sharing Strategy

### Option 1: Metadata Only (Recommended for v1.0)

**Publish:** Darwin Core records with URLs pointing to AAFC servers

**Benefits:**
- Smaller package size
- Institutional control over image hosting
- Easier updates/corrections

**Image URLs in DwC:**
```csv
associatedMedia: https://herbarium.agr.gc.ca/images/019121.jpg
```

### Option 2: Full Image Archive

**Publish:** Images bundled in DwC-A (or separate Zenodo deposit)

**Benefits:**
- Complete preservation package
- No dependency on institutional servers
- Archival redundancy (GBIF + Zenodo)

**Considerations:**
- Large file size (~5-10 GB for 2,885 images)
- Upload bandwidth/time
- Storage costs (if Zenodo)

**Recommendation:** Start with metadata-only (v1.0), add images for v2.0 if stakeholders request

## Quality Documentation

### Required Disclosures

**Data Quality Statement in EML:**

```xml
<dataQuality>
  <report>
    <description>
      Extraction Method: Apple Vision API (v1.0) + GPT-4o-mini (v2.0)

      v1.0 Baseline Quality:
      - 7 Darwin Core fields extracted
      - ~5% scientificName completeness
      - Known OCR limitations on handwritten labels
      - Suitable for initial dataset, refinement ongoing

      v2.0 Enhanced Quality:
      - 16 Darwin Core fields extracted
      - Layout-aware prompts (TOP vs BOTTOM label distinction)
      - Improved accuracy on scientificName, habitat, elevation
      - Validated against 20-specimen ground truth sample

      Validation: 20 specimens manually corrected (see human_validation.jsonl)

      Recommended Use: Ecological research, species distribution modeling,
      taxonomic studies. Verify critical identifications against images.
    </description>
  </report>
</dataQuality>
```

## Timeline & Milestones

### Week 1: v1.0 Publication Prep
- [ ] Export v1.0 baseline to DwC CSV
- [ ] Generate EML metadata
- [ ] Create DwC-A package
- [ ] Validate with GBIF Data Validator
- [ ] Obtain AAFC institutional approval

### Week 2: Canadensys Submission
- [ ] Request Canadensys IPT account (if needed)
- [ ] Upload dataset to IPT
- [ ] Map fields and configure metadata
- [ ] Submit for Canadensys review
- [ ] Address any reviewer feedback

### Week 3: GBIF Publication
- [ ] Canadensys approves and publishes
- [ ] DOI assigned
- [ ] Dataset syncs to GBIF
- [ ] Verify GBIF portal display
- [ ] Announce publication (AAFC channels)

### Week 4-5: v2.0 Update (if v2 extraction complete)
- [ ] Export v2.0 enhanced data (16 fields)
- [ ] Update EML with v2.0 quality notes
- [ ] Replace dataset in IPT
- [ ] New version published to GBIF
- [ ] DOI version increment (10.5886/aafc.herbarium.2025.2)

## Citation Format

**GBIF Auto-Generated Citation:**

```
Agriculture and Agri-Food Canada (2025). AAFC Herbarium - Saskatchewan Flora.
Version 1.0. Agriculture and Agri-Food Canada. Occurrence dataset
https://doi.org/10.5886/aafc.herbarium.2025 accessed via GBIF.org on YYYY-MM-DD.
```

**Recommended Project Citation:**

```
Murphy, D., Agriculture and Agri-Food Canada (2025). AAFC Herbarium Darwin Core
Extraction: Automated digitization of 2,885 Saskatchewan specimens using Vision
API and GPT-4o-mini. Dataset published via Canadensys and GBIF.
https://doi.org/10.5886/aafc.herbarium.2025
```

## Implementation Scripts

### Export DwC CSV

**Location:** `scripts/export_dwc_archive.py`

```python
#!/usr/bin/env python3
"""Export extraction results to Darwin Core CSV for GBIF publication."""

import json
from pathlib import Path
from typing import Dict, List

def load_extractions(jsonl_path: Path) -> List[Dict]:
    """Load extraction results from JSONL."""
    records = []
    with jsonl_path.open() as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def to_dwc_occurrence(record: Dict) -> Dict[str, str]:
    """Convert extraction record to Darwin Core occurrence."""
    dwc = record.get("dwc", {})

    return {
        "catalogNumber": dwc.get("catalogNumber", ""),
        "scientificName": dwc.get("scientificName", ""),
        "eventDate": dwc.get("eventDate", ""),
        "recordedBy": dwc.get("recordedBy", ""),
        "locality": dwc.get("locality", ""),
        "stateProvince": dwc.get("stateProvince", ""),
        "country": dwc.get("country", ""),
        # v2.0 fields
        "habitat": dwc.get("habitat", ""),
        "minimumElevationInMeters": dwc.get("minimumElevationInMeters", ""),
        "recordNumber": dwc.get("recordNumber", ""),
        "identifiedBy": dwc.get("identifiedBy", ""),
        # Image reference
        "associatedMedia": f"https://herbarium.agr.gc.ca/images/{record.get('sha256', '')}.jpg",
    }

def export_dwc_csv(input_jsonl: Path, output_csv: Path) -> None:
    """Export JSONL extractions to DwC CSV."""
    records = load_extractions(input_jsonl)
    occurrences = [to_dwc_occurrence(r) for r in records]

    # Write CSV
    import csv
    fields = list(occurrences[0].keys())

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(occurrences)

    print(f"Exported {len(occurrences)} occurrences to {output_csv}")

if __name__ == "__main__":
    import sys

    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("deliverables/v1.0_vision_api_baseline.jsonl")
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dwc-archive/occurrence.txt")

    export_dwc_csv(input_file, output_file)
```

### Generate EML

**Location:** `scripts/generate_eml.py`

```python
#!/usr/bin/env python3
"""Generate EML metadata for Darwin Core Archive publication."""

from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

def generate_eml(
    title: str,
    creator_org: str,
    license: str,
    output_path: Path,
) -> None:
    """Generate EML metadata XML."""

    eml = ET.Element("eml:eml", {
        "xmlns:eml": "eml://ecoinformatics.org/eml-2.1.1",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "system": "canadensys",
    })

    dataset = ET.SubElement(eml, "dataset")

    # Title
    title_elem = ET.SubElement(dataset, "title")
    title_elem.text = title

    # Creator
    creator = ET.SubElement(dataset, "creator")
    org_name = ET.SubElement(creator, "organizationName")
    org_name.text = creator_org

    # License
    rights = ET.SubElement(dataset, "intellectualRights")
    para = ET.SubElement(rights, "para")
    if license == "CC0":
        para.text = "This work is licensed under CC0 1.0 Universal (Public Domain Dedication)."

    # Pretty print
    xml_str = minidom.parseString(ET.tostring(eml)).toprettyxml(indent="  ")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_str, encoding="utf-8")

    print(f"Generated EML metadata: {output_path}")

if __name__ == "__main__":
    generate_eml(
        title="AAFC Herbarium - Saskatchewan Flora",
        creator_org="Agriculture and Agri-Food Canada",
        license="CC0",
        output_path=Path("dwc-archive/eml.xml"),
    )
```

## Deployment Context Considerations

### Personal Mac Environment (Development)

**Current Setup:**
- macOS with full tool access (uv, homebrew, Python 3.11)
- No workplace IT restrictions
- Third-party cloud services available (OpenAI, Anthropic)
- Local processing and testing unrestricted

**Advantages:**
- Rapid prototyping and iteration
- Full extraction pipeline testing
- Direct API integration
- Flexible deployment options

**Use Cases:**
- Pipeline development
- Quality validation
- Test extractions
- Documentation preparation

### Work Windows Environment (Production)

**AAFC SRDC Constraints:**
- Windows 10/11 with IT management
- Restricted software installation (may require IT approval)
- Potential limitations on cloud service access
- VPN/network security policies

**Considerations:**
1. **Export scripts should be portable**
   - Python standard library preferred
   - Minimize external dependencies
   - Document uv alternative: `pip install -r requirements.txt`

2. **Data validation can run offline**
   - GBIF validator is web-based (no install needed)
   - DwC CSV is plain text (Excel compatible)

3. **IPT access is web-based**
   - No local installation required
   - Canadensys hosted instance
   - Browser-only workflow

4. **Image hosting considerations**
   - If AAFC servers used for associatedMedia URLs
   - Coordinate with IT for public accessibility
   - Alternative: Bundle images in DwC-A (no server dependency)

### Hybrid Workflow Recommendation

**Phase 1: Development (Personal Mac)**
- Extract metadata with full pipeline
- Generate DwC CSV and EML
- Validate with GBIF tools
- Create complete DwC-A package

**Phase 2: Institutional Upload (Work Windows)**
- Transfer DwC-A package via secure method
- Upload to Canadensys IPT from work computer
- Coordinate with AAFC IT for any approvals
- Monitor GBIF publication from work environment

**Phase 3: Maintenance (Context-Flexible)**
- Updates can be prepared on either system
- Final upload from institutional account
- Version control via GitHub (accessible from both)

### Data Sensitivity Note

**Public Data = Flexible Deployment:**
- Herbarium specimens are public scientific data
- No AAFC confidentiality restrictions
- Safe to process on personal systems
- Cloud API usage appropriate (OpenAI, etc.)

**If Data Were Sensitive:**
- Restrict to AAFC network only
- No third-party cloud services
- On-premises processing required
- Different architecture needed

**Current Project:** Public data enables optimal development workflow on personal Mac, with straightforward transfer to institutional publication when ready.

## Resources

### Documentation
- **Darwin Core Standard:** https://dwc.tdwg.org/
- **GBIF Data Publishing:** https://www.gbif.org/publishing-data
- **Canadensys IPT:** https://data.canadensys.net/ipt/
- **CC0 License:** https://creativecommons.org/publicdomain/zero/1.0/

### Tools
- **GBIF Data Validator:** https://www.gbif.org/tools/data-validator
- **Darwin Core Validator:** https://tools.gbif.org/dwca-validator/
- **IPT Installation Guide:** https://ipt.gbif.org/manual/en/ipt/latest/

### AAFC Context
- **BioMob Initiative:** $30M digitization project (2016-2022)
- **AAFC Collections:** 3.5M records published to GBIF
- **Canadensys:** Canada's GBIF node, hosts AAFC data

---

**Next Steps:**
1. Obtain AAFC institutional approval for publication
2. Implement export scripts (DwC CSV, EML generation)
3. Create v1.0 Darwin Core Archive
4. Submit to Canadensys IPT
5. Coordinate with GBIF publication timeline

*Generated with Claude Code on October 6, 2025*
