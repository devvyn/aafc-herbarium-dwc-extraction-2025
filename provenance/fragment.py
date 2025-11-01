"""
Provenance Fragment - Immutable lineage records for scientific data.

Each fragment captures:
- Source (what came in)
- Process (what was done)
- Output (what was created)
- Chain (link to previous fragment)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any


class FragmentType(Enum):
    """Processing stages in the herbarium workflow."""

    CAMERA_CAPTURE = "camera_capture"
    IMAGE_PROCESSING = "image_processing"
    IMAGE_PREPROCESSING = "image_preprocessing"  # Grayscale, deskew, contrast, etc.
    OCR_EXTRACTION = "ocr_extraction"
    DWC_EXTRACTION = "dwc_extraction"  # Text/image → Darwin Core fields
    QC_VALIDATION = "qc_validation"  # GBIF verification, duplicate detection
    VALIDATION = "validation"
    PUBLICATION = "publication"


@dataclass
class ProvenanceFragment:
    """Immutable provenance record for one processing stage."""

    fragment_type: FragmentType
    source_identifier: str  # SHA256 hash or manifest reference
    process_operation: str
    process_agent_type: str  # "human", "automated", "ai_model"
    process_agent_id: str
    output_identifier: str  # SHA256 hash of output
    output_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    previous_fragment_id: Optional[str] = None
    batch_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def fragment_id(self) -> str:
        """Generate deterministic fragment ID from content."""
        content = {
            "type": self.fragment_type.value,
            "source": self.source_identifier,
            "process": f"{self.process_operation}:{self.process_agent_id}",
            "output": self.output_identifier,
            "timestamp": self.timestamp.isoformat(),
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Export fragment as JSON-serializable dict."""
        return {
            "fragment_id": self.fragment_id,
            "fragment_type": self.fragment_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": {
                "type": "processed_image"
                if self.fragment_type == FragmentType.OCR_EXTRACTION
                else "raw_image",
                "identifier": self.source_identifier,
                "previous_fragment_id": self.previous_fragment_id,
            },
            "process": {
                "operation": self.process_operation,
                "agent": {"type": self.process_agent_type, "identifier": self.process_agent_id},
                "parameters": self.parameters,
                "batch_id": self.batch_id,
            },
            "output": {
                "type": self.output_type,
                "identifier": self.output_identifier,
                "quality_metrics": self.quality_metrics,
            },
            "metadata": self.metadata,
        }

    def to_jsonl(self) -> str:
        """Export as JSONL line for append-only storage."""
        return json.dumps(self.to_dict())


def create_extraction_fragment(
    image_sha256: str,
    darwin_core_data: Dict[str, Any],
    batch_id: str,
    model: str = "gpt-4o-mini",
    temperature: Optional[float] = None,
    confidence_scores: Optional[Dict[str, float]] = None,
    institution: str = "AAFC",
    previous_fragment_id: Optional[str] = None,
) -> ProvenanceFragment:
    """
    Create provenance fragment for OCR extraction stage.

    Args:
        image_sha256: SHA256 hash of source image
        darwin_core_data: Extracted Darwin Core fields
        batch_id: OpenAI Batch API ID
        model: Model used for extraction
        temperature: Temperature parameter
        confidence_scores: Field-level confidence scores
        institution: Institution code
        previous_fragment_id: Link to previous fragment (e.g., image processing)

    Returns:
        ProvenanceFragment for this extraction
    """
    # Calculate output hash from Darwin Core data
    output_content = json.dumps(darwin_core_data, sort_keys=True)
    output_hash = hashlib.sha256(output_content.encode()).hexdigest()

    # Build parameters
    parameters = {"model": model, "strategy": "few-shot", "response_format": "json_object"}
    if temperature is not None:
        parameters["temperature"] = temperature

    # Build quality metrics
    quality_metrics = {}
    if confidence_scores:
        avg_confidence = (
            sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        )
        quality_metrics["average_confidence"] = avg_confidence
        quality_metrics["field_confidences"] = confidence_scores

    # Build metadata
    metadata = {
        "institution": institution,
        "project": "aafc-herbarium-digitization-2025",
        "compliance": ["DarwinCore", "GBIF", "Federal_Data_Governance"],
        "purpose": "biodiversity_research",
    }

    return ProvenanceFragment(
        fragment_type=FragmentType.OCR_EXTRACTION,
        source_identifier=image_sha256,
        process_operation="ai_vision_extraction",
        process_agent_type="ai_model",
        process_agent_id=model,
        output_identifier=output_hash,
        output_type="darwin_core_record",
        previous_fragment_id=previous_fragment_id,
        batch_id=batch_id,
        parameters=parameters,
        quality_metrics=quality_metrics,
        metadata=metadata,
    )


