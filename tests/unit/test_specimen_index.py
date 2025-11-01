"""Tests for specimen provenance index (v2.0.0 architecture)."""

from datetime import datetime, timezone

import pytest

from provenance.specimen_index import (
    ExtractionResult,
    ImageTransformation,
    OriginalFile,
    SpecimenIndex,
)


@pytest.fixture
def specimen_index(tmp_path):
    """Provide a temporary specimen index database."""
    db_path = tmp_path / "test_index.db"
    index = SpecimenIndex(db_path)
    yield index
    index.close()


@pytest.fixture
def sample_specimen_id():
    """Provide a sample specimen ID."""
    return "AAFC12345_001"


@pytest.fixture
def sample_image_sha256():
    """Provide a sample image SHA256."""
    return "a" * 64


@pytest.fixture
def sample_extraction_params():
    """Provide sample extraction parameters."""
    return {
        "engine": "vision",
        "model": "default",
        "preprocessing": ["grayscale", "deskew"],
    }


def test_specimen_index_init(tmp_path):
    """Test SpecimenIndex initialization creates database and schema."""
    db_path = tmp_path / "index.db"
    index = SpecimenIndex(db_path)

    assert db_path.exists()

    # Verify tables exist
    tables = index.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t["name"] for t in tables]

    assert "specimens" in table_names
    assert "original_files" in table_names
    assert "image_transformations" in table_names
    assert "extractions" in table_names
    assert "specimen_aggregations" in table_names
    assert "reviews" in table_names
    assert "data_quality_flags" in table_names

    index.close()


def test_register_specimen_new(specimen_index, sample_specimen_id):
    """Test registering a new specimen."""
    created = specimen_index.register_specimen(
        specimen_id=sample_specimen_id,
        camera_filename="DSC_12345.NEF",
        expected_catalog_number="AAFC-12345",
    )

    assert created is True

    # Verify in database
    row = specimen_index.conn.execute(
        "SELECT * FROM specimens WHERE specimen_id = ?", (sample_specimen_id,)
    ).fetchone()

    assert row is not None
    assert row["specimen_id"] == sample_specimen_id
    assert row["camera_filename"] == "DSC_12345.NEF"
    assert row["expected_catalog_number"] == "AAFC-12345"


def test_register_specimen_duplicate(specimen_index, sample_specimen_id):
    """Test registering the same specimen twice returns False."""
    specimen_index.register_specimen(sample_specimen_id)

    # Try to register again
    created = specimen_index.register_specimen(sample_specimen_id)

    assert created is False


def test_register_original_file(specimen_index, sample_specimen_id, sample_image_sha256):
    """Test registering an original camera file."""
    specimen_index.register_specimen(sample_specimen_id)

    original = OriginalFile(
        sha256=sample_image_sha256,
        specimen_id=sample_specimen_id,
        file_path="/path/to/DSC_12345.NEF",
        format="NEF",
        dimensions=(6000, 4000),
        size_bytes=25_000_000,
        role="original_raw",
        captured_at=datetime(2024, 10, 15, 10, 30, 0, tzinfo=timezone.utc),
    )

    specimen_index.register_original_file(original)

    # Verify in database
    row = specimen_index.conn.execute(
        "SELECT * FROM original_files WHERE sha256 = ?", (sample_image_sha256,)
    ).fetchone()

    assert row is not None
    assert row["specimen_id"] == sample_specimen_id
    assert row["file_path"] == "/path/to/DSC_12345.NEF"
    assert row["format"] == "NEF"
    assert row["size_bytes"] == 25_000_000
    assert row["role"] == "original_raw"


