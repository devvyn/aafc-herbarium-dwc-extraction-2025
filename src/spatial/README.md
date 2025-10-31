# Spatial Zone Detection Module (Deferred to v2.1+)

**Status**: Implemented but not integrated
**Date Created**: 2025-10-28
**Reason for Deferral**: Review UI stabilization takes priority

## Purpose

Spatial zone detection enables location-aware field extraction by mapping text regions to zones on herbarium specimen labels.

## Use Case

Herbarium specimens often have multiple labels with different information:
- **TOP label**: Collector info, date, location
- **BOTTOM label**: Taxonomic identification, determiner

Without spatial awareness, OCR may confuse which text belongs to which semantic field. For example, "Identified by: Dr. Smith" might be incorrectly extracted as the collector name instead of the determiner.

## Implementation Status

### Completed

1. **zone_detector.py** (7.3KB)
   - Text region bounding box analysis
   - 9-zone grid template creation
   - Zone statistics calculation

2. **zone_loader.py** (5.1KB)
   - Template cache system
   - JSONL format loading
   - Zone lookup by specimen

3. **image_annotator.py** (5.3KB)
   - Visualization overlay rendering
   - Zone boundary drawing
   - Debug visualization for development

### Not Completed

1. **Integration with extraction pipeline**
   - No engine uses zone information yet
   - Extraction methods don't filter by zone

2. **Template generation**
   - `scripts/analyze_spatial_zones.py` exists but not run
   - No `spatial_zones.jsonl` template file generated

3. **Validation**
   - No unit tests
   - No validation that zones improve accuracy
   - Unknown if 9-zone grid is optimal

## Why Deferred

### Priority 1: Stable Review Interface

The Quart review interface is working and needs to remain stable for AAFC delivery. Adding spatial zone complexity risks introducing bugs without proven accuracy benefit.

### Uncertain Value

- **No baseline**: Don't know current field extraction accuracy
- **No A/B test**: Can't measure if zones improve results
- **Complexity cost**: Adds significant extraction pipeline complexity

### NiceGUI Dependency

Spatial zones were developed for the NiceGUI interface to show zone overlays during review. Since NiceGUI is also deferred (filter bug), the visualization use case is blocked.

## Future Integration Plan

### v2.1.0: Validation Phase

1. **Generate templates**: Run `analyze_spatial_zones.py` on sample dataset
2. **Measure baseline**: Extract without zones, measure field accuracy
3. **Implement zone-aware extraction**: Modify one engine to use zones
4. **Measure improvement**: Compare accuracy with/without zones
5. **Decision**: Keep if >5% accuracy gain, otherwise remove

### v2.2.0: Production (if validated)

1. **Integrate all engines**: Add zone filtering to all extraction methods
2. **Update review UI**: Show zone overlays in Quart interface
3. **Document methodology**: Add zone detection to architecture docs

## Related Files

- `scripts/analyze_spatial_zones.py` - Template generation (untracked)
- `deliverables/v1.0_vision_baseline/image_rotations.json` - Rotation cache (untracked)
- `archive/experimental/nicegui-review-ui/` - Original visualization target

## Technical Details

### 9-Zone Grid

```
┌─────┬─────┬─────┐
│ TL  │  T  │ TR  │  (Top, Top-Left, Top-Right)
├─────┼─────┼─────┤
│  L  │  C  │  R  │  (Left, Center, Right)
├─────┼─────┼─────┤
│ BL  │  B  │ BR  │  (Bottom, Bottom-Left, Bottom-Right)
└─────┴─────┴─────┘
```

### Zone-Aware Extraction Example

```python
from spatial.zone_detector import load_zones

zones = load_zones("spatial_zones.jsonl")
specimen_zones = zones["abc123"]

# Filter OCR results by zone
collector_texts = [
    text for text, bbox in ocr_results
    if bbox_in_zone(bbox, specimen_zones["T"])  # Top zone
]

determiner_texts = [
    text for text, bbox in ocr_results
    if bbox_in_zone(bbox, specimen_zones["B"])  # Bottom zone
]
```

---

*Module kept in source tree to preserve implementation. Not included in any production workflows until validation demonstrates value.*