def create_preprocessing_fragment(
    source_image_sha256: str,
    output_image_sha256: str,
    preprocessing_steps: list[str],
    parameters: Optional[Dict[str, Any]] = None,
    previous_fragment_id: Optional[str] = None,
) -> ProvenanceFragment:
    """
    Create provenance fragment for image preprocessing stage.

    Args:
        source_image_sha256: SHA256 hash of source image
        output_image_sha256: SHA256 hash of preprocessed image
        preprocessing_steps: List of preprocessing operations applied (e.g., ["grayscale", "deskew", "binarize"])
        parameters: Preprocessing parameters (e.g., {"dpi": 300, "contrast_factor": 1.5})
        previous_fragment_id: Link to previous fragment

    Returns:
        ProvenanceFragment for preprocessing
    """
    params = parameters or {}
    params["operations"] = preprocessing_steps

    return ProvenanceFragment(
        fragment_type=FragmentType.IMAGE_PREPROCESSING,
        source_identifier=source_image_sha256,
        process_operation="image_preprocessing",
        process_agent_type="automated",
        process_agent_id="preprocess.py",
        output_identifier=output_image_sha256,
        output_type="preprocessed_image",
        previous_fragment_id=previous_fragment_id,
        parameters=params,
    )


def create_dwc_extraction_fragment(
    source_identifier: str,
    source_type: str,  # "ocr_text" or "image"
    darwin_core_data: Dict[str, Any],
    engine: str,
    engine_version: Optional[str] = None,
    confidence_scores: Optional[Dict[str, float]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    previous_fragment_id: Optional[str] = None,
) -> ProvenanceFragment:
    """
    Create provenance fragment for Darwin Core field extraction.

    Args:
        source_identifier: SHA256 hash of source (OCR text or image)
        source_type: Type of source ("ocr_text" or "image")
        darwin_core_data: Extracted Darwin Core fields
        engine: Extraction engine used (e.g., "gpt-4o-mini", "rules")
        engine_version: Engine version
        confidence_scores: Field-level confidence scores
        parameters: Extraction parameters (e.g., {"temperature": 0.7, "prompt_version": "v2"})
        previous_fragment_id: Link to previous fragment (OCR or preprocessing)

    Returns:
        ProvenanceFragment for DWC extraction
    """
    # Calculate output hash from Darwin Core data
    output_content = json.dumps(darwin_core_data, sort_keys=True)
    output_hash = hashlib.sha256(output_content.encode()).hexdigest()

    # Build parameters
    params = parameters or {}
    params["engine"] = engine
    if engine_version:
        params["engine_version"] = engine_version

    # Build quality metrics
    quality_metrics = {}
    if confidence_scores:
        avg_confidence = (
            sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        )
        quality_metrics["average_confidence"] = avg_confidence
        quality_metrics["field_confidences"] = confidence_scores
        quality_metrics["field_count"] = len(darwin_core_data)

    # Determine agent type
    agent_type = (
        "ai_model" if "gpt" in engine.lower() or "vision" in engine.lower() else "automated"
    )

    return ProvenanceFragment(
        fragment_type=FragmentType.DWC_EXTRACTION,
        source_identifier=source_identifier,
        process_operation=f"dwc_extraction_{source_type}",
        process_agent_type=agent_type,
        process_agent_id=engine,
        output_identifier=output_hash,
        output_type="darwin_core_record",
        previous_fragment_id=previous_fragment_id,
        parameters=params,
        quality_metrics=quality_metrics,
    )


def create_qc_validation_fragment(
    source_dwc_hash: str,
    validated_dwc_data: Dict[str, Any],
    validation_operations: list[str],
    gbif_verification: Optional[Dict[str, Any]] = None,
    flags: Optional[list[str]] = None,
    added_fields: Optional[list[str]] = None,
    previous_fragment_id: Optional[str] = None,
) -> ProvenanceFragment:
    """
    Create provenance fragment for QC validation stage.

    Args:
        source_dwc_hash: SHA256 hash of source Darwin Core data
        validated_dwc_data: Darwin Core data after validation
        validation_operations: List of validation steps (e.g., ["gbif_taxonomy", "duplicate_detection"])
        gbif_verification: GBIF verification metadata
        flags: QC flags raised during validation
        added_fields: Fields added during validation
        previous_fragment_id: Link to previous fragment (DWC extraction)

    Returns:
        ProvenanceFragment for QC validation
    """
    # Calculate output hash
    output_content = json.dumps(validated_dwc_data, sort_keys=True)
    output_hash = hashlib.sha256(output_content.encode()).hexdigest()

    # Build parameters
    parameters = {"operations": validation_operations}
    if added_fields:
        parameters["fields_added"] = added_fields

    # Build quality metrics
    quality_metrics = {}
    if flags:
        quality_metrics["flags"] = flags
        quality_metrics["flag_count"] = len(flags)
    if gbif_verification:
        quality_metrics["gbif_verification"] = gbif_verification

    return ProvenanceFragment(
        fragment_type=FragmentType.QC_VALIDATION,
        source_identifier=source_dwc_hash,
        process_operation="qc_validation",
        process_agent_type="automated",
        process_agent_id="qc/gbif.py",
        output_identifier=output_hash,
        output_type="validated_darwin_core_record",
        previous_fragment_id=previous_fragment_id,
        parameters=parameters,
        quality_metrics=quality_metrics,
    )


def write_provenance_fragments(fragments: list[ProvenanceFragment], output_path: Path) -> None:
    """
    Write provenance fragments to JSONL file (append-only).

    Args:
        fragments: List of provenance fragments
        output_path: Path to provenance.jsonl file
    """
    with open(output_path, "a") as f:
        for fragment in fragments:
            f.write(fragment.to_jsonl() + "\n")