def test_register_transformation(specimen_index, sample_specimen_id, sample_image_sha256):
    """Test registering an image transformation."""
    specimen_index.register_specimen(sample_specimen_id)

    # Register original first
    original = OriginalFile(
        sha256=sample_image_sha256,
        specimen_id=sample_specimen_id,
        file_path="/original.nef",
        format="NEF",
    )
    specimen_index.register_original_file(original)

    # Register transformation
    derived_sha256 = "b" * 64
    transformation = ImageTransformation(
        sha256=derived_sha256,
        specimen_id=sample_specimen_id,
        derived_from=sample_image_sha256,
        operation="resize_and_convert",
        params={"max_dim": 4000, "format": "jpg", "quality": 95},
        timestamp=datetime.now(timezone.utc),
        tool="PIL",
        tool_version="10.0.0",
        stored_at="/derivatives/derived.jpg",
    )

    specimen_index.register_transformation(transformation)

    # Verify in database
    row = specimen_index.conn.execute(
        "SELECT * FROM image_transformations WHERE sha256 = ?", (derived_sha256,)
    ).fetchone()

    assert row is not None
    assert row["specimen_id"] == sample_specimen_id
    assert row["derived_from"] == sample_image_sha256
    assert row["operation"] == "resize_and_convert"
    assert row["tool"] == "PIL"


def test_get_specimen_id_from_original_image(
    specimen_index, sample_specimen_id, sample_image_sha256
):
    """Test retrieving specimen ID from original image SHA256."""
    specimen_index.register_specimen(sample_specimen_id)

    original = OriginalFile(
        sha256=sample_image_sha256,
        specimen_id=sample_specimen_id,
        file_path="/original.jpg",
        format="JPG",
    )
    specimen_index.register_original_file(original)

    # Retrieve specimen ID
    retrieved_id = specimen_index.get_specimen_id_from_image(sample_image_sha256)

    assert retrieved_id == sample_specimen_id


