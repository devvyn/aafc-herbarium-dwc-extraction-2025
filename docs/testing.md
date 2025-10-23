# Testing Guide

**Comprehensive guide to running and writing tests for the herbarium extraction system**

This document covers all aspects of testing: running tests, understanding test types, writing new tests, and maintaining test quality.

---

## Quick Start

### Run All Tests
```bash
# Run complete test suite
uv run python -m pytest

# Run with verbose output
uv run python -m pytest -v

# Run with coverage report
uv run python -m pytest --cov=src --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only (fast)
uv run python -m pytest tests/unit/ -v

# Integration tests only (slower)
uv run python -m pytest tests/integration/ -v

# Regression tests (database compatibility)
./test-regression.sh
```

---

## Test Organization

### Directory Structure
```
tests/
├── __init__.py
├── unit/                    # Fast, isolated tests
│   ├── test_archive.py      # Darwin Core archive creation
│   ├── test_candidates.py   # Database candidate models
│   ├── test_cli_helpers.py  # CLI utility functions
│   ├── test_cli_ocr.py      # OCR engine selection logic
│   ├── test_config.py       # Configuration loading
│   └── ...
├── integration/             # End-to-end workflow tests
│   ├── test_archive.py      # Full archive generation
│   ├── test_cli_process.py  # Complete processing pipeline
│   ├── test_web_review.py   # Web interface integration
│   └── ...
├── slash_commands/          # Custom slash command tests
│   └── test_*.py
└── resources/               # Test data and fixtures
    └── sample_images/
```

### Test Types

#### Unit Tests (tests/unit/)
**Purpose**: Test individual functions and classes in isolation

**Characteristics**:
- Fast (< 1 second per test)
- No external dependencies (APIs, databases, files)
- Use mocking/patching extensively
- Focus on single component behavior

**Example**:
```python
# tests/unit/test_cli_ocr.py
def test_process_cli_uses_preferred_engine(monkeypatch, tmp_path):
    """Test that CLI respects configured OCR engine preference"""
    calls = []

    def fake_dispatch(task, *args, engine="gpt", **kwargs):
        if task == "image_to_text" and engine == "vision":
            calls.append(engine)
            return "vision text", [0.9]
        return {}, {"field": 0.9}

    cfg = {
        "ocr": {
            "preferred_engine": "vision",
            "confidence_threshold": 0.7,
        }
    }

    # Run test with mocked dispatch
    out_dir = _setup(monkeypatch, tmp_path, cfg, fake_dispatch)
    cli.process_cli(tmp_path, out_dir, None)

    assert calls == ["vision"]
```

#### Integration Tests (tests/integration/)
**Purpose**: Test how components work together

**Characteristics**:
- Slower (1-10 seconds per test)
- May use temporary files, databases
- Test complete workflows
- Verify end-to-end functionality

**Example**:
```python
# tests/integration/test_cli_process.py
def test_process_generates_outputs(tmp_path):
    """Test that processing creates expected output files"""
    # Create test image
    img_path = tmp_path / "specimen.jpg"
    create_test_image(img_path)

    # Process image
    output_dir = tmp_path / "output"
    process_specimen(img_path, output_dir)

    # Verify outputs
    assert (output_dir / "raw.jsonl").exists()
    assert (output_dir / "occurrence.csv").exists()
    assert (output_dir / "candidates.db").exists()
```

#### Regression Tests (./test-regression.sh)
**Purpose**: Prevent known bugs from reoccurring

**Focus Areas**:
- Database compatibility (SQLAlchemy ↔ sqlite3)
- Web review interface integration
- Candidate model behavior
- Data migration compatibility

**Run regression tests**:
```bash
./test-regression.sh

# Output:
# 🧪 Running Database Compatibility Regression Tests
# ==================================================
# 📊 Testing SQLAlchemy <-> sqlite3 compatibility...
# ✓ test_fetch_candidates_sqlite_compatibility PASSED
# ✓ test_sqlalchemy_and_sqlite3_equivalence PASSED
#
# 🌐 Testing web review database integration...
# ✓ test_web_review_database_compatibility PASSED
#
# ✅ All regression tests passed!
```

---

## Running Tests

### Basic Usage

