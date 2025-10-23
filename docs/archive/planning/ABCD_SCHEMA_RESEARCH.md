# ABCD Schema Research and Mapping

## Overview

**ABCD** (Access to Biological Collection Data) is a comprehensive standard for biological collection data maintained by TDWG (Biodiversity Information Standards).

- **Current Version**: 2.06 (July 2015)
- **Official Documentation**: https://abcd.tdwg.org
- **GitHub Repository**: https://github.com/tdwg/abcd
- **Used By**: GBIF, BioCASe networks

## Purpose

ABCD is more comprehensive than Darwin Core, supporting:
- **Atomised data** and free-text
- **Institutional metadata** (staff attributions, workflow)
- **Specimen history** (revisions, verifications)
- **Rich relationships** between terms
- Wide variety of database structures

## Why ABCD for AAFC Herbarium?

Darwin Core is optimized for **biodiversity occurrence data**, but herbarium workflows need:

1. **Staff Attribution**
   - Who prepared the specimen
   - Who cataloged it
   - Who verified identifications
   - Multiple determination history

2. **Institutional Workflow**
   - Accession process tracking
   - Curation history
   - Loan tracking
   - Conservation status

3. **Specimen History**
   - Original collector (recordedBy)
   - Subsequent identifiers (identifiedBy)
   - Verification chain
   - Annotation history

## ABCD vs Darwin Core

### Darwin Core Fields (What we extract now)
```yaml
Core ID fields:
  - catalogNumber (institutional ID)
  - scientificName (current determination)
  - recordedBy (original field collector)

Location/Event:
  - locality, habitat, eventDate
  - stateProvince, country
  - coordinates

Limited History:
  - identifiedBy (single person)
  - identificationRemarks (notes)
```

### ABCD Additional Capabilities (Research needed)
```yaml
Institutional metadata:
  - PreparedBy (person, date, method)
  - CataloguedBy (person, date)
  - VerifiedBy (multiple, with dates)

Specimen history:
  - DeterminationHistory (full chain)
  - AnnotationHistory (all notes)
  - AcquisitionSource (how it entered collection)
  - LoanHistory (where it's been)

Organizational:
  - OrganizationalUnit (department, section)
  - ResponsibleDepartment
  - OwnerOrganization
```

## Implementation Plan

### Phase 1: Research (PENDING)
- [ ] Download ABCD 2.06 XML schema
- [ ] Identify fields for herbarium workflows
- [ ] Map Darwin Core → ABCD fields
- [ ] Document AAFC-specific needs

### Phase 2: Extraction Enhancement
- [ ] Add ABCD fields to prompts
- [ ] Test extraction quality
- [ ] Validate with AAFC staff

### Phase 3: Dual Export
- [ ] Darwin Core Archive (for GBIF)
- [ ] ABCD XML (for institutional record)
- [ ] Maintain both formats

## Next Actions

**Immediate**:
1. Download ABCD 2.06 schema from GitHub
2. Parse XML to extract field definitions
3. Create mapping table: Darwin Core ↔ ABCD

**Future**:
4. Implement ABCD export alongside Darwin Core
5. Test with GBIF Integrated Publishing Toolkit (IPT)
6. Validate with herbarium curators

## References

- ABCD Standard: https://abcd.tdwg.org
- GitHub Repository: https://github.com/tdwg/abcd
- Darwin Core: https://dwc.tdwg.org
- GBIF IPT: https://www.gbif.org/ipt

## Notes for Future Sessions

When user asks about "herbarium staff credit" or "who prepared specimens", this is where ABCD shines. The current Darwin Core extraction captures occurrence data well, but institutional workflow attribution requires ABCD's richer schema.

**Key insight from user**: "the abcd extension allows recording history and herbarium or clerical staff credit" - this is the primary motivation for ABCD support.
