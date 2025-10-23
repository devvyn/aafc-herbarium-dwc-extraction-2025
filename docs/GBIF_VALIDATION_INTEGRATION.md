# GBIF Validation Integration (v2.1.0 Planned)

## Overview

GBIF (Global Biodiversity Information Facility) validation provides scientific verification of taxonomic names, geographic coordinates, and occurrence patterns. Integrating GBIF validation into the v2.0.0 specimen provenance system creates a production-ready data quality pipeline.

**Timeline**: November 1-28, 2025 (4-week milestone)

## Current State

### Already Implemented ✅

**GBIF Integration** (`qc/gbif.py`, `src/review/validators.py`):
- Taxonomy verification (scientificName, family, genus matching)
- Locality verification (coordinate validation, distance calculations)
- Occurrence validation (check against known GBIF records)
- Confidence scoring (0-100 scale)
- LRU caching for performance
- Retry logic with exponential backoff
- Async support for non-blocking operations
- Autocomplete suggestions

### Missing Integration ❌

- GBIF validation not stored in specimen index
- No automatic pre-validation during extraction aggregation
- Review UI doesn't show GBIF status
- No quality flags for GBIF validation failures

## Proposed Architecture: Two-Tier Validation

### Tier 1: Automatic Pre-Validation

**When**: During specimen aggregation (before human review)

**Purpose**: Auto-validate high-confidence extractions, flag problems for review

**Implementation**:
```python
# In src/provenance/specimen_index.py

def aggregate_specimen_extractions(self, specimen_id: str) -> Dict[str, Any]:
    """
    Aggregate multiple extraction results for a specimen.
    NOW WITH AUTOMATIC GBIF PRE-VALIDATION.
    """
    # ... existing aggregation logic ...

    # NEW: Automatic GBIF pre-validation
    gbif_validation = self._auto_validate_gbif(best_candidates)

    # Save aggregation WITH validation
    with self.conn:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO specimen_aggregations
            (specimen_id, candidate_fields_json, best_candidates_json,
             gbif_validation_json, review_status, queued_for_review_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                specimen_id,
                json.dumps(candidate_fields),
                json.dumps(best_candidates),
                json.dumps(gbif_validation),  # NEW
                "pending",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    return {
        "candidate_fields": candidate_fields,
        "best_candidates": best_candidates,
        "gbif_validation": gbif_validation,  # NEW
    }


def _auto_validate_gbif(
    self, candidates: Dict[str, Any], confidence_threshold: float = 0.9
) -> Dict[str, Any]:
    """
    Automatic GBIF pre-validation for high-confidence extractions.

    Args:
        candidates: Best candidate values per field
        confidence_threshold: Only validate if confidence >= threshold

    Returns:
        GBIF validation results and flags
    """
    from qc.gbif import GbifLookup

    gbif = GbifLookup(
        min_confidence_score=0.80,
        enable_fuzzy_matching=True,
        enable_occurrence_validation=False,  # Too slow for batch
    )

    validation = {
        "auto_validated": False,
        "taxonomy": None,
        "locality": None,
        "issues": [],
        "requires_review": False,
    }

    # Only auto-validate high-confidence extractions
    scientific_name_confidence = candidates.get("scientificName", {}).get("confidence", 0)
    if scientific_name_confidence < confidence_threshold:
        validation["issues"].append("low_confidence_scientific_name")
        validation["requires_review"] = True
        return validation

    # Build record for GBIF validation
    record = {
        field: candidates.get(field, {}).get("value")
        for field in [
            "scientificName",
            "family",
            "genus",
            "specificEpithet",
            "decimalLatitude",
            "decimalLongitude",
        ]
        if candidates.get(field, {}).get("value")
    }

    # Taxonomy validation
    if record.get("scientificName"):
        try:
            updated_record, taxonomy_metadata = gbif.verify_taxonomy(record)
            validation["taxonomy"] = taxonomy_metadata

            # Flag validation failures
            if not taxonomy_metadata["gbif_taxonomy_verified"]:
                validation["issues"].append("taxonomy_not_verified")
                validation["requires_review"] = True

            if taxonomy_metadata["gbif_confidence"] < 80:
                validation["issues"].append(
                    f"low_gbif_confidence_{taxonomy_metadata['gbif_confidence']}"
                )
                validation["requires_review"] = True

        except Exception as e:
            validation["issues"].append(f"taxonomy_validation_error: {e}")
            validation["requires_review"] = True

    # Locality validation (if coordinates present)
    if record.get("decimalLatitude") and record.get("decimalLongitude"):
        try:
            updated_record, locality_metadata = gbif.verify_locality(record)
            validation["locality"] = locality_metadata

            # Flag coordinate issues
            if not locality_metadata["gbif_coordinate_valid"]:
                validation["issues"].append("invalid_coordinates")
                validation["requires_review"] = True

            distance_km = locality_metadata.get("gbif_distance_km")
            if distance_km and distance_km > 10.0:
                validation["issues"].append(f"coordinate_discrepancy_{distance_km:.1f}km")
                validation["requires_review"] = True

        except Exception as e:
            validation["issues"].append(f"locality_validation_error: {e}")
            validation["requires_review"] = True

    # Mark as successfully validated if no issues
    if not validation["issues"]:
        validation["auto_validated"] = True

    return validation
```