#### Run All Tests
```bash
# Standard run
uv run python -m pytest

# Verbose output (shows each test name)
uv run python -m pytest -v

# Very verbose (shows test docstrings)
uv run python -m pytest -vv
```

#### Run Specific Tests
```bash
# Run single test file
uv run python -m pytest tests/unit/test_cli_ocr.py

# Run single test function
uv run python -m pytest tests/unit/test_cli_ocr.py::test_process_cli_uses_preferred_engine

# Run tests matching pattern
uv run python -m pytest -k "ocr" -v

# Run tests NOT matching pattern
uv run python -m pytest -k "not slow" -v
```

#### Run by Test Type
```bash
# Unit tests only (fast)
uv run python -m pytest tests/unit/

# Integration tests only
uv run python -m pytest tests/integration/

# Slash command tests
uv run python -m pytest tests/slash_commands/
```

### Advanced Options

#### Stop on First Failure
```bash
# Stop immediately on first failure
uv run python -m pytest -x

# Stop after 3 failures
uv run python -m pytest --maxfail=3
```

#### Show Test Output
```bash
# Show print statements
uv run python -m pytest -s

# Show local variables on failure
uv run python -m pytest -l

# Show full diff on assertion failures
uv run python -m pytest -vv
```

#### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
uv run python -m pytest -n auto

# Run on 4 cores
uv run python -m pytest -n 4
```

#### Coverage Reporting
```bash
# Run with coverage
uv run python -m pytest --cov=src

# Generate HTML coverage report
uv run python -m pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Writing Tests

### Test Structure

#### Basic Test Template
```python
# tests/unit/test_my_feature.py
import pytest
from src.my_module import my_function

def test_my_function_basic_behavior():
    """Test that my_function works correctly with valid input"""
    result = my_function(input_value="test")
    assert result == expected_value

def test_my_function_edge_cases():
    """Test my_function handles edge cases"""
    # Empty input
    assert my_function("") == default_value

    # None input
    with pytest.raises(ValueError):
        my_function(None)
```

#### Using Fixtures
```python
import pytest

@pytest.fixture
def sample_image(tmp_path):
    """Create a temporary test image"""
    from PIL import Image
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), "white")
    img.save(img_path)
    return img_path

def test_ocr_with_fixture(sample_image):
    """Test OCR engine with test image"""
    from engines.vision_swift import image_to_text
    text, confidences = image_to_text(sample_image)
    assert isinstance(text, str)
    assert isinstance(confidences, list)
```

#### Mocking External Dependencies
```python
from unittest.mock import Mock, patch

def test_with_mocked_api():
    """Test function that calls external API"""
    # Mock the API call
    with patch('src.api.fetch_data') as mock_fetch:
        mock_fetch.return_value = {"result": "success"}

        # Run function that uses API
        result = process_with_api()

        # Verify mock was called correctly
        mock_fetch.assert_called_once()
        assert result["status"] == "success"
```

#### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("AAFC-001", "AAFC-001"),
    ("  AAFC-002  ", "AAFC-002"),  # Whitespace trimmed
    ("", None),                     # Empty string
    (None, None),                   # None value
])
def test_normalize_catalog_number(input, expected):
    """Test catalog number normalization with various inputs"""
    result = normalize_catalog_number(input)
    assert result == expected
```

### Test Organization Best Practices

#### One Test, One Assertion (Generally)
```python
# Good: Clear, focused test
def test_catalog_number_extraction():
    """Test catalog number is extracted correctly"""
    text = "Specimen No. AAFC-12345"
    result = extract_catalog_number(text)
    assert result == "AAFC-12345"

def test_catalog_number_missing():
    """Test behavior when catalog number is missing"""
    text = "No catalog number here"
    result = extract_catalog_number(text)
    assert result is None

# Acceptable: Multiple related assertions
def test_extraction_completeness():
    """Test all Darwin Core fields are extracted"""
    result = extract_darwin_core(sample_text)
    assert result["catalogNumber"] == "AAFC-001"
    assert result["scientificName"] == "Pinus strobus"
    assert result["eventDate"] == "1969-08-14"
```

#### Use Descriptive Test Names
```python
# Good: Descriptive names
def test_process_handles_rotated_images()
def test_export_creates_valid_darwin_core_archive()
def test_gbif_validation_flags_invalid_coordinates()

