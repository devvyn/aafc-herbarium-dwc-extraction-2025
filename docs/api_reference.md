# API Reference

This document provides comprehensive API documentation for the herbarium OCR to Darwin Core toolkit, including programmatic interfaces for custom integrations and advanced workflows.

## Table of Contents

1. [Core Processing API](#core-processing-api)
2. [OCR Engine API](#ocr-engine-api)
3. [Database API](#database-api)
4. [Quality Control API](#quality-control-api)
5. [Export API](#export-api)
6. [Configuration API](#configuration-api)

---

## Core Processing API

### Processing Pipeline Functions

#### `process_specimen(image_path, config, engines=None)`

Process a single specimen image through the complete OCR and data extraction pipeline.

**Parameters**:
- `image_path` (Path): Path to specimen image file
- `config` (dict): Configuration parameters
- `engines` (list, optional): List of OCR engines to use

**Returns**:
- `ProcessingResult`: Object containing extracted data and metadata

**Example**:
```python
from pathlib import Path
from cli import process_specimen

config = {
    'ocr': {
        'preferred_engine': 'tesseract',
        'confidence_threshold': 0.7
    }
}

result = process_specimen(
    image_path=Path("specimen_001.jpg"),
    config=config,
    engines=['tesseract', 'vision']
)

print(f"Scientific name: {result.scientific_name}")
print(f"Confidence: {result.confidence}")
```

#### `batch_process(input_dir, output_dir, config, **kwargs)`

Process multiple specimens in batch mode with progress tracking.

**Parameters**:
- `input_dir` (Path): Directory containing specimen images
- `output_dir` (Path): Output directory for results
- `config` (dict): Configuration parameters
- `resume` (bool): Resume interrupted processing
- `parallel` (bool): Enable parallel processing

**Returns**:
- `BatchResult`: Summary statistics and processing status

**Example**:
```python
from cli import batch_process

result = batch_process(
    input_dir=Path("./specimens/"),
    output_dir=Path("./output/"),
    config=config,
    resume=True,
    parallel=True
)

print(f"Processed: {result.processed_count}")
print(f"Failed: {result.failed_count}")
```

---

## OCR Engine API

### Engine Registration

#### `register_engine(name, engine_class)`

Register a custom OCR engine with the processing pipeline.

**Parameters**:
- `name` (str): Unique engine identifier
- `engine_class` (class): Engine implementation class

**Example**:
```python
from engines import register_engine
from engines.protocols import ImageToTextEngine

class CustomOCREngine:
    def image_to_text(self, image_path, **kwargs):
        # Custom OCR implementation
        return extracted_text, confidence_scores

register_engine("custom_ocr", CustomOCREngine)
```

### Built-in Engines

#### Tesseract Engine

```python
from engines.tesseract import image_to_text

text, confidence = image_to_text(
    image=Path("specimen.jpg"),
    oem=1,  # LSTM neural net
    psm=6,  # Uniform block of text
    langs=["eng"]
)
```

#### GPT Vision Engine

```python
from engines.gpt.image_to_text import image_to_text

text, confidence = image_to_text(
    image=Path("specimen.jpg"),
    model="gpt-4-vision-preview",
    prompt_dir=Path("custom_prompts/"),
    langs=["en", "la"]
)
```

#### Apple Vision Engine (macOS only)

```python
from engines.vision_swift import image_to_text

text, confidence = image_to_text(
    image=Path("specimen.jpg"),
    language_preference=["en"]
)
```

#### PaddleOCR Engine

```python
from engines.paddleocr import image_to_text

text, confidence = image_to_text(
    image=Path("specimen.jpg"),
    lang="latin",
    use_gpu=True
)
```

---

## Database API

### Database Connection

#### `get_database_connection(output_dir)`

Get a connection to the processing database.

**Example**:
```python
from io_utils.database import get_database_connection

with get_database_connection("./output/") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM specimens WHERE confidence > 0.8")
    high_confidence_records = cursor.fetchall()
```

### Data Models

#### Specimen Record

```python
from io_utils.candidate_models import SpecimenRecord

specimen = SpecimenRecord(
    image_path="specimen_001.jpg",
    scientific_name="Quercus alba",
    collector="John Smith",
    collection_date="2023-05-15",
    locality="Ontario, Canada",
    confidence=0.85
)
```

#### OCR Candidate

```python
from io_utils.candidate_models import OCRCandidate

candidate = OCRCandidate(
    specimen_id="spec_001",
    engine_name="tesseract",
    raw_text="Quercus alba L.\nColl: John Smith\n15 May 2023",
    confidence=0.75,
    processing_time=2.3
)
```

### Database Queries

#### Common Query Functions

```python
from io_utils.database import query_specimens

# Get specimens by confidence threshold
high_confidence = query_specimens(
    db_path="./output/app.db",
    filter_sql="confidence > ?",
    params=[0.8]
)

# Get specimens needing review
needs_review = query_specimens(
    db_path="./output/app.db",
    filter_sql="gbif_match = 0 OR confidence < ?",
    params=[0.7]
)

# Get specimens by date range
recent_specimens = query_specimens(
    db_path="./output/app.db",
    filter_sql="collection_date >= ? AND collection_date <= ?",
    params=["2023-01-01", "2023-12-31"]
)
```

---

## Quality Control API

### Validation Functions

#### `validate_darwin_core(record)`

Validate a specimen record against Darwin Core standards.

**Example**:
```python
from qc.dwc_validation import validate_darwin_core

validation_result = validate_darwin_core(specimen_record)

if validation_result.is_valid:
    print("Record passes Darwin Core validation")
else:
    print(f"Validation errors: {validation_result.errors}")
```

#### `validate_coordinates(latitude, longitude)`

Validate geographic coordinates.

**Example**:
```python
from qc.geographic import validate_coordinates

is_valid, errors = validate_coordinates(
    latitude=45.4215,
    longitude=-75.6972
)

if not is_valid:
    print(f"Coordinate errors: {errors}")
```

#### `validate_taxonomy(scientific_name)`

Validate taxonomic names against GBIF backbone.

**Example**:
```python
from qc.gbif import validate_taxonomy

gbif_result = validate_taxonomy("Quercus alba")

print(f"GBIF match: {gbif_result.is_match}")
print(f"Accepted name: {gbif_result.accepted_name}")
print(f"Taxonomic status: {gbif_result.status}")
```

### Duplicate Detection

#### `detect_duplicates(db_path, threshold=0.9)`

Detect potential duplicate specimens using perceptual hashing.

**Example**:
```python
from qc.duplicates import detect_duplicates

duplicates = detect_duplicates(
    db_path="./output/app.db",
    threshold=0.95
)

for group in duplicates:
    print(f"Potential duplicates: {group.specimen_ids}")
    print(f"Similarity score: {group.similarity}")
```

---

## Export API

### Export Functions

#### `export_darwin_core(db_path, output_path, format="csv")`

Export processed specimens in Darwin Core format.

**Example**:
```python
from export_review import export_darwin_core

# Export to CSV
export_darwin_core(
    db_path="./output/app.db",
    output_path="./exports/occurrence.csv",
    format="csv",
    filter_sql="confidence > 0.7"
)

# Export to Excel with multiple sheets
export_darwin_core(
    db_path="./output/app.db",
    output_path="./exports/full_dataset.xlsx",
    format="excel",
    include_identification_history=True
)
```

#### `create_dwc_archive(output_dir, version, **kwargs)`

Create a Darwin Core Archive (DwC-A) bundle.

**Example**:
```python
from dwc.archive import create_dwc_archive

archive_path = create_dwc_archive(
    output_dir="./output/",
    version="1.0.0",
    filter_sql="confidence > 0.8 AND gbif_validated = 1",
    include_multimedia=True,
    validate_archive=True
)

print(f"Archive created: {archive_path}")
```

### Custom Export Formats

#### `export_custom_format(db_path, output_path, field_mapping)`

Export data with custom field mappings.

**Example**:
```python
from export_review import export_custom_format

custom_mapping = {
    "species": "scientific_name",
    "location": "locality",
    "date_collected": "collection_date",
    "collector_name": "collector"
}

export_custom_format(
    db_path="./output/app.db",
    output_path="./exports/custom_format.csv",
    field_mapping=custom_mapping,
    filter_sql="confidence > 0.6"
)
```

---

## Configuration API

### Configuration Management

#### `load_config(config_path, merge_defaults=True)`

Load and parse configuration files.

**Example**:
```python
from config import load_config

config = load_config(
    config_path="./config/institution.toml",
    merge_defaults=True
)

print(f"Preferred engine: {config['ocr']['preferred_engine']}")
print(f"Enabled engines: {config['ocr']['enabled_engines']}")
```

#### `validate_config(config)`

Validate configuration parameters.

**Example**:
```python
from config import validate_config

validation_result = validate_config(config)

if not validation_result.is_valid:
    print(f"Configuration errors: {validation_result.errors}")
```

### Dynamic Configuration

#### `update_config(config, updates)`

Update configuration parameters at runtime.

**Example**:
```python
from config import update_config

updated_config = update_config(config, {
    'ocr.confidence_threshold': 0.8,
    'gpt.model': 'gpt-4-vision-preview',
    'preprocess.max_dim_px': 3000
})
```

---

## Error Handling

### Custom Exceptions

The toolkit defines several custom exception types for different error conditions:

```python
from engines.errors import EngineError
from io_utils.database import DatabaseError
from qc.errors import ValidationError

try:
    result = process_specimen(image_path, config)
except EngineError as e:
    print(f"OCR engine error: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Error Recovery

#### `retry_failed_specimens(db_path, max_retries=3)`

Retry processing for specimens that previously failed.

**Example**:
```python
from cli import retry_failed_specimens

retry_result = retry_failed_specimens(
    db_path="./output/app.db",
    max_retries=3,
    engine_override="gpt"  # Try different engine
)

print(f"Retry success rate: {retry_result.success_rate}")
```

---

## Integration Examples

### Custom Processing Pipeline

```python
from pathlib import Path
from cli import process_specimen
from qc.gbif import validate_taxonomy
from export_review import export_darwin_core

def custom_pipeline(image_dir, output_dir):
    """Custom processing pipeline with enhanced validation."""

    config = load_config("./config/custom.toml")
    results = []

    for image_path in Path(image_dir).glob("*.jpg"):
        # Process specimen
        result = process_specimen(image_path, config)

        # Enhanced validation
        if result.scientific_name:
            gbif_result = validate_taxonomy(result.scientific_name)
            result.gbif_validated = gbif_result.is_match

        # Custom quality flags
        if result.confidence < 0.7:
            result.needs_review = True

        results.append(result)

    # Export results
    export_darwin_core(
        results=results,
        output_path=Path(output_dir) / "custom_export.csv"
    )

    return results
```

### Batch Processing with Monitoring

```python
import time
from concurrent.futures import ThreadPoolExecutor
from cli import process_specimen

def monitored_batch_process(image_paths, config, max_workers=4):
    """Batch processing with progress monitoring."""

    results = []
    failed = []

    def process_with_monitoring(image_path):
        try:
            start_time = time.time()
            result = process_specimen(image_path, config)
            result.processing_time = time.time() - start_time
            return result
        except Exception as e:
            failed.append((image_path, str(e)))
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_with_monitoring, img)
            for img in image_paths
        ]

        for i, future in enumerate(futures):
            result = future.result()
            if result:
                results.append(result)

            # Progress reporting
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(image_paths)} specimens")

    return results, failed
```

This API reference provides the foundation for building custom integrations and extending the toolkit for specialized use cases. For specific implementation details, refer to the source code and existing examples in the codebase.