def test_get_specimen_id_from_transformed_image(
    specimen_index, sample_specimen_id, sample_image_sha256
):
    """Test retrieving specimen ID from transformed image SHA256."""
    specimen_index.register_specimen(sample_specimen_id)

    # Register original
    original = OriginalFile(
        sha256=sample_image_sha256,
        specimen_id=sample_specimen_id,
        file_path="/original.jpg",
        format="JPG",
    )
    specimen_index.register_original_file(original)

    # Register transformation
    derived_sha256 = "c" * 64
    transformation = ImageTransformation(
        sha256=derived_sha256,
        specimen_id=sample_specimen_id,
        derived_from=sample_image_sha256,
        operation="grayscale",
        params={},
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.register_transformation(transformation)

    # Retrieve specimen ID from derived image
    retrieved_id = specimen_index.get_specimen_id_from_image(derived_sha256)

    assert retrieved_id == sample_specimen_id


def test_get_specimen_id_from_nonexistent_image(specimen_index):
    """Test retrieving specimen ID for nonexistent image returns None."""
    result = specimen_index.get_specimen_id_from_image("nonexistent_sha256")

    assert result is None


def test_should_extract_new_extraction(
    specimen_index, sample_specimen_id, sample_image_sha256, sample_extraction_params
):
    """Test should_extract returns True for new extraction."""
    specimen_index.register_specimen(sample_specimen_id)

    should_extract, existing_id = specimen_index.should_extract(
        sample_image_sha256, sample_extraction_params
    )

    assert should_extract is True
    assert existing_id is None


def test_should_extract_duplicate_completed(
    specimen_index, sample_specimen_id, sample_image_sha256, sample_extraction_params
):
    """Test should_extract returns False for completed extraction."""
    specimen_index.register_specimen(sample_specimen_id)

    # Record a completed extraction
    extraction = ExtractionResult(
        extraction_id="ext_001",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash=specimen_index._hash_params(sample_extraction_params),
        run_id="run_001",
        status="completed",
        dwc_fields={"catalogNumber": {"value": "AAFC-12345", "confidence": 0.95}},
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.record_extraction(extraction)

    # Check if should extract again
    should_extract, existing_id = specimen_index.should_extract(
        sample_image_sha256, sample_extraction_params
    )

    assert should_extract is False
    assert existing_id == "ext_001"


def test_should_extract_failed_extraction_reextracts(
    specimen_index, sample_specimen_id, sample_image_sha256, sample_extraction_params
):
    """Test should_extract returns True for failed extraction (re-extract)."""
    specimen_index.register_specimen(sample_specimen_id)

    # Record a failed extraction
    extraction = ExtractionResult(
        extraction_id="ext_failed",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash=specimen_index._hash_params(sample_extraction_params),
        run_id="run_001",
        status="failed",
        dwc_fields={},
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.record_extraction(extraction)

    # Check if should extract again
    should_extract, existing_id = specimen_index.should_extract(
        sample_image_sha256, sample_extraction_params
    )

    assert should_extract is True
    assert existing_id == "ext_failed"


def test_record_extraction(
    specimen_index, sample_specimen_id, sample_image_sha256, sample_extraction_params
):
    """Test recording an extraction result."""
    specimen_index.register_specimen(sample_specimen_id)

    extraction = ExtractionResult(
        extraction_id="ext_002",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash=specimen_index._hash_params(sample_extraction_params),
        run_id="run_002",
        status="completed",
        dwc_fields={
            "catalogNumber": {"value": "AAFC-12345", "confidence": 0.95},
            "scientificName": {"value": "Pinus contorta", "confidence": 0.88},
        },
        raw_jsonl_offset=12345,
        timestamp=datetime.now(timezone.utc),
    )

    specimen_index.record_extraction(extraction)

    # Verify in database
    row = specimen_index.conn.execute(
        "SELECT * FROM extractions WHERE extraction_id = ?", ("ext_002",)
    ).fetchone()

    assert row is not None
    assert row["specimen_id"] == sample_specimen_id
    assert row["status"] == "completed"
    assert row["raw_jsonl_offset"] == 12345


def test_aggregate_specimen_extractions_single(
    specimen_index, sample_specimen_id, sample_image_sha256, sample_extraction_params
):
    """Test aggregating a single extraction."""
    specimen_index.register_specimen(sample_specimen_id)

    # Record one extraction
    extraction = ExtractionResult(
        extraction_id="ext_001",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash=specimen_index._hash_params(sample_extraction_params),
        run_id="run_001",
        status="completed",
        dwc_fields={
            "catalogNumber": {"value": "AAFC-12345", "confidence": 0.95},
            "scientificName": {"value": "Pinus contorta", "confidence": 0.88},
        },
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.record_extraction(extraction)

    # Aggregate
    result = specimen_index.aggregate_specimen_extractions(sample_specimen_id)

    assert "candidate_fields" in result
    assert "best_candidates" in result
    assert "catalogNumber" in result["best_candidates"]
    assert result["best_candidates"]["catalogNumber"]["value"] == "AAFC-12345"
    assert result["best_candidates"]["catalogNumber"]["confidence"] == 0.95


def test_aggregate_specimen_extractions_multiple_selects_best(
    specimen_index, sample_specimen_id, sample_image_sha256
):
    """Test aggregating multiple extractions selects highest confidence."""
    specimen_index.register_specimen(sample_specimen_id)

    # Record three extractions with different confidences
    for i, (catalog, confidence) in enumerate(
        [("AAFC-12345", 0.75), ("AAFC-12345", 0.95), ("AAFC-12345", 0.80)]
    ):
        extraction = ExtractionResult(
            extraction_id=f"ext_{i:03d}",
            specimen_id=sample_specimen_id,
            image_sha256=sample_image_sha256,
            params_hash=specimen_index._hash_params({"run": i}),
            run_id=f"run_{i:03d}",
            status="completed",
            dwc_fields={"catalogNumber": {"value": catalog, "confidence": confidence}},
            timestamp=datetime.now(timezone.utc),
        )
        specimen_index.record_extraction(extraction)

    # Aggregate
    result = specimen_index.aggregate_specimen_extractions(sample_specimen_id)

    # Should select the 0.95 confidence result
    assert result["best_candidates"]["catalogNumber"]["confidence"] == 0.95
    assert result["best_candidates"]["catalogNumber"]["source"] == "ext_001"


def test_aggregate_specimen_extractions_filters_empty_values(
    specimen_index, sample_specimen_id, sample_image_sha256
):
    """Test aggregation filters out empty/None values."""
    specimen_index.register_specimen(sample_specimen_id)

    # Record extraction with empty and valid values
    extraction = ExtractionResult(
        extraction_id="ext_001",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash=specimen_index._hash_params({}),
        run_id="run_001",
        status="completed",
        dwc_fields={
            "catalogNumber": {"value": "AAFC-12345", "confidence": 0.95},
            "recordedBy": {"value": None, "confidence": 0.0},
            "locality": {"value": "", "confidence": 0.5},
        },
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.record_extraction(extraction)

    # Aggregate
    result = specimen_index.aggregate_specimen_extractions(sample_specimen_id)

    # Should only have catalogNumber (others are None/empty)
    assert "catalogNumber" in result["best_candidates"]
    assert "recordedBy" not in result["best_candidates"]
    assert "locality" not in result["best_candidates"]


def test_aggregate_specimen_extractions_no_completed(specimen_index, sample_specimen_id):
    """Test aggregation with no completed extractions."""
    specimen_index.register_specimen(sample_specimen_id)

    # Don't record any extractions
    result = specimen_index.aggregate_specimen_extractions(sample_specimen_id)

    assert result["candidate_fields"] == {}
    assert result["best_candidates"] == {}


def test_flag_specimen(specimen_index, sample_specimen_id):
    """Test adding a data quality flag to a specimen."""
    specimen_index.register_specimen(sample_specimen_id)

    specimen_index.flag_specimen(
        sample_specimen_id,
        "MISSING_REQUIRED_FIELD",
        "catalogNumber is missing",
        severity="error",
    )

    # Verify in database
    row = specimen_index.conn.execute(
        "SELECT * FROM data_quality_flags WHERE specimen_id = ?", (sample_specimen_id,)
    ).fetchone()

    assert row is not None
    assert row["flag_type"] == "MISSING_REQUIRED_FIELD"
    assert row["severity"] == "error"
    assert row["message"] == "catalogNumber is missing"
    assert row["resolved"] == 0  # SQLite uses 0/1 for boolean


def test_get_specimen_flags_unresolved_only(specimen_index, sample_specimen_id):
    """Test retrieving only unresolved flags."""
    specimen_index.register_specimen(sample_specimen_id)

    # Add two unresolved flags
    specimen_index.flag_specimen(sample_specimen_id, "FLAG1", "Issue 1", "warning")
    specimen_index.flag_specimen(sample_specimen_id, "FLAG2", "Issue 2", "error")

    # Mark one as resolved
    specimen_index.conn.execute(
        """
        UPDATE data_quality_flags
        SET resolved = TRUE
        WHERE specimen_id = ? AND flag_type = ?
        """,
        (sample_specimen_id, "FLAG1"),
    )
    specimen_index.conn.commit()

    # Get unresolved only
    flags = specimen_index.get_specimen_flags(sample_specimen_id, unresolved_only=True)

    assert len(flags) == 1
    assert flags[0]["flag_type"] == "FLAG2"


def test_get_specimen_flags_include_resolved(specimen_index, sample_specimen_id):
    """Test retrieving all flags including resolved."""
    specimen_index.register_specimen(sample_specimen_id)

    # Add flags and resolve one
    specimen_index.flag_specimen(sample_specimen_id, "FLAG1", "Issue 1", "warning")
    specimen_index.flag_specimen(sample_specimen_id, "FLAG2", "Issue 2", "error")

    specimen_index.conn.execute(
        "UPDATE data_quality_flags SET resolved = TRUE WHERE flag_type = ?", ("FLAG1",)
    )
    specimen_index.conn.commit()

    # Get all flags
    flags = specimen_index.get_specimen_flags(sample_specimen_id, unresolved_only=False)

    assert len(flags) == 2


def test_check_catalog_number_duplicates(specimen_index):
    """Test checking for duplicate catalog numbers across specimens."""
    # Register two specimens with same catalog number
    specimen_index.register_specimen("spec_001")
    specimen_index.register_specimen("spec_002")

    # Create aggregations with duplicate catalog number
    for spec_id in ["spec_001", "spec_002"]:
        specimen_index.conn.execute(
            """
            INSERT INTO specimen_aggregations
            (specimen_id, best_candidates_json, review_status)
            VALUES (?, ?, ?)
            """,
            (
                spec_id,
                '{"catalogNumber": {"value": "AAFC-99999", "confidence": 0.9}}',
                "pending",
            ),
        )
    specimen_index.conn.commit()

    # Check for duplicates
    duplicate_count = specimen_index.check_catalog_number_duplicates()

    assert duplicate_count == 1

    # Verify flags were created
    flags_001 = specimen_index.get_specimen_flags("spec_001")
    flags_002 = specimen_index.get_specimen_flags("spec_002")

    assert len(flags_001) == 1
    assert len(flags_002) == 1
    assert flags_001[0]["flag_type"] == "DUPLICATE_CATALOG_NUMBER"
    assert flags_002[0]["flag_type"] == "DUPLICATE_CATALOG_NUMBER"


def test_check_malformed_catalog_numbers(specimen_index, sample_specimen_id):
    """Test checking for catalog numbers that don't match pattern."""
    specimen_index.register_specimen(sample_specimen_id)

    # Create aggregation with malformed catalog number
    specimen_index.conn.execute(
        """
        INSERT INTO specimen_aggregations
        (specimen_id, best_candidates_json, review_status)
        VALUES (?, ?, ?)
        """,
        (
            sample_specimen_id,
            '{"catalogNumber": {"value": "BAD-FORMAT", "confidence": 0.9}}',
            "pending",
        ),
    )
    specimen_index.conn.commit()

    # Check for malformed (default pattern: AAFC-\d{5,6})
    malformed_count = specimen_index.check_malformed_catalog_numbers()

    assert malformed_count == 1

    # Verify flag was created
    flags = specimen_index.get_specimen_flags(sample_specimen_id)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "MALFORMED_CATALOG_NUMBER"


def test_get_stats(specimen_index, sample_specimen_id, sample_image_sha256):
    """Test retrieving index statistics."""
    # Register specimen and related data
    specimen_index.register_specimen(sample_specimen_id)

    original = OriginalFile(
        sha256=sample_image_sha256,
        specimen_id=sample_specimen_id,
        file_path="/original.jpg",
        format="JPG",
    )
    specimen_index.register_original_file(original)

    extraction = ExtractionResult(
        extraction_id="ext_001",
        specimen_id=sample_specimen_id,
        image_sha256=sample_image_sha256,
        params_hash="hash123",
        run_id="run_001",
        status="completed",
        dwc_fields={},
        timestamp=datetime.now(timezone.utc),
    )
    specimen_index.record_extraction(extraction)

    specimen_index.flag_specimen(sample_specimen_id, "TEST_FLAG", "Test message")

    # Get stats
    stats = specimen_index.get_stats()

    assert stats["total_specimens"] == 1
    assert stats["original_files"] == 1
    assert stats["extractions"] == 1
    assert stats["unresolved_flags"] == 1
    assert stats["transformations"] == 0  # None added
    assert stats["reviews"] == 0  # None added


def test_hash_params_deterministic(specimen_index):
    """Test that parameter hashing is deterministic."""
    params = {"engine": "vision", "preprocessing": ["grayscale", "deskew"], "threshold": 0.8}

    hash1 = specimen_index._hash_params(params)
    hash2 = specimen_index._hash_params(params)

    assert hash1 == hash2


def test_hash_params_order_independent(specimen_index):
    """Test that parameter hashing is order-independent."""
    params1 = {"a": 1, "b": 2, "c": 3}
    params2 = {"c": 3, "a": 1, "b": 2}

    hash1 = specimen_index._hash_params(params1)
    hash2 = specimen_index._hash_params(params2)

    assert hash1 == hash2


def test_context_manager(tmp_path):
    """Test SpecimenIndex as context manager."""
    db_path = tmp_path / "context_test.db"

    with SpecimenIndex(db_path) as index:
        index.register_specimen("spec_001")

        # Verify it works within context
        row = index.conn.execute(
            "SELECT * FROM specimens WHERE specimen_id = ?", ("spec_001",)
        ).fetchone()
        assert row is not None

    # Connection should be closed after context
    # Note: Can't test conn.execute after close as it will raise
    assert db_path.exists()