**Database Schema Update**:
```sql
-- Add GBIF validation column to specimen_aggregations table
ALTER TABLE specimen_aggregations
ADD COLUMN gbif_validation_json TEXT;

-- Add GBIF validation index
CREATE INDEX IF NOT EXISTS idx_gbif_validated
ON specimen_aggregations(
    json_extract(gbif_validation_json, '$.auto_validated')
);

-- Add GBIF validation flags to data_quality_flags
-- (New flag types)
INSERT INTO data_quality_flags (specimen_id, flag_type, severity, message)
SELECT
    specimen_id,
    'GBIF_TAXONOMY_UNVERIFIED',
    'warning',
    'Taxonomic name could not be verified against GBIF'
FROM specimen_aggregations
WHERE json_extract(gbif_validation_json, '$.taxonomy.gbif_taxonomy_verified') = false;
```

### Tier 2: Interactive Human Validation

**When**: During human review of flagged specimens

**Purpose**: Manual verification and correction with GBIF assistance

**Review UI Implementation**:

```javascript
// In review UI: src/review/templates/review.html

<div class="gbif-validation-panel">
  <h3>GBIF Validation Status</h3>

  <!-- Auto-validation results -->
  <div class="auto-validation">
    <span class="badge {{ 'success' if gbif.auto_validated else 'warning' }}">
      {{ 'Auto-Validated' if gbif.auto_validated else 'Requires Review' }}
    </span>
  </div>

  <!-- Taxonomy validation -->
  <div class="taxonomy-validation">
    <h4>Taxonomic Name</h4>
    <input type="text"
           id="scientific-name"
           value="{{ best_candidates.scientificName.value }}"
           data-gbif-autocomplete>

    <div class="validation-result">
      <span class="match-type">{{ gbif.taxonomy.gbif_match_type }}</span>
      <span class="confidence">{{ gbif.taxonomy.gbif_confidence }}%</span>
    </div>

    <!-- GBIF suggestions (autocomplete) -->
    <div id="gbif-suggestions" class="suggestions-dropdown">
      <!-- Populated dynamically via /api/gbif/suggest -->
    </div>

    <!-- Manual re-validation button -->
    <button onclick="revalidateGBIF()">
      Validate with GBIF
    </button>
  </div>

  <!-- Locality validation -->
  <div class="locality-validation">
    <h4>Geographic Coordinates</h4>
    <div class="coordinates">
      <input type="text" id="lat" value="{{ best_candidates.decimalLatitude.value }}">
      <input type="text" id="lng" value="{{ best_candidates.decimalLongitude.value }}">
    </div>

    <div class="validation-result">
      <span class="valid">
        {{ 'Valid' if gbif.locality.gbif_coordinate_valid else 'Invalid' }}
      </span>
      {% if gbif.locality.gbif_distance_km %}
      <span class="distance">
        Distance from GBIF: {{ gbif.locality.gbif_distance_km }}km
      </span>
      {% endif %}
    </div>
  </div>

  <!-- Validation issues -->
  {% if gbif.issues %}
  <div class="validation-issues">
    <h4>Issues Detected</h4>
    <ul>
      {% for issue in gbif.issues %}
      <li class="issue-{{ issue.split('_')[0] }}">{{ issue }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}
</div>
```

