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
    OCR_EXTRACTION = "ocr_extraction"
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
            "timestamp": self.timestamp.isoformat()
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
                "type": "processed_image" if self.fragment_type == FragmentType.OCR_EXTRACTION else "raw_image",
                "identifier": self.source_identifier,
                "previous_fragment_id": self.previous_fragment_id
            },
            "process": {
                "operation": self.process_operation,
                "agent": {
                    "type": self.process_agent_type,
                    "identifier": self.process_agent_id
                },
                "parameters": self.parameters,
                "batch_id": self.batch_id
            },
            "output": {
                "type": self.output_type,
                "identifier": self.output_identifier,
                "quality_metrics": self.quality_metrics
            },
            "metadata": self.metadata
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
    previous_fragment_id: Optional[str] = None
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
    parameters = {
        "model": model,
        "strategy": "few-shot",
        "response_format": "json_object"
    }
    if temperature is not None:
        parameters["temperature"] = temperature

    # Build quality metrics
    quality_metrics = {}
    if confidence_scores:
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        quality_metrics["average_confidence"] = avg_confidence
        quality_metrics["field_confidences"] = confidence_scores

    # Build metadata
    metadata = {
        "institution": institution,
        "project": "aafc-herbarium-digitization-2025",
        "compliance": ["DarwinCore", "GBIF", "Federal_Data_Governance"],
        "purpose": "biodiversity_research"
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
        metadata=metadata
    )


def write_provenance_fragments(
    fragments: list[ProvenanceFragment],
    output_path: Path
) -> None:
    """
    Write provenance fragments to JSONL file (append-only).

    Args:
        fragments: List of provenance fragments
        output_path: Path to provenance.jsonl file
    """
    with open(output_path, "a") as f:
        for fragment in fragments:
            f.write(fragment.to_jsonl() + "\n")