# Bad: Vague names
def test_process()
def test_export()
def test_validation()
```

#### Document Expected Behavior
```python
def test_confidence_threshold_filters_low_quality():
    """Test that specimens below confidence threshold are flagged

    Given:
        - 3 specimens with confidences [0.95, 0.72, 0.88]
        - Confidence threshold set to 0.80

    Expect:
        - Specimens 1 and 3 pass (0.95, 0.88 >= 0.80)
        - Specimen 2 flagged for review (0.72 < 0.80)
    """
    specimens = [
        {"id": "1", "confidence": 0.95},
        {"id": "2", "confidence": 0.72},
        {"id": "3", "confidence": 0.88},
    ]

    flagged = filter_by_confidence(specimens, threshold=0.80)

    assert len(flagged) == 1
    assert flagged[0]["id"] == "2"
```

---

## Test Data and Fixtures

### Using Test Resources
```bash
# Test resources directory
tests/resources/
├── sample_images/
│   ├── specimen_printed.jpg      # Printed label
│   ├── specimen_handwritten.jpg  # Handwritten label
│   └── specimen_mixed.jpg        # Mixed label
├── sample_data/
│   ├── raw_ocr.jsonl            # Sample OCR output
│   └── occurrence.csv            # Sample Darwin Core data
└── fixtures/
    └── test_database.db          # Pre-populated test database
```

### Loading Test Data
```python
import pytest
from pathlib import Path

@pytest.fixture
def test_resources():
    """Return path to test resources directory"""
    return Path(__file__).parent / "resources"

@pytest.fixture
def sample_specimen_image(test_resources):
    """Return path to sample specimen image"""
    return test_resources / "sample_images" / "specimen_printed.jpg"

def test_with_real_image(sample_specimen_image):
    """Test OCR with real specimen image"""
    from engines.vision_swift import image_to_text
    text, confidences = image_to_text(sample_specimen_image)
    assert len(text) > 0
    assert all(0 <= c <= 1 for c in confidences)
```

---

## Continuous Integration

### GitHub Actions (Planned)
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --dev

      - name: Run tests
        run: uv run python -m pytest tests/ -v

      - name: Run regression tests
        run: ./test-regression.sh
```

### Pre-commit Hooks
```bash
# Install pre-commit (optional but recommended)
uv pip install pre-commit

# Install git hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Test Markers

### Using pytest Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_process_large_batch():
    """Test processing 1000 specimens (takes ~5 minutes)"""
    # ... test implementation

# Mark tests requiring API keys
@pytest.mark.requires_api
def test_gpt_extraction():
    """Test GPT-4 extraction (requires OPENAI_API_KEY)"""
    # ... test implementation

# Mark tests by feature
@pytest.mark.specify
def test_specify_command():
    """Test /specify slash command"""
    # ... test implementation
```

### Running Tests by Marker
```bash
# Run only fast tests (skip slow)
uv run python -m pytest -m "not slow"

# Run only API tests
uv run python -m pytest -m requires_api

# Run specify command tests
uv run python -m pytest -m specify
```

### Defined Markers (pytest.ini)
```ini
[pytest]
markers =
    specify: Tests for /specify command
    plan: Tests for /plan command
    tasks: Tests for /tasks command
    implement: Tests for /implement command
    slow: Tests that take >10 seconds
    requires_api: Tests requiring API keys
```

---

## Debugging Tests

### Interactive Debugging with pdb
```bash
# Drop into debugger on failure
uv run python -m pytest --pdb

# Drop into debugger on first failure
uv run python -m pytest -x --pdb
```

### Using pytest Trace
```python
def test_with_debugging():
    """Test with embedded breakpoint"""
    result = my_function()

    # Drop into debugger here
    pytest.set_trace()

    assert result == expected
```

### Print Debugging
```bash
# Show print statements
uv run python -m pytest -s

# Show output even for passing tests
uv run python -m pytest -s -v
```

---

## Common Testing Patterns

### Testing File Operations
```python
def test_creates_output_files(tmp_path):
    """Test that processing creates expected files"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Run function that creates files
    process_specimen(input_image, output_dir)

    # Verify files exist
    assert (output_dir / "raw.jsonl").exists()
    assert (output_dir / "occurrence.csv").exists()

    # Verify file contents
    with open(output_dir / "occurrence.csv") as f:
        content = f.read()
        assert "catalogNumber" in content
```