**Review API Endpoints**:
```python
# In src/review/web_app.py

@app.route("/api/specimen/<specimen_id>/gbif/validate", methods=["POST"])
async def validate_specimen_gbif(specimen_id: str):
    """
    Manual GBIF validation triggered by reviewer.

    Runs full validation including:
    - Taxonomy verification
    - Locality verification
    - Occurrence validation (optional, slower)
    """
    data = await request.get_json()

    # Get validator
    validator = create_gbif_validator()

    # Build record from submitted data
    record = {
        "scientificName": data.get("scientificName"),
        "family": data.get("family"),
        "genus": data.get("genus"),
        "decimalLatitude": data.get("decimalLatitude"),
        "decimalLongitude": data.get("decimalLongitude"),
    }

    # Run validation
    taxonomy_result = await validator.verify_taxonomy(record)
    locality_result = await validator.verify_locality(record)

    # Optionally run occurrence validation (slower)
    occurrence_result = None
    if data.get("check_occurrences"):
        occurrence_result = await validator.validate_occurrence(record)

    # Store validation results in specimen index
    specimen_index.update_gbif_validation(
        specimen_id=specimen_id,
        validation={
            "taxonomy": taxonomy_result[1],
            "locality": locality_result[1],
            "occurrence": occurrence_result[1] if occurrence_result else None,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validated_by": data.get("reviewer_email"),
        },
    )

    return jsonify({
        "success": True,
        "taxonomy": taxonomy_result[1],
        "locality": locality_result[1],
        "occurrence": occurrence_result[1] if occurrence_result else None,
    })


@app.route("/api/gbif/suggest")
async def gbif_suggest():
    """
    GBIF taxonomic name autocomplete.

    Provides real-time suggestions as reviewer types.
    """
    partial_name = request.args.get("q", "")
    limit = int(request.args.get("limit", "10"))

    validator = create_gbif_validator()
    suggestions = await validator.get_suggestions(partial_name, limit)

    return jsonify(suggestions)
```

## Publication Tiers with GBIF Validation

### v2.1.0-draft: Pre-Validated Only
```
Specimens: All 2,885
GBIF Auto-Validated: ~1,800 (high-confidence, passed validation)
Requires Review: ~1,085 (low confidence or validation failed)

Published: All specimens with validation status
```

### v2.1.0-validated: Human-Reviewed GBIF
```
Specimens: Auto-validated + Human-verified
GBIF Validated: ~2,500 (auto + manual verification)
Rejected: ~385 (validation failed, unresolvable)

Published: Only GBIF-validated specimens
Quality: Publication-ready for GBIF submission
```

### v2.1.0: Final Release
```
Specimens: All approved after human review
GBIF Validated: 100%
Quality Flags: All resolved

Published: Production-ready Darwin Core Archive
Suitable for: GBIF, Canadensys, institutional repositories
```

## Efficiency Benefits

### Pre-Validation Reduces Manual Work

**Without pre-validation**:
- Human reviews all 2,885 specimens
- Manual GBIF lookup for each
- ~15 minutes per specimen
- **Total: ~720 hours**

**With pre-validation**:
- Auto-validated: ~1,800 specimens (quick approval)
- Requires review: ~1,085 specimens (focus effort here)
- ~5 minutes per auto-validated specimen
- ~20 minutes per flagged specimen
- **Total: ~510 hours**

**Savings**: ~210 hours (29% reduction)

### High-Confidence Auto-Validation Criteria

```python
# Specimen auto-validates if:
extraction_confidence >= 0.9  # High confidence extraction
AND gbif_taxonomy_verified == True  # GBIF verified name
AND gbif_confidence >= 80  # High GBIF confidence
AND no_coordinate_issues  # Valid coordinates (if present)
AND no_catalog_duplicates  # Unique catalog number

# Result: ~62% of specimens auto-validate
```

