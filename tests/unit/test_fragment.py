"""Tests for provenance fragment functionality."""

import json
import pytest
from datetime import datetime

from provenance.fragment import (
    FragmentType,
    ProvenanceFragment,
    create_extraction_fragment,
    write_provenance_fragments,
)


@pytest.fixture
def sample_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2025, 1, 15, 12, 30, 45)


@pytest.fixture
def sample_fragment(sample_timestamp):
    """Provide a sample provenance fragment for testing."""
    return ProvenanceFragment(
        fragment_type=FragmentType.OCR_EXTRACTION,
        source_identifier="abc123" * 10,  # SHA256-like string
        process_operation="ai_vision_extraction",
        process_agent_type="ai_model",
        process_agent_id="gpt-4o-mini",
        output_identifier="def456" * 10,
        output_type="darwin_core_record",
        timestamp=sample_timestamp,
        previous_fragment_id="previous123" * 10,
        batch_id="batch_001",
        parameters={"model": "gpt-4o-mini", "temperature": 0.7},
        quality_metrics={"average_confidence": 0.85},
        metadata={"institution": "AAFC"},
    )


def test_fragment_type_enum():
    """Test FragmentType enum values."""
    assert FragmentType.CAMERA_CAPTURE.value == "camera_capture"
    assert FragmentType.IMAGE_PROCESSING.value == "image_processing"
    assert FragmentType.OCR_EXTRACTION.value == "ocr_extraction"
    assert FragmentType.VALIDATION.value == "validation"
    assert FragmentType.PUBLICATION.value == "publication"


def test_provenance_fragment_init(sample_timestamp):
    """Test ProvenanceFragment initialization."""
    fragment = ProvenanceFragment(
        fragment_type=FragmentType.CAMERA_CAPTURE,
        source_identifier="original_file.nef",
        process_operation="camera_capture",
        process_agent_type="human",
        process_agent_id="photographer_001",
        output_identifier="raw_image_sha256",
        output_type="raw_image",
        timestamp=sample_timestamp,
    )

    assert fragment.fragment_type == FragmentType.CAMERA_CAPTURE
    assert fragment.source_identifier == "original_file.nef"
    assert fragment.process_operation == "camera_capture"
    assert fragment.process_agent_type == "human"
    assert fragment.process_agent_id == "photographer_001"
    assert fragment.output_identifier == "raw_image_sha256"
    assert fragment.output_type == "raw_image"
    assert fragment.timestamp == sample_timestamp
    assert fragment.previous_fragment_id is None
    assert fragment.batch_id is None
    assert fragment.parameters == {}
    assert fragment.quality_metrics == {}
    assert fragment.metadata == {}


def test_fragment_id_determinism(sample_timestamp):
    """Test fragment_id is deterministic for same content."""
    fragment1 = ProvenanceFragment(
        fragment_type=FragmentType.OCR_EXTRACTION,
        source_identifier="source_hash",
        process_operation="extraction",
        process_agent_type="ai_model",
        process_agent_id="gpt-4o-mini",
        output_identifier="output_hash",
        output_type="darwin_core",
        timestamp=sample_timestamp,
    )

    fragment2 = ProvenanceFragment(
        fragment_type=FragmentType.OCR_EXTRACTION,
        source_identifier="source_hash",
        process_operation="extraction",
        process_agent_type="ai_model",
        process_agent_id="gpt-4o-mini",
        output_identifier="output_hash",
        output_type="darwin_core",
        timestamp=sample_timestamp,
    )

    # Same content should produce same ID
    assert fragment1.fragment_id == fragment2.fragment_id

    # Different timestamp should produce different ID
    fragment3 = ProvenanceFragment(
        fragment_type=FragmentType.OCR_EXTRACTION,
        source_identifier="source_hash",
        process_operation="extraction",
        process_agent_type="ai_model",
        process_agent_id="gpt-4o-mini",
        output_identifier="output_hash",
        output_type="darwin_core",
        timestamp=datetime(2025, 1, 15, 13, 0, 0),  # Different time
    )
    assert fragment1.fragment_id != fragment3.fragment_id


def test_fragment_id_is_sha256_hash(sample_fragment):
    """Test fragment_id is a valid SHA256 hash."""
    fragment_id = sample_fragment.fragment_id

    # SHA256 hash is 64 hex characters
    assert len(fragment_id) == 64
    assert all(c in "0123456789abcdef" for c in fragment_id)


