# Workflow Examples: Real-World Herbarium Digitization Scenarios

This document provides detailed, step-by-step examples for common herbarium digitization scenarios, complete with sample data, configurations, and expected outcomes.

## Table of Contents

1. [Small University Herbarium](#small-university-herbarium)
2. [Large National Institution](#large-national-institution)
3. [Historical Collection with Multilingual Labels](#historical-collection-with-multilingual-labels)
4. [Type Specimen Digitization](#type-specimen-digitization)
5. [Citizen Science Collection](#citizen-science-collection)
6. [Emergency Digitization (Flood/Fire Recovery)](#emergency-digitization)

---

## Small University Herbarium

**Scenario**: Regional university with 5,000 specimens, mostly local flora, limited budget, student workers.

**Goals**:
- Process 200-500 specimens per month
- Minimize costs (avoid paid APIs when possible)
- Train students on botanical data standards
- Publish to GBIF within 6 months

### Setup and Configuration

**Equipment needed**:
- Standard DSLR or smartphone camera
- Copy stand or light box
- Computer with 8GB+ RAM

**Software setup**:
```bash
# Install with free engines only
./bootstrap.sh
uv add ".[tesseract,apple-vision]"  # Skip GPT to avoid costs

# Create institutional configuration
cp config/config.default.toml config/university.toml
```

**Configuration** (`config/university.toml`):
```toml
[ocr]
preferred_engine = "tesseract"
enabled_engines = ["tesseract", "vision"]  # vision only on macOS
confidence_threshold = 0.6  # Lower threshold due to handwritten labels
langs = ["en"]

[preprocess]
pipeline = ["grayscale", "contrast", "deskew", "binarize"]
contrast_factor = 1.3  # Enhance faded labels
max_dim_px = 2000     # Balance quality vs processing time

[dwc]
assume_country_if_missing = "United States"
strict_minimal_fields = false  # Allow incomplete records for training

[qc]
manual_review_threshold = 0.5  # Flag low confidence for student review
phash_threshold = 0.9         # Detect duplicate images
```

### Sample Processing Workflow

**Day 1: Setup and Testing**
```bash
# Create project structure
mkdir -p ./projects/university-herbarium/{input,output,review}

# Test with 10 sample specimens
python cli.py process \
  --input ./projects/university-herbarium/input/test-batch \
  --output ./projects/university-herbarium/output/test \
  --config config/university.toml \
  --engine tesseract \
  --engine vision

# Review results
python review_web.py \
  --db ./projects/university-herbarium/output/test/candidates.db \
  --images ./projects/university-herbarium/input/test-batch \
  --port 8080
```

**Weekly Processing Routine**:
```bash
# 1. Process new batch (50-100 specimens)
python cli.py process \
  --input ./projects/university-herbarium/input/week-$(date +%U) \
  --output ./projects/university-herbarium/output/week-$(date +%U) \
  --config config/university.toml

# 2. Generate QC report for student review
python qc/quality_report.py \
  --db ./projects/university-herbarium/output/week-$(date +%U)/app.db \
  --output ./review/week-$(date +%U)-review.xlsx \
  --filter "confidence < 0.7"

# 3. Students review flagged records
# (Manual step using Excel or web interface)

# 4. Import corrections
python import_review.py \
  --db ./projects/university-herbarium/output/week-$(date +%U)/app.db \
  --input ./review/week-$(date +%U)-corrected.xlsx
```

**Monthly Export for GBIF**:
```bash
# Combine all processed weeks
python cli.py merge \
  --inputs ./projects/university-herbarium/output/week-* \
  --output ./projects/university-herbarium/monthly/$(date +%Y-%m)

# Create Darwin Core Archive
python cli.py archive \
  --output ./projects/university-herbarium/monthly/$(date +%Y-%m) \
  --version $(date +%Y.%m.0) \
  --filter "confidence > 0.6 AND gbif_validated = true"
```

**Expected Results**:
- **Processing time**: 2-5 minutes per specimen
- **Accuracy**: 70-85% for typed labels, 50-70% for handwritten
- **Monthly output**: 200-400 validated records
- **Cost**: ~$0 (using free engines only)

---

## Large National Institution

**Scenario**: National museum with 500,000+ specimens, professional staff, digitization mandate.

**Goals**:
- Process 10,000+ specimens per month
- Achieve >90% accuracy
- Maintain detailed audit trails
- Support multiple simultaneous projects

### Setup and Configuration

**Infrastructure**:
- High-performance imaging station
- Server cluster with 64GB+ RAM per node
- Network storage for images and databases
- API budget for GPT-4 Vision

**Configuration** (`config/national-institution.toml`):
```toml
[ocr]
preferred_engine = "gpt"
enabled_engines = ["gpt", "tesseract", "vision", "paddleocr"]
confidence_threshold = 0.8
langs = ["en", "fr", "de", "la", "es"]  # Multilingual collection

[gpt]
model = "gpt-4-vision-preview"
dry_run = false
rate_limit_delay = 1.0
batch_size = 20
fallback_threshold = 0.7

[preprocess]
pipeline = ["grayscale", "deskew", "binarize", "resize"]
max_dim_px = 4000  # High resolution for maximum accuracy

[dwc]
strict_minimal_fields = true
assume_country_if_missing = ""  # Don't assume - flag for review

[qc]
manual_review_threshold = 0.8  # High standards
enable_gbif_validation = true
enable_coordinate_validation = true
duplicate_detection = true

[database]
use_postgresql = true  # Scale beyond SQLite
connection_string = "postgresql://user:pass@db-server/herbarium"
```

### Production Workflow

**Batch Processing Pipeline**:
```bash
#!/bin/bash
# production_pipeline.sh

PROJECT_NAME=$1
BATCH_SIZE=${2:-1000}
INPUT_DIR="/storage/imaging/${PROJECT_NAME}"
OUTPUT_DIR="/storage/processing/${PROJECT_NAME}"

# 1. Validate image quality before processing
python scripts/validate_images.py \
  --input "${INPUT_DIR}" \
  --min-resolution 300 \
  --check-integrity \
  --output "${OUTPUT_DIR}/validation.json"

# 2. Process in parallel batches
python scripts/parallel_process.py \
  --input "${INPUT_DIR}" \
  --output "${OUTPUT_DIR}" \
  --config config/national-institution.toml \
  --batch-size ${BATCH_SIZE} \
  --workers 8 \
  --engine gpt \
  --engine tesseract

# 3. Automated QC
python qc/comprehensive_qc.py \
  --db "${OUTPUT_DIR}/app.db" \
  --output "${OUTPUT_DIR}/qc_report.html" \
  --enable-all-checks

# 4. Generate review packages for curators
python export_review.py \
  --db "${OUTPUT_DIR}/app.db" \
  --filter "confidence < 0.8 OR gbif_match = false OR coordinate_issues = true" \
  --format xlsx \
  --output "${OUTPUT_DIR}/curator_review.xlsx"

# 5. Send notification
python scripts/notify_completion.py \
  --project "${PROJECT_NAME}" \
  --stats "${OUTPUT_DIR}/processing_stats.json"
```

**Curator Review Workflow**:
```bash
# High-throughput review interface
python review_web.py \
  --db ./storage/processing/bryophytes-2024/candidates.db \
  --images ./storage/imaging/bryophytes-2024 \
  --port 8080 \
  --expert-mode \
  --batch-review \
  --auto-save-interval 30

# Batch approval of high-confidence records
python scripts/batch_approve.py \
  --db ./storage/processing/bryophytes-2024/app.db \
  --filter "confidence > 0.9 AND gbif_match = true" \
  --curator "Dr. Smith" \
  --approve-all
```

**Weekly Exports**:
```bash
# Create publication-ready datasets
python cli.py archive \
  --output ./storage/processing/bryophytes-2024 \
  --version 2024.$(date +%W).0 \
  --filter "curator_approved = true" \
  --include-multimedia \
  --gbif-validate \
  --sign-manifest

# Automatic GBIF upload via IPT API
python scripts/upload_to_ipt.py \
  --dataset ./storage/processing/bryophytes-2024/dwca_v2024.$(date +%W).0.zip \
  --ipt-endpoint "https://ipt.museum.org" \
  --resource-id "bryophytes-2024"
```

**Expected Results**:
- **Processing time**: 30-60 seconds per specimen
- **Accuracy**: 90-95% for most labels
- **Monthly output**: 8,000-12,000 validated records
- **Cost**: $0.02-0.05 per specimen (GPT API costs)

---

## Historical Collection with Multilingual Labels

**Scenario**: European herbarium with 19th-century specimens, labels in German, French, Latin.

**Goals**:
- Preserve historical collecting information
- Handle faded, damaged labels
- Maintain original language while providing translations
- Capture determiner histories

### Specialized Configuration

**Configuration** (`config/historical-multilingual.toml`):
```toml
[ocr]
preferred_engine = "paddleocr"  # Best multilingual support
enabled_engines = ["paddleocr", "gpt", "tesseract"]
langs = ["de", "fr", "la", "en"]
confidence_threshold = 0.5  # Lower due to historical labels

[paddleocr]
lang = "latin"  # Covers most European scripts
use_gpu = true

[preprocess]
pipeline = ["grayscale", "contrast", "deskew", "binarize", "denoise"]
contrast_factor = 2.0  # Aggressive enhancement for faded text
binarize_method = "adaptive"

[dwc]
preserve_original_language = true
include_translations = true
verbatim_fields = ["verbatimLocality", "verbatimCollector", "verbatimIdentification"]

[historical]
# Custom section for historical data
parse_historical_dates = true
geocode_historical_localities = true
preserve_determiner_history = true
```

### Processing Workflow

**Preprocessing for Historical Images**:
```bash
# Enhanced preprocessing for damaged labels
python scripts/enhance_historical.py \
  --input ./input/historical-german \
  --output ./input/historical-german-enhanced \
  --operations "unsharp_mask,noise_reduction,contrast_stretch"

# Process with multiple engines for comparison
python cli.py process \
  --input ./input/historical-german-enhanced \
  --output ./output/historical-german \
  --config config/historical-multilingual.toml \
  --engine paddleocr \
  --engine gpt \
  --save-intermediates
```

**Language-Specific Processing**:
```bash
# Process German labels
python cli.py process \
  --input ./input/german-labels \
  --output ./output/german \
  --config config/historical-multilingual.toml \
  --language-hint "de" \
  --engine paddleocr

# Process French labels
python cli.py process \
  --input ./input/french-labels \
  --output ./output/french \
  --config config/historical-multilingual.toml \
  --language-hint "fr" \
  --engine paddleocr

# Process Latin labels
python cli.py process \
  --input ./input/latin-labels \
  --output ./output/latin \
  --config config/historical-multilingual.toml \
  --language-hint "la" \
  --engine gpt  # GPT better for Latin scientific names
```

**Historical Data Enhancement**:
```bash
# Geocode historical locality names
python scripts/geocode_historical.py \
  --db ./output/historical-german/app.db \
  --gazetteer "geonames,historical" \
  --language "de" \
  --country "Germany"

# Parse and normalize historical dates
python scripts/parse_historical_dates.py \
  --db ./output/historical-german/app.db \
  --language "de" \
  --date-formats "dd.mm.yyyy,dd/mm/yyyy,dd-mm-yyyy"

# Extract determiner information
python scripts/extract_determiners.py \
  --db ./output/historical-german/app.db \
  --language "de" \
  --pattern-file "config/patterns/german_determiners.txt"
```

**Sample Configuration for Historical Patterns**:

Create `config/patterns/german_determiners.txt`:
```
# German determiner patterns
det\.|det\s+[A-Z]
bestimmt\s+von
rev\.|rev\s+[A-Z]
revidiert\s+von
conf\.|conf\s+[A-Z]
```

**Expected Results**:
- **Processing time**: 2-8 minutes per specimen (complex labels)
- **Accuracy**: 60-80% (varies with label condition)
- **Language detection**: 85-95% accuracy
- **Historical data extraction**: 70-85% success rate

---

## Type Specimen Digitization

**Scenario**: Processing nomenclatural type specimens requiring highest accuracy and detailed metadata.

**Goals**:
- Achieve maximum possible accuracy
- Capture complete nomenclatural information
- Link to original publications
- Ensure Global Type Registry compliance

### High-Precision Configuration

**Configuration** (`config/type-specimens.toml`):
```toml
[ocr]
preferred_engine = "gpt"
enabled_engines = ["gpt", "vision", "tesseract"]
confidence_threshold = 0.9  # Very high threshold
enable_consensus_voting = true  # Use multiple engines

[gpt]
model = "gpt-4-vision-preview"
temperature = 0.1  # Minimize randomness
max_tokens = 2048
custom_instructions = "This is a nomenclatural type specimen. Extract all taxonomic, locality, and publication information with extreme precision."

[type_specimens]
# Custom section for type specimens
extract_type_status = true
extract_publication_details = true
validate_nomenclature = true
cross_reference_protologue = true

[qc]
manual_review_threshold = 1.0  # Review everything
enable_expert_validation = true
require_dual_review = true
```

### Type Specimen Workflow

**Preparation**:
```bash
# Create dedicated type specimen directory
mkdir -p ./projects/types/{input,output,review,publication}

# High-resolution imaging checklist
python scripts/validate_type_images.py \
  --input ./projects/types/input \
  --min-resolution 600 \
  --require-label-detail \
  --require-specimen-detail \
  --output ./projects/types/image_validation.json
```

**Processing with Maximum Precision**:
```bash
# Process with consensus from multiple engines
python cli.py process \
  --input ./projects/types/input \
  --output ./projects/types/output \
  --config config/type-specimens.toml \
  --engine gpt \
  --engine vision \
  --engine tesseract \
  --consensus-threshold 2  # Require agreement from 2+ engines
  --save-all-results
```

**Nomenclatural Validation**:
```bash
# Validate type information against databases
python scripts/validate_types.py \
  --db ./projects/types/output/app.db \
  --check-ipni \
  --check-tropicos \
  --check-indexfungorum \
  --output ./projects/types/nomenclature_validation.json

# Cross-reference with original publications
python scripts/protologue_matching.py \
  --db ./projects/types/output/app.db \
  --biodiversity-heritage-library \
  --output ./projects/types/publication_links.json
```

**Expert Review Process**:
```bash
# Generate expert review packages
python export_review.py \
  --db ./projects/types/output/app.db \
  --format expert_review \
  --include-images \
  --include-literature \
  --output ./projects/types/review/expert_package.zip

# Track review status
python scripts/review_tracker.py \
  --db ./projects/types/output/app.db \
  --reviewers "Dr.Smith,Dr.Jones,Dr.Brown" \
  --require-majority-agreement
```

**Publication to Type Registries**:
```bash
# Format for Global Plants
python export_review.py \
  --db ./projects/types/output/app.db \
  --format global_plants \
  --filter "review_status = 'approved'" \
  --output ./projects/types/publication/global_plants.xml

# Format for GBIF
python cli.py archive \
  --output ./projects/types/output \
  --version 1.0.0 \
  --filter "review_status = 'approved'" \
  --type-specimens-only \
  --include-nomenclature
```

**Expected Results**:
- **Processing time**: 10-30 minutes per specimen
- **Accuracy**: 95-99% (with expert review)
- **Nomenclatural validation**: 90-95% automatically verified
- **Cost**: $0.10-0.25 per specimen (high-quality GPT usage)

---

## Citizen Science Collection

**Scenario**: Community-contributed specimens with variable image quality and documentation.

**Goals**:
- Process diverse image qualities
- Provide feedback to contributors
- Maintain data quality standards
- Engage citizen scientists in validation

### Flexible Configuration

**Configuration** (`config/citizen-science.toml`):
```toml
[ocr]
preferred_engine = "tesseract"
enabled_engines = ["tesseract", "paddleocr", "gpt"]
confidence_threshold = 0.6
adaptive_thresholding = true  # Adjust based on image quality

[citizen_science]
# Custom section for citizen science
enable_contributor_feedback = true
auto_flag_unusual_records = true
provide_educational_hints = true

[preprocess]
pipeline = ["auto_orient", "grayscale", "adaptive_contrast", "deskew", "binarize"]
# Adaptive preprocessing based on image analysis

[qc]
flag_geographic_outliers = true
flag_temporal_outliers = true
flag_taxonomic_outliers = true
community_validation = true
```

### Community Processing Workflow

**Image Quality Triage**:
```bash
# Automatically sort images by quality
python scripts/triage_images.py \
  --input ./input/community-submissions \
  --output-high ./input/high-quality \
  --output-medium ./input/medium-quality \
  --output-low ./input/needs-improvement \
  --criteria "resolution,blur,lighting,label_visibility"

# Provide feedback to contributors
python scripts/contributor_feedback.py \
  --input ./input/needs-improvement \
  --template "templates/improvement_suggestions.txt" \
  --output ./feedback/improvement_needed.json
```

**Adaptive Processing**:
```bash
# Process high-quality images with standard pipeline
python cli.py process \
  --input ./input/high-quality \
  --output ./output/high-quality \
  --config config/citizen-science.toml \
  --engine tesseract

# Process medium-quality with enhanced preprocessing
python cli.py process \
  --input ./input/medium-quality \
  --output ./output/medium-quality \
  --config config/citizen-science.toml \
  --engine tesseract \
  --engine paddleocr \
  --preprocess-intensive

# Process challenging images with GPT
python cli.py process \
  --input ./input/challenging \
  --output ./output/challenging \
  --config config/citizen-science.toml \
  --engine gpt \
  --manual-review-all
```

**Community Validation**:
```bash
# Create community validation interface
python review_web.py \
  --db ./output/community-records/candidates.db \
  --images ./input/community-submissions \
  --community-mode \
  --gamification \
  --reputation-system

# Educational feedback generation
python scripts/educational_feedback.py \
  --db ./output/community-records/app.db \
  --generate-hints \
  --taxonomy-lessons \
  --geography-lessons
```

**Quality Control and Outlier Detection**:
```bash
# Flag unusual records for expert review
python qc/outlier_detection.py \
  --db ./output/community-records/app.db \
  --geographic-outliers \
  --temporal-outliers \
  --taxonomic-outliers \
  --output ./review/outliers.json

# Expert validation of flagged records
python review_web.py \
  --db ./output/community-records/candidates.db \
  --filter "flagged = true" \
  --expert-mode
```

**Expected Results**:
- **Processing time**: 1-10 minutes per specimen (varies by quality)
- **Accuracy**: 50-90% (highly variable)
- **Community engagement**: 70-80% contributor participation in validation
- **Data quality improvement**: 60-80% of flagged records corrected

---

## Emergency Digitization (Flood/Fire Recovery)

**Scenario**: Rapid digitization of damaged specimens following natural disaster.

**Goals**:
- Process specimens before further deterioration
- Extract maximum information from damaged labels
- Prioritize unique/irreplaceable specimens
- Create digital backup of collection

### Emergency Response Configuration

**Configuration** (`config/emergency-response.toml`):
```toml
[ocr]
preferred_engine = "gpt"  # Best for damaged text
enabled_engines = ["gpt", "vision", "tesseract"]
confidence_threshold = 0.3  # Accept lower quality due to damage
emergency_mode = true

[preprocess]
pipeline = ["stabilize", "contrast_extreme", "denoise_aggressive", "binarize_adaptive"]
# Aggressive image enhancement for damaged specimens

[emergency]
# Custom section for emergency processing
prioritize_types = true
prioritize_rare_species = true
capture_damage_assessment = true
rapid_processing_mode = true

[qc]
damage_documentation = true
priority_specimen_tracking = true
minimal_validation = true  # Speed over perfection
```

### Emergency Processing Workflow

**Rapid Triage and Prioritization**:
```bash
# Quick assessment of specimen condition
python scripts/emergency_triage.py \
  --input ./emergency/damaged-specimens \
  --output ./emergency/triage \
  --priority-list ./config/priority_taxa.txt \
  --damage-assessment

# Separate by priority level
# Priority 1: Types, rare species, unique localities
# Priority 2: Regional flora, common species
# Priority 3: Recent collections, duplicates
```

**High-Speed Processing**:
```bash
# Process priority specimens first
for priority in 1 2 3; do
  python cli.py process \
    --input "./emergency/triage/priority-${priority}" \
    --output "./emergency/output/priority-${priority}" \
    --config config/emergency-response.toml \
    --engine gpt \
    --rapid-mode \
    --save-all-attempts
done

# Parallel processing across multiple machines
python scripts/distributed_emergency.py \
  --input ./emergency/triage \
  --workers "server1,server2,server3" \
  --config config/emergency-response.toml
```

**Damage Documentation**:
```bash
# Document damage while processing
python scripts/damage_assessment.py \
  --input ./emergency/damaged-specimens \
  --output ./emergency/damage_report.json \
  --categories "water,fire,mold,insect,physical"

# Generate conservation priority list
python scripts/conservation_priority.py \
  --damage-report ./emergency/damage_report.json \
  --specimen-db ./emergency/output/*/app.db \
  --output ./emergency/conservation_priorities.xlsx
```

**Rapid Export and Backup**:
```bash
# Create immediate backup exports
python cli.py archive \
  --output ./emergency/output/priority-1 \
  --version emergency-$(date +%Y%m%d) \
  --rapid-export \
  --include-damage-notes

# Upload to multiple cloud storage locations
python scripts/emergency_backup.py \
  --archives ./emergency/output/*/dwca_emergency-*.zip \
  --destinations "aws-s3,google-drive,institutional-backup" \
  --verify-integrity
```

**Real-time Progress Tracking**:
```bash
# Monitor processing progress
python scripts/emergency_dashboard.py \
  --databases ./emergency/output/*/app.db \
  --port 8080 \
  --auto-refresh 30

# Generate status reports
python scripts/emergency_report.py \
  --databases ./emergency/output/*/app.db \
  --output ./emergency/status_report_$(date +%Y%m%d_%H%M).html \
  --email-stakeholders
```

**Expected Results**:
- **Processing time**: 30 seconds - 5 minutes per specimen
- **Accuracy**: 30-80% (varies with damage severity)
- **Recovery rate**: 70-90% of specimens processed within 48 hours
- **Data preservation**: 60-85% of original information captured

---

## Workflow Comparison Summary

| Scenario | Processing Speed | Accuracy Target | Cost per Specimen | Primary Challenges |
|----------|------------------|-----------------|-------------------|-------------------|
| Small University | 2-5 min | 70-85% | $0 | Budget constraints, training |
| National Institution | 0.5-1 min | 90-95% | $0.02-0.05 | Scale, audit trails |
| Historical Multilingual | 2-8 min | 60-80% | $0.01-0.03 | Language barriers, faded text |
| Type Specimens | 10-30 min | 95-99% | $0.10-0.25 | Absolute precision required |
| Citizen Science | 1-10 min | 50-90% | $0-0.02 | Variable quality, education |
| Emergency Response | 0.5-5 min | 30-80% | $0.05-0.15 | Time pressure, damage |

Each workflow can be adapted based on specific institutional needs, available resources, and collection characteristics.