## Data Quality Improvements

### Validation Metrics

```json
{
  "total_specimens": 2885,
  "gbif_validation": {
    "auto_validated": 1800,
    "manually_validated": 700,
    "validation_failed": 385,
    "validation_coverage": "86.7%"
  },
  "taxonomy_quality": {
    "exact_match": 2100,
    "fuzzy_match": 400,
    "higher_rank": 200,
    "no_match": 185
  },
  "locality_quality": {
    "coordinates_valid": 1500,
    "coordinates_flagged": 200,
    "no_coordinates": 1185
  }
}
```

### Quality Flags Integration

```sql
-- Examples of GBIF-related quality flags:

-- Taxonomy issues
GBIF_TAXONOMY_UNVERIFIED
GBIF_LOW_CONFIDENCE_<score>
GBIF_FUZZY_MATCH_ONLY
GBIF_NAME_NOT_FOUND

-- Locality issues
GBIF_INVALID_COORDINATES
GBIF_COORDINATE_DISCREPANCY_<km>
GBIF_COORDINATE_OUT_OF_RANGE

-- Occurrence issues (optional)
GBIF_NO_KNOWN_OCCURRENCES
GBIF_OCCURRENCE_MISMATCH
```

## Implementation Timeline (v2.1.0)

### Week 1: Database Schema & Pre-Validation (Nov 1-7)
- [ ] Add gbif_validation_json column to specimen_aggregations
- [ ] Implement _auto_validate_gbif() method
- [ ] Run pre-validation on all aggregated specimens
- [ ] Generate GBIF validation quality flags

### Week 2: Review UI Integration (Nov 8-14)
- [ ] Add GBIF validation panel to review UI
- [ ] Implement /api/gbif/suggest autocomplete endpoint
- [ ] Implement /api/specimen/<id>/gbif/validate endpoint
- [ ] Add GBIF status to specimen list view

### Week 3: Testing & Refinement (Nov 15-21)
- [ ] Test pre-validation accuracy on sample data
- [ ] Tune confidence thresholds
- [ ] Verify autocomplete performance
- [ ] Load testing on GBIF API calls

### Week 4: Publication (Nov 22-28)
- [ ] Export v2.1.0-draft (all specimens with GBIF status)
- [ ] Begin human review of flagged specimens
- [ ] Export v2.1.0-validated (GBIF-verified only)
- [ ] Final v2.1.0 release

## Success Criteria

### Technical
- [ ] GBIF validation stored in specimen index
- [ ] Pre-validation runs automatically during aggregation
- [ ] Review UI shows GBIF status
- [ ] Autocomplete provides real-time suggestions
- [ ] Manual validation updates specimen index

### Scientific
- [ ] >85% of specimens GBIF-validated
- [ ] Taxonomic names match GBIF backbone
- [ ] Geographic coordinates verified
- [ ] Quality flags comprehensive

### Operational
- [ ] Pre-validation reduces review time by >25%
- [ ] GBIF API calls cached effectively
- [ ] No rate limiting issues
- [ ] Publication-ready Darwin Core Archive

## Benefits Summary

### For Researchers
- Scientific rigor: All names verified against global authority
- Geographic accuracy: Coordinates validated
- Occurrence context: Known distribution patterns available
- Traceable: Full validation provenance recorded

### For Institutions
- Data quality: Publication-ready for GBIF/Canadensys
- Efficiency: Automated pre-validation reduces manual work
- Standards compliance: Meets international biodiversity data standards
- Auditability: Complete validation history preserved

### For Data Users
- Trustworthy: GBIF-validated increases confidence
- Interoperable: Standardized naming conventions
- Discoverable: Ready for global biodiversity platforms
- Citable: Full provenance supports scientific citation

## Related Documentation

- **GBIF Implementation**: `qc/gbif.py`, `src/review/validators.py`
- **Specimen Provenance**: [specimen_provenance_architecture.md](specimen_provenance_architecture.md)
- **Release Plan**: [RELEASE_2_0_PLAN.md](RELEASE_2_0_PLAN.md)
- **Review System**: `src/review/web_app.py`