def test_to_dict_structure(sample_fragment):
    """Test to_dict produces correct structure."""
    data = sample_fragment.to_dict()

    # Top-level keys
    assert "fragment_id" in data
    assert "fragment_type" in data
    assert "timestamp" in data
    assert "source" in data
    assert "process" in data
    assert "output" in data
    assert "metadata" in data

    # Fragment metadata
    assert data["fragment_type"] == "ocr_extraction"
    assert data["timestamp"] == "2025-01-15T12:30:45"

    # Source structure
    assert data["source"]["type"] == "processed_image"
    assert data["source"]["identifier"] == sample_fragment.source_identifier
    assert data["source"]["previous_fragment_id"] == sample_fragment.previous_fragment_id

    # Process structure
    assert data["process"]["operation"] == "ai_vision_extraction"
    assert data["process"]["agent"]["type"] == "ai_model"
    assert data["process"]["agent"]["identifier"] == "gpt-4o-mini"
    assert data["process"]["parameters"] == {"model": "gpt-4o-mini", "temperature": 0.7}
    assert data["process"]["batch_id"] == "batch_001"

    # Output structure
    assert data["output"]["type"] == "darwin_core_record"
    assert data["output"]["identifier"] == sample_fragment.output_identifier
    assert data["output"]["quality_metrics"] == {"average_confidence": 0.85}


def test_to_dict_source_type_for_camera_capture(sample_timestamp):
    """Test to_dict sets source type to raw_image for non-OCR fragments."""
    fragment = ProvenanceFragment(
        fragment_type=FragmentType.CAMERA_CAPTURE,
        source_identifier="camera_file.nef",
        process_operation="capture",
        process_agent_type="human",
        process_agent_id="photographer",
        output_identifier="image_hash",
        output_type="raw_image",
        timestamp=sample_timestamp,
    )

    data = fragment.to_dict()
    assert data["source"]["type"] == "raw_image"


def test_to_jsonl_format(sample_fragment):
    """Test to_jsonl produces valid JSONL."""
    jsonl = sample_fragment.to_jsonl()

    # Should be single-line JSON
    assert "\n" not in jsonl

    # Should be parseable as JSON
    data = json.loads(jsonl)
    assert data["fragment_id"] == sample_fragment.fragment_id
    assert data["fragment_type"] == "ocr_extraction"


def test_create_extraction_fragment_basic():
    """Test create_extraction_fragment with basic parameters."""
    image_sha256 = "a" * 64
    darwin_core_data = {
        "catalogNumber": "AAFC-12345",
        "scientificName": "Plantae specimen",
    }
    batch_id = "batch_001"

    fragment = create_extraction_fragment(
        image_sha256=image_sha256,
        darwin_core_data=darwin_core_data,
        batch_id=batch_id,
    )

    assert fragment.fragment_type == FragmentType.OCR_EXTRACTION
    assert fragment.source_identifier == image_sha256
    assert fragment.process_operation == "ai_vision_extraction"
    assert fragment.process_agent_type == "ai_model"
    assert fragment.process_agent_id == "gpt-4o-mini"  # Default model
    assert fragment.output_type == "darwin_core_record"
    assert fragment.batch_id == batch_id
    assert fragment.previous_fragment_id is None

    # Check parameters
    assert fragment.parameters["model"] == "gpt-4o-mini"
    assert fragment.parameters["strategy"] == "few-shot"
    assert fragment.parameters["response_format"] == "json_object"
    assert "temperature" not in fragment.parameters  # Not set

    # Check metadata
    assert fragment.metadata["institution"] == "AAFC"
    assert fragment.metadata["project"] == "aafc-herbarium-digitization-2025"
    assert "DarwinCore" in fragment.metadata["compliance"]
    assert "GBIF" in fragment.metadata["compliance"]


def test_create_extraction_fragment_with_temperature():
    """Test create_extraction_fragment includes temperature when provided."""
    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
        temperature=0.7,
    )

    assert fragment.parameters["temperature"] == 0.7


def test_create_extraction_fragment_with_custom_model():
    """Test create_extraction_fragment with custom model."""
    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
        model="gpt-4o",
    )

    assert fragment.process_agent_id == "gpt-4o"
    assert fragment.parameters["model"] == "gpt-4o"


def test_create_extraction_fragment_with_confidence_scores():
    """Test create_extraction_fragment calculates quality metrics from confidence scores."""
    confidence_scores = {
        "catalogNumber": 0.95,
        "scientificName": 0.85,
        "eventDate": 0.75,
    }

    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={
            "catalogNumber": "AAFC-12345",
            "scientificName": "Plantae specimen",
            "eventDate": "2024-03-15",
        },
        batch_id="batch_001",
        confidence_scores=confidence_scores,
    )

    # Check quality metrics
    assert "average_confidence" in fragment.quality_metrics
    assert "field_confidences" in fragment.quality_metrics

    # Average should be (0.95 + 0.85 + 0.75) / 3 = 0.85
    assert fragment.quality_metrics["average_confidence"] == pytest.approx(0.85)
    assert fragment.quality_metrics["field_confidences"] == confidence_scores


def test_create_extraction_fragment_with_custom_institution():
    """Test create_extraction_fragment with custom institution."""
    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "TEST-12345"},
        batch_id="batch_001",
        institution="TEST_INST",
    )

    assert fragment.metadata["institution"] == "TEST_INST"


def test_create_extraction_fragment_with_previous_fragment():
    """Test create_extraction_fragment links to previous fragment."""
    previous_id = "b" * 64

    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
        previous_fragment_id=previous_id,
    )

    assert fragment.previous_fragment_id == previous_id