### Testing Database Operations
```python
def test_database_insertion(tmp_path):
    """Test candidate insertion into database"""
    db_path = tmp_path / "test.db"
    session = init_candidate_db(db_path)

    # Insert test candidate
    candidate = CandidateModel(
        specimen_image_sha256="abc123",
        field="catalogNumber",
        value="AAFC-001",
        confidence=0.95,
    )
    session.add(candidate)
    session.commit()

    # Verify insertion
    result = session.query(CandidateModel).first()
    assert result.value == "AAFC-001"
    assert result.confidence == 0.95

    session.close()
```

### Testing API Calls
```python
@patch('src.api.gbif.requests.get')
def test_gbif_api_call(mock_get):
    """Test GBIF API integration"""
    # Mock API response
    mock_get.return_value.json.return_value = {
        "usageKey": 12345,
        "scientificName": "Pinus strobus L.",
        "confidence": 95,
    }
    mock_get.return_value.status_code = 200

    # Call function that uses API
    result = validate_scientific_name("Pinus strobus")

    # Verify result
    assert result["scientificName"] == "Pinus strobus L."
    assert result["confidence"] == 95

    # Verify API was called correctly
    mock_get.assert_called_once()
```

---

## Test Coverage

### Measuring Coverage
```bash
# Run with coverage
uv run python -m pytest --cov=src

# Generate HTML report
uv run python -m pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Goals
- **Unit tests**: Aim for >80% coverage
- **Integration tests**: Cover critical user workflows
- **Regression tests**: Prevent known bugs

### What to Test
**High Priority**:
- Darwin Core field extraction
- Database operations
- OCR engine selection logic
- Web review interface
- Export/archive generation

**Medium Priority**:
- Configuration loading
- Image preprocessing
- Quality control checks
- GBIF validation

**Lower Priority**:
- Utility functions
- Logging
- CLI help text

---

## Troubleshooting Tests

### Common Issues

#### Tests Fail Locally But Pass in CI
```bash
# Check Python version matches CI
python --version

# Clear pytest cache
rm -rf .pytest_cache __pycache__

# Reinstall dependencies
uv sync --reinstall
```

#### Import Errors
```bash
# Ensure package is installed in development mode
uv pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

#### Database Lock Errors
```bash
# Close all database connections in test
def test_with_database(tmp_path):
    db_path = tmp_path / "test.db"
    session = init_candidate_db(db_path)

    # ... test code ...

    # IMPORTANT: Close session
    session.close()
```

#### Slow Tests
```bash
# Identify slow tests
uv run python -m pytest --durations=10

# Run only fast tests
uv run python -m pytest -m "not slow"
```

---

## Best Practices Summary

1. **Write tests first** (TDD) or immediately after implementing features
2. **Keep tests isolated** - no dependencies between tests
3. **Use descriptive names** - test names should document behavior
4. **One test, one concept** - focused, single-purpose tests
5. **Mock external dependencies** - APIs, databases, file systems
6. **Use fixtures** - share setup code across tests
7. **Document edge cases** - test boundary conditions
8. **Run tests frequently** - catch bugs early
9. **Maintain test quality** - refactor tests as code evolves
10. **Measure coverage** - aim for comprehensive testing

---

## Quick Reference

### Most Common Commands
```bash
# Run all tests
uv run python -m pytest

# Run specific test file
uv run python -m pytest tests/unit/test_cli_ocr.py

# Run with verbose output
uv run python -m pytest -v

# Run regression tests
./test-regression.sh

# Run with coverage
uv run python -m pytest --cov=src --cov-report=html

# Stop on first failure
uv run python -m pytest -x

# Run tests matching pattern
uv run python -m pytest -k "ocr" -v
```

### Writing a New Test
```python
# tests/unit/test_my_feature.py
import pytest

def test_my_new_feature():
    """Brief description of what this tests"""
    # Arrange: Set up test data
    input_data = ...

    # Act: Execute the function
    result = my_function(input_data)

    # Assert: Verify the result
    assert result == expected_value
```

---

**Questions?** See [troubleshooting.md](troubleshooting.md) or [open an issue](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues).
