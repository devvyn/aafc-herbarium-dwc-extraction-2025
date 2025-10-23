"""Integration tests for end-to-end specimen provenance workflow (v2.0.0)."""

import hashlib
import json
from datetime import datetime, timezone

import pytest
from PIL import Image

from src.provenance.fragment import FragmentType, ProvenanceFragment, create_extraction_fragment
from src.provenance.specimen_index import (
    ExtractionResult,
    ImageTransformation,
    OriginalFile,
    SpecimenIndex,
)


@pytest.fixture
def temp_specimen_db(tmp_path):
    """Provide a temporary specimen database."""
    db_path = tmp_path / "specimen_index.db"
    index = SpecimenIndex(db_path)
    yield index
    index.close()


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image and return its path and SHA256."""
    image_path = tmp_path / "test_image.jpg"
    # Create a simple 100x100 red image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)

    # Calculate SHA256
    with open(image_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    return image_path, sha256


@pytest.fixture
def sample_darwin_core_data():
    """Provide sample Darwin Core data for testing."""
    return {
        "catalogNumber": "AAFC-12345",
        "scientificName": "Pinus contorta Douglas ex Loudon",
        "family": "Pinaceae",
        "eventDate": "2024-08-15",
        "country": "Canada",
        "stateProvince": "Saskatchewan",
        "locality": "Prince Albert National Park",
        "recordedBy": "J. Smith",
        "identifiedBy": "A. Botanist",
        "basisOfRecord": "PreservedSpecimen",
    }


def test_specimen_lifecycle_single_extraction(
    temp_specimen_db, sample_image, sample_darwin_core_data
):
    """Test complete specimen lifecycle with a single extraction."""
    image_path, image_sha256 = sample_image
    specimen_id = "AAFC12345_001"

    # Step 1: Register specimen
    created = temp_specimen_db.register_specimen(
        specimen_id=specimen_id,
        camera_filename="DSC_12345.NEF",
        expected_catalog_number="AAFC-12345",
    )
    assert created is True

    # Step 2: Register original file
    original = OriginalFile(
        sha256=image_sha256,
        specimen_id=specimen_id,
        file_path=str(image_path),
        format="JPG",
        dimensions=(100, 100),
        size_bytes=image_path.stat().st_size,
        role="original_raw",
        captured_at=datetime(2024, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
    )
    temp_specimen_db.register_original_file(original)

    # Step 3: Check deduplication (should extract)
    extraction_params = {"engine": "vision", "model": "gpt-4o-mini"}
    should_extract, existing_id = temp_specimen_db.should_extract(image_sha256, extraction_params)
    assert should_extract is True
    assert existing_id is None

    # Step 4: Record extraction
    extraction = ExtractionResult(
        extraction_id="ext_001",
        specimen_id=specimen_id,
        image_sha256=image_sha256,
        params_hash=temp_specimen_db._hash_params(extraction_params),
        run_id="run_001",
        status="completed",
        dwc_fields={
            field: {"value": value, "confidence": 0.95}
            for field, value in sample_darwin_core_data.items()
        },
        raw_jsonl_offset=0,
        timestamp=datetime.now(timezone.utc),
    )
    temp_specimen_db.record_extraction(extraction)

    # Step 5: Check deduplication (should NOT extract again)
    should_extract, existing_id = temp_specimen_db.should_extract(image_sha256, extraction_params)
    assert should_extract is False
    assert existing_id == "ext_001"

    # Step 6: Aggregate extractions
    aggregation = temp_specimen_db.aggregate_specimen_extractions(specimen_id)
    assert "best_candidates" in aggregation
    assert aggregation["best_candidates"]["catalogNumber"]["value"] == "AAFC-12345"
    assert aggregation["best_candidates"]["catalogNumber"]["confidence"] == 0.95

    # Step 7: Verify statistics
    stats = temp_specimen_db.get_stats()
    assert stats["total_specimens"] == 1
    assert stats["original_files"] == 1
    assert stats["extractions"] == 1
    assert stats["unresolved_flags"] == 0


def test_specimen_workflow_with_image_transformations(temp_specimen_db, sample_image):
    """Test specimen workflow with image preprocessing transformations."""
    image_path, original_sha256 = sample_image
    specimen_id = "AAFC12346_001"

    # Register specimen and original
    temp_specimen_db.register_specimen(specimen_id)
    original = OriginalFile(
        sha256=original_sha256,
        specimen_id=specimen_id,
        file_path=str(image_path),
        format="JPG",
    )
    temp_specimen_db.register_original_file(original)

    # Simulate image transformations (grayscale, resize, etc.)
    transformations = [
        ("grayscale_sha256" * 5, "convert_grayscale", {"format": "jpg"}),
        ("resized_sha256" * 5, "resize", {"max_dim": 2000}),
        ("deskewed_sha256" * 5, "deskew", {"angle": -2.5}),
    ]

    previous_sha256 = original_sha256
    for i, (sha256, operation, params) in enumerate(transformations):
        transformation = ImageTransformation(
            sha256=sha256,
            specimen_id=specimen_id,
            derived_from=previous_sha256,
            operation=operation,
            params=params,
            timestamp=datetime.now(timezone.utc),
            tool="PIL" if i == 0 else "custom",
            tool_version="10.0.0",
            stored_at=f"/derivatives/{operation}.jpg",
        )
        temp_specimen_db.register_transformation(transformation)
        previous_sha256 = sha256

    # Verify lineage tracking
    final_sha256 = transformations[-1][0]
    retrieved_specimen_id = temp_specimen_db.get_specimen_id_from_image(final_sha256)
    assert retrieved_specimen_id == specimen_id

    # Can also trace back to original
    original_retrieved = temp_specimen_db.get_specimen_id_from_image(original_sha256)
    assert original_retrieved == specimen_id

    # Verify stats
    stats = temp_specimen_db.get_stats()
    assert stats["transformations"] == 3


def test_specimen_workflow_multiple_extractions_aggregation(temp_specimen_db, sample_image):
    """Test specimen workflow with multiple extractions and confidence-based aggregation."""
    image_path, image_sha256 = sample_image
    specimen_id = "AAFC12347_001"

    # Register specimen
    temp_specimen_db.register_specimen(specimen_id)

    # Simulate multiple extraction runs with different confidence levels
    extraction_configs = [
        (
            "run_001",
            "ext_001",
            {"catalogNumber": "AAFC-12347", "scientificName": "Plantae sp."},
            {"catalogNumber": 0.85, "scientificName": 0.60},
        ),
        (
            "run_002",
            "ext_002",
            {"catalogNumber": "AAFC-12347", "scientificName": "Pinus contorta"},
            {"catalogNumber": 0.95, "scientificName": 0.92},
        ),
        (
            "run_003",
            "ext_003",
            {"catalogNumber": "AAFC-12347", "scientificName": "Pinus contorta"},
            {"catalogNumber": 0.90, "scientificName": 0.95},
        ),
    ]

    for run_id, ext_id, fields, confidences in extraction_configs:
        dwc_fields = {
            field: {"value": value, "confidence": confidences[field]}
            for field, value in fields.items()
        }

        extraction = ExtractionResult(
            extraction_id=ext_id,
            specimen_id=specimen_id,
            image_sha256=image_sha256 if ext_id == "ext_001" else f"variant_{ext_id}",
            params_hash=temp_specimen_db._hash_params({"run": run_id}),
            run_id=run_id,
            status="completed",
            dwc_fields=dwc_fields,
            timestamp=datetime.now(timezone.utc),
        )
        temp_specimen_db.record_extraction(extraction)

    # Aggregate extractions
    aggregation = temp_specimen_db.aggregate_specimen_extractions(specimen_id)

    # Should select highest confidence values
    # catalogNumber: ext_002 (0.95)
    # scientificName: ext_003 (0.95)
    assert aggregation["best_candidates"]["catalogNumber"]["value"] == "AAFC-12347"
    assert aggregation["best_candidates"]["catalogNumber"]["confidence"] == 0.95
    assert aggregation["best_candidates"]["catalogNumber"]["source"] == "ext_002"

    assert aggregation["best_candidates"]["scientificName"]["value"] == "Pinus contorta"
    assert aggregation["best_candidates"]["scientificName"]["confidence"] == 0.95
    assert aggregation["best_candidates"]["scientificName"]["source"] == "ext_003"

    # Verify all candidate values are tracked
    assert len(aggregation["candidate_fields"]["catalogNumber"]) == 3
    assert len(aggregation["candidate_fields"]["scientificName"]) == 3


def test_specimen_workflow_quality_control_duplicate_catalogs(temp_specimen_db):
    """Test quality control workflow for duplicate catalog numbers."""
    # Register two specimens
    temp_specimen_db.register_specimen("spec_001")
    temp_specimen_db.register_specimen("spec_002")

    # Create aggregations with duplicate catalog number
    duplicate_catalog = "AAFC-99999"
    for spec_id in ["spec_001", "spec_002"]:
        temp_specimen_db.conn.execute(
            """
            INSERT INTO specimen_aggregations
            (specimen_id, best_candidates_json, review_status)
            VALUES (?, ?, ?)
            """,
            (
                spec_id,
                json.dumps({"catalogNumber": {"value": duplicate_catalog, "confidence": 0.9}}),
                "pending",
            ),
        )
    temp_specimen_db.conn.commit()

    # Run quality control check
    duplicate_count = temp_specimen_db.check_catalog_number_duplicates()
    assert duplicate_count == 1

    # Verify flags were created
    flags_001 = temp_specimen_db.get_specimen_flags("spec_001")
    flags_002 = temp_specimen_db.get_specimen_flags("spec_002")

    assert len(flags_001) == 1
    assert len(flags_002) == 1
    assert flags_001[0]["flag_type"] == "DUPLICATE_CATALOG_NUMBER"
    assert flags_002[0]["flag_type"] == "DUPLICATE_CATALOG_NUMBER"
    assert flags_001[0]["severity"] == "error"
    assert duplicate_catalog in flags_001[0]["message"]


def test_specimen_workflow_quality_control_malformed_catalogs(temp_specimen_db):
    """Test quality control workflow for malformed catalog numbers."""
    specimen_id = "spec_003"
    temp_specimen_db.register_specimen(specimen_id)

    # Create aggregation with malformed catalog number
    temp_specimen_db.conn.execute(
        """
        INSERT INTO specimen_aggregations
        (specimen_id, best_candidates_json, review_status)
        VALUES (?, ?, ?)
        """,
        (
            specimen_id,
            json.dumps({"catalogNumber": {"value": "INVALID-FORMAT", "confidence": 0.9}}),
            "pending",
        ),
    )
    temp_specimen_db.conn.commit()

    # Run quality control check
    malformed_count = temp_specimen_db.check_malformed_catalog_numbers()
    assert malformed_count == 1

    # Verify flag
    flags = temp_specimen_db.get_specimen_flags(specimen_id)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "MALFORMED_CATALOG_NUMBER"
    assert flags[0]["severity"] == "warning"


def test_specimen_workflow_failed_extraction_retry(temp_specimen_db, sample_image):
    """Test workflow where failed extraction allows retry."""
    image_path, image_sha256 = sample_image
    specimen_id = "AAFC12348_001"

    temp_specimen_db.register_specimen(specimen_id)

    extraction_params = {"engine": "vision"}

    # Record a failed extraction
    failed_extraction = ExtractionResult(
        extraction_id="ext_failed",
        specimen_id=specimen_id,
        image_sha256=image_sha256,
        params_hash=temp_specimen_db._hash_params(extraction_params),
        run_id="run_001",
        status="failed",
        dwc_fields={},
        timestamp=datetime.now(timezone.utc),
    )
    temp_specimen_db.record_extraction(failed_extraction)

    # Should allow re-extraction for failed attempts
    should_extract, existing_id = temp_specimen_db.should_extract(image_sha256, extraction_params)
    assert should_extract is True
    assert existing_id == "ext_failed"

    # Record successful retry
    success_extraction = ExtractionResult(
        extraction_id="ext_success",
        specimen_id=specimen_id,
        image_sha256=image_sha256,
        params_hash=temp_specimen_db._hash_params(extraction_params),
        run_id="run_002",
        status="completed",
        dwc_fields={"catalogNumber": {"value": "AAFC-12348", "confidence": 0.95}},
        timestamp=datetime.now(timezone.utc),
    )
    temp_specimen_db.record_extraction(success_extraction)

    # Now should NOT allow re-extraction (successful extraction with same params exists)
    should_extract, existing_id = temp_specimen_db.should_extract(image_sha256, extraction_params)
    assert should_extract is False
    assert existing_id == "ext_success"  # Now points to successful extraction

    # Note: Second extraction replaces first in DB due to unique constraint on (image_sha256, params_hash)
    # This is expected behavior - we don't want duplicate extractions with same parameters
    stats = temp_specimen_db.get_stats()
    assert stats["extractions"] == 1


def test_provenance_fragment_integration_with_specimen_index(
    tmp_path, sample_image, sample_darwin_core_data
):
    """Test integration between provenance fragments and specimen index."""
    image_path, image_sha256 = sample_image
    specimen_id = "AAFC12349_001"

    # Create fragment for extraction
    fragment = create_extraction_fragment(
        image_sha256=image_sha256,
        darwin_core_data=sample_darwin_core_data,
        batch_id="batch_001",
        model="gpt-4o-mini",
        temperature=0.7,
        confidence_scores={field: 0.95 for field in sample_darwin_core_data},
        previous_fragment_id="preprocessing_fragment_id",
    )

    # Write fragment to JSONL
    from src.provenance.fragment import write_provenance_fragments

    provenance_path = tmp_path / "provenance.jsonl"
    write_provenance_fragments([fragment], provenance_path)

    # Create specimen index entry
    with SpecimenIndex(tmp_path / "specimen_index.db") as index:
        index.register_specimen(specimen_id)

        # Record extraction with reference to fragment
        extraction = ExtractionResult(
            extraction_id="ext_001",
            specimen_id=specimen_id,
            image_sha256=image_sha256,
            params_hash=index._hash_params({"model": "gpt-4o-mini", "temperature": 0.7}),
            run_id="run_001",
            status="completed",
            dwc_fields={
                field: {"value": value, "confidence": 0.95}
                for field, value in sample_darwin_core_data.items()
            },
            raw_jsonl_offset=0,  # First line in provenance.jsonl
            timestamp=datetime.now(timezone.utc),
        )
        index.record_extraction(extraction)

        # Verify extraction recorded
        stats = index.get_stats()
        assert stats["extractions"] == 1

    # Verify provenance fragment can be read
    with open(provenance_path) as f:
        fragment_data = json.loads(f.readline())
        assert fragment_data["fragment_id"] == fragment.fragment_id
        assert fragment_data["fragment_type"] == "ocr_extraction"
        assert fragment_data["source"]["identifier"] == image_sha256
        assert fragment_data["process"]["agent"]["identifier"] == "gpt-4o-mini"


def test_full_specimen_workflow_end_to_end(tmp_path, sample_image):
    """Test complete end-to-end specimen workflow from capture to review."""
    image_path, original_sha256 = sample_image
    specimen_id = "AAFC12350_001"

    # Custom Darwin Core data for this specimen
    darwin_core_data = {
        "catalogNumber": "AAFC-12350",  # Match specimen_id
        "scientificName": "Pinus contorta Douglas ex Loudon",
        "family": "Pinaceae",
        "eventDate": "2024-08-15",
        "country": "Canada",
        "stateProvince": "Saskatchewan",
    }

    # Initialize databases
    index = SpecimenIndex(tmp_path / "specimen_index.db")
    provenance_path = tmp_path / "provenance.jsonl"

    try:
        # Step 1: Camera capture (create fragment)
        capture_fragment = ProvenanceFragment(
            fragment_type=FragmentType.CAMERA_CAPTURE,
            source_identifier="DSC_12350.NEF",
            process_operation="camera_capture",
            process_agent_type="human",
            process_agent_id="photographer_001",
            output_identifier=original_sha256,
            output_type="raw_image",
            timestamp=datetime(2024, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
        )

        # Step 2: Register specimen
        index.register_specimen(
            specimen_id=specimen_id,
            camera_filename="DSC_12350.NEF",
            expected_catalog_number="AAFC-12350",
        )

        # Step 3: Register original file
        original = OriginalFile(
            sha256=original_sha256,
            specimen_id=specimen_id,
            file_path=str(image_path),
            format="JPG",
            dimensions=(100, 100),
            size_bytes=image_path.stat().st_size,
            role="original_raw",
            captured_at=datetime(2024, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        index.register_original_file(original)

        # Step 4: Image processing (create transformation fragment)
        processed_sha256 = "processed_" + original_sha256
        processing_fragment = ProvenanceFragment(
            fragment_type=FragmentType.IMAGE_PROCESSING,
            source_identifier=original_sha256,
            process_operation="resize_and_convert",
            process_agent_type="automated",
            process_agent_id="PIL_10.0.0",
            output_identifier=processed_sha256,
            output_type="processed_image",
            timestamp=datetime.now(timezone.utc),
            previous_fragment_id=capture_fragment.fragment_id,
            parameters={"max_dim": 4000, "format": "jpg"},
        )

        transformation = ImageTransformation(
            sha256=processed_sha256,
            specimen_id=specimen_id,
            derived_from=original_sha256,
            operation="resize_and_convert",
            params={"max_dim": 4000, "format": "jpg"},
            timestamp=datetime.now(timezone.utc),
            tool="PIL",
            tool_version="10.0.0",
        )
        index.register_transformation(transformation)

        # Step 5: OCR extraction (create extraction fragment)
        extraction_fragment = create_extraction_fragment(
            image_sha256=processed_sha256,
            darwin_core_data=darwin_core_data,
            batch_id="batch_001",
            model="gpt-4o-mini",
            confidence_scores={field: 0.95 for field in darwin_core_data},
            previous_fragment_id=processing_fragment.fragment_id,
        )

        extraction = ExtractionResult(
            extraction_id="ext_001",
            specimen_id=specimen_id,
            image_sha256=processed_sha256,
            params_hash=index._hash_params({"model": "gpt-4o-mini"}),
            run_id="run_001",
            status="completed",
            dwc_fields={
                field: {"value": value, "confidence": 0.95}
                for field, value in darwin_core_data.items()
            },
            raw_jsonl_offset=2,  # Third fragment in file
            timestamp=datetime.now(timezone.utc),
        )
        index.record_extraction(extraction)

        # Step 6: Aggregate extractions
        aggregation = index.aggregate_specimen_extractions(specimen_id)
        assert aggregation["best_candidates"]["catalogNumber"]["value"] == "AAFC-12350"

        # Step 7: Quality control
        malformed_count = index.check_malformed_catalog_numbers()
        duplicate_count = index.check_catalog_number_duplicates()
        flags = index.get_specimen_flags(specimen_id)

        # Should have no quality issues
        assert malformed_count == 0
        assert duplicate_count == 0
        assert len(flags) == 0

        # Step 8: Write provenance chain
        from src.provenance.fragment import write_provenance_fragments

        write_provenance_fragments(
            [capture_fragment, processing_fragment, extraction_fragment], provenance_path
        )

        # Verify provenance chain
        assert provenance_path.exists()
        fragments = [json.loads(line) for line in provenance_path.read_text().strip().split("\n")]
        assert len(fragments) == 3
        assert fragments[0]["fragment_type"] == "camera_capture"
        assert fragments[1]["fragment_type"] == "image_processing"
        assert fragments[2]["fragment_type"] == "ocr_extraction"
        assert fragments[1]["source"]["previous_fragment_id"] == fragments[0]["fragment_id"]
        assert fragments[2]["source"]["previous_fragment_id"] == fragments[1]["fragment_id"]

        # Verify final statistics
        stats = index.get_stats()
        assert stats["total_specimens"] == 1
        assert stats["original_files"] == 1
        assert stats["transformations"] == 1
        assert stats["extractions"] == 1
        assert stats["unresolved_flags"] == 0

    finally:
        index.close()