def test_create_extraction_fragment_output_hash_determinism():
    """Test create_extraction_fragment produces same output hash for same data."""
    darwin_core_data = {
        "catalogNumber": "AAFC-12345",
        "scientificName": "Plantae specimen",
    }

    fragment1 = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data=darwin_core_data,
        batch_id="batch_001",
    )

    fragment2 = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data=darwin_core_data,
        batch_id="batch_001",
    )

    # Same Darwin Core data should produce same output hash
    assert fragment1.output_identifier == fragment2.output_identifier


def test_write_provenance_fragments_creates_file(tmp_path):
    """Test write_provenance_fragments creates JSONL file."""
    output_path = tmp_path / "provenance.jsonl"

    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
    )

    write_provenance_fragments([fragment], output_path)

    assert output_path.exists()


def test_write_provenance_fragments_appends(tmp_path):
    """Test write_provenance_fragments appends to existing file."""
    output_path = tmp_path / "provenance.jsonl"

    fragment1 = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-001"},
        batch_id="batch_001",
    )

    fragment2 = create_extraction_fragment(
        image_sha256="b" * 64,
        darwin_core_data={"catalogNumber": "AAFC-002"},
        batch_id="batch_002",
    )

    # Write first fragment
    write_provenance_fragments([fragment1], output_path)

    # Append second fragment
    write_provenance_fragments([fragment2], output_path)

    # Read all lines
    lines = output_path.read_text().strip().split("\n")
    assert len(lines) == 2

    # Verify both fragments are present
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])
    assert data1["fragment_id"] == fragment1.fragment_id
    assert data2["fragment_id"] == fragment2.fragment_id


def test_write_provenance_fragments_multiple(tmp_path):
    """Test write_provenance_fragments with multiple fragments at once."""
    output_path = tmp_path / "provenance.jsonl"

    fragments = [
        create_extraction_fragment(
            image_sha256=f"{chr(97 + i)}" * 64,
            darwin_core_data={"catalogNumber": f"AAFC-{i:05d}"},
            batch_id=f"batch_{i:03d}",
        )
        for i in range(5)
    ]

    write_provenance_fragments(fragments, output_path)

    # Verify all fragments written
    lines = output_path.read_text().strip().split("\n")
    assert len(lines) == 5

    # Verify each fragment is valid JSON
    for i, line in enumerate(lines):
        data = json.loads(line)
        assert data["fragment_id"] == fragments[i].fragment_id


def test_fragment_chain_linking(sample_timestamp):
    """Test creating a chain of linked fragments."""
    # Fragment 1: Camera capture
    fragment1 = ProvenanceFragment(
        fragment_type=FragmentType.CAMERA_CAPTURE,
        source_identifier="camera_file.nef",
        process_operation="capture",
        process_agent_type="human",
        process_agent_id="photographer_001",
        output_identifier="raw_image_hash",
        output_type="raw_image",
        timestamp=sample_timestamp,
    )

    # Fragment 2: Image processing (links to fragment 1)
    fragment2 = ProvenanceFragment(
        fragment_type=FragmentType.IMAGE_PROCESSING,
        source_identifier=fragment1.output_identifier,
        process_operation="color_correction",
        process_agent_type="automated",
        process_agent_id="imagemagick_v7",
        output_identifier="processed_image_hash",
        output_type="processed_image",
        timestamp=sample_timestamp,
        previous_fragment_id=fragment1.fragment_id,
    )

    # Fragment 3: OCR extraction (links to fragment 2)
    fragment3 = create_extraction_fragment(
        image_sha256=fragment2.output_identifier,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
        previous_fragment_id=fragment2.fragment_id,
    )

    # Verify chain
    assert fragment2.previous_fragment_id == fragment1.fragment_id
    assert fragment3.previous_fragment_id == fragment2.fragment_id

    # Verify source identifiers link to previous outputs
    assert fragment2.source_identifier == fragment1.output_identifier
    assert fragment3.source_identifier == fragment2.output_identifier


def test_fragment_quality_metrics_empty_confidence_scores():
    """Test create_extraction_fragment with empty confidence scores."""
    fragment = create_extraction_fragment(
        image_sha256="a" * 64,
        darwin_core_data={"catalogNumber": "AAFC-12345"},
        batch_id="batch_001",
        confidence_scores={},
    )

    # Empty confidence scores should result in no quality metrics
    assert fragment.quality_metrics == {}


def test_fragment_serialization_roundtrip(sample_fragment):
    """Test fragment can be serialized and deserialized."""
    # Serialize to dict
    data = sample_fragment.to_dict()

    # Serialize to JSON
    json_str = json.dumps(data)

    # Deserialize
    loaded_data = json.loads(json_str)

    # Verify key fields preserved
    assert loaded_data["fragment_id"] == sample_fragment.fragment_id
    assert loaded_data["fragment_type"] == sample_fragment.fragment_type.value
    assert loaded_data["source"]["identifier"] == sample_fragment.source_identifier
    assert loaded_data["output"]["identifier"] == sample_fragment.output_identifier
