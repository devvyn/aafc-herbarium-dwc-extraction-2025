"""Contextual GPT Engine for Herbarium Specimen Processing

This module implements a sophisticated GPT-based engine specifically designed
for herbarium specimen digitization. It leverages GPT-4o-mini's superior
contextual understanding to:

- Intelligently ignore ColorChecker calibration cards
- Focus on specimen labels and botanical information
- Parse complex, multi-layered label information
- Extract scientific citations and verification data
- Handle partially covered and irregular formatting
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from .. import register_task
from ..errors import EngineError
from ..protocols import ImageToTextEngine

try:
    import openai
except ImportError:
    openai = None


@dataclass
class HerbariumContext:
    """Context configuration for herbarium specimen processing."""

    # Focus areas for extraction
    focus_areas: List[str] = None
    ignore_elements: List[str] = None

    # Scientific data priorities
    extract_taxonomy: bool = True
    extract_locality: bool = True
    extract_collector_info: bool = True
    extract_dates: bool = True
    extract_identifications: bool = True
    extract_annotations: bool = True

    # Quality expectations
    require_scientific_names: bool = True
    validate_taxonomic_hierarchy: bool = False
    extract_coordinates: bool = True

    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = [
                "specimen labels",
                "collection data",
                "determination labels",
                "annotation slips",
                "verification labels",
                "handwritten notes",
                "printed institutional labels"
            ]

        if self.ignore_elements is None:
            self.ignore_elements = [
                "ColorChecker calibration cards",
                "color reference charts",
                "rulers and scale bars",
                "background mounting paper",
                "institutional watermarks",
                "camera metadata overlays",
                "photographer information"
            ]


class HerbariumGPTEngine:
    """GPT-4o-mini engine optimized for herbarium specimen processing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        context: Optional[HerbariumContext] = None
    ):
        if openai is None:
            raise EngineError(
                "MISSING_DEPENDENCY",
                "openai package required for GPT processing"
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.context = context or HerbariumContext()
        self.logger = logging.getLogger(__name__)

    def process_specimen_image(
        self,
        image_path: Path,
        extraction_focus: Optional[str] = None,
        max_tokens: int = 1500
    ) -> Tuple[str, List[float]]:
        """Process herbarium specimen image with contextual understanding."""

        try:
            # Encode image
            encoded_image = self._encode_image(image_path)

            # Generate contextual prompt
            prompt = self._create_herbarium_prompt(extraction_focus)

            # Call GPT-4o-mini
            response = self._call_gpt_vision(encoded_image, prompt, max_tokens)

            # Parse response and extract confidence indicators
            text, confidence = self._parse_response(response)

            return text, confidence

        except Exception as e:
            raise EngineError("GPT_PROCESSING_ERROR", str(e)) from e

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 for GPT Vision."""
        with image_path.open("rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_herbarium_prompt(self, extraction_focus: Optional[str] = None) -> str:
        """Create comprehensive herbarium-specific prompt."""

        base_prompt = """You are an expert botanical digitization specialist analyzing a herbarium specimen image. Your task is to extract ALL textual information from specimen labels while intelligently ignoring non-specimen elements.

IGNORE THESE ELEMENTS (do not extract text from):
- ColorChecker calibration cards or color reference charts
- Rulers, scale bars, or measurement tools
- Background mounting paper or institutional watermarks
- Camera metadata, timestamps, or photographer information
- Any technical photography equipment visible in the image

FOCUS ON THESE SPECIMEN-RELATED ELEMENTS:
- Primary specimen identification labels
- Collection data labels (collector, date, locality)
- Determination/identification labels (who identified the specimen)
- Annotation slips or verification labels
- Handwritten notes or corrections
- Any text directly related to the botanical specimen

EXTRACTION REQUIREMENTS:

1. TAXONOMIC INFORMATION:
   - Scientific names (genus, species, subspecies, varieties)
   - Family names
   - Common names if present
   - Author citations (e.g., "L." for Linnaeus)

2. COLLECTION DATA:
   - Collector name(s) and collection numbers
   - Collection date (any format)
   - Geographic locality (country, state, specific location)
   - Habitat description
   - Elevation or coordinates if present

3. IDENTIFICATION/DETERMINATION:
   - Who determined/identified the specimen ("Det." or "Determined by")
   - When the identification was made
   - Any verification or revision information

4. ADDITIONAL ANNOTATIONS:
   - Updates, corrections, or notes
   - Institutional information
   - Catalog or accession numbers
   - Any other relevant specimen data

SPECIAL HANDLING:
- Parse overlapping or partially obscured labels carefully
- Distinguish between original labels and later annotations
- Handle multiple identification labels (revisions/updates)
- Extract text even if handwriting is irregular or labels are at angles
- Indicate uncertainty with [?] for unclear text
- Separate different types of information clearly

"""

        if extraction_focus:
            base_prompt += f"\nSPECIAL FOCUS: Pay particular attention to {extraction_focus}.\n"

        if self.context.extract_taxonomy:
            base_prompt += "\nPrioritize complete taxonomic information including author citations.\n"

        if self.context.extract_coordinates:
            base_prompt += "\nLook carefully for coordinates in any format (decimal degrees, DMS, etc.).\n"

        base_prompt += """
OUTPUT FORMAT:
Provide the extracted text in a structured format:

TAXONOMY:
[Scientific names, family, authorities]

COLLECTION:
[Collector, number, date, locality details]

IDENTIFICATION:
[Determiner, determination date, verification info]

ANNOTATIONS:
[Any additional notes, corrections, institutional data]

RAW_TEXT:
[All text extracted, preserving original formatting where possible]

If any category has no information, write "None found" for that section.
"""

        return base_prompt

    def _call_gpt_vision(self, encoded_image: str, prompt: str, max_tokens: int) -> Dict:
        """Call GPT-4o-mini Vision API with herbarium-specific parameters."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}",
                                    "detail": "high"  # High detail for specimen labels
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.1,  # Low temperature for consistent extraction
                top_p=0.9
            )

            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": response.usage._asdict() if response.usage else {},
                "model": response.model
            }

        except Exception as e:
            self.logger.error(f"GPT API call failed: {e}")
            raise EngineError("GPT_API_ERROR", str(e)) from e

    def _parse_response(self, response: Dict) -> Tuple[str, List[float]]:
        """Parse GPT response and estimate confidence levels."""

        content = response.get("content", "")
        if not content:
            return "", [0.0]

        # Estimate confidence based on response characteristics
        confidence_indicators = self._assess_response_confidence(content, response)

        # Extract structured information
        structured_text = self._structure_extracted_data(content)

        return structured_text, confidence_indicators

    def _assess_response_confidence(self, content: str, response: Dict) -> List[float]:
        """Assess confidence in GPT extraction based on response characteristics."""

        confidence_factors = []

        # Response completeness factor
        if len(content.strip()) > 100:
            confidence_factors.append(0.9)
        elif len(content.strip()) > 50:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)

        # Structured format compliance
        expected_sections = ["TAXONOMY:", "COLLECTION:", "IDENTIFICATION:", "RAW_TEXT:"]
        found_sections = sum(1 for section in expected_sections if section in content)
        structure_score = found_sections / len(expected_sections)
        confidence_factors.append(structure_score)

        # Scientific content indicators
        scientific_patterns = [
            r'\b[A-Z][a-z]+\s+[a-z]+\b',  # Binomial nomenclature
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # Dates
            r'[A-Z][a-z]+\s+(det\.|determined)',  # Determination info
            r'(coll\.|leg\.|collector)',  # Collection info
        ]

        pattern_matches = sum(1 for pattern in scientific_patterns
                            if re.search(pattern, content, re.IGNORECASE))
        scientific_score = min(pattern_matches / len(scientific_patterns), 1.0)
        confidence_factors.append(scientific_score)

        # Uncertainty indicators (lower confidence if many [?] markers)
        uncertainty_count = content.count('[?]')
        uncertainty_penalty = max(0.0, 1.0 - (uncertainty_count * 0.1))
        confidence_factors.append(uncertainty_penalty)

        # API response quality indicators
        if response.get("finish_reason") == "stop":
            confidence_factors.append(0.95)
        elif response.get("finish_reason") == "length":
            confidence_factors.append(0.8)  # Truncated response
        else:
            confidence_factors.append(0.6)

        # Generate token-level confidence estimates
        # (Simplified - in practice, could be more sophisticated)
        avg_confidence = sum(confidence_factors) / len(confidence_factors)
        token_count = len(content.split())

        return [avg_confidence] * max(1, token_count)

    def _structure_extracted_data(self, content: str) -> str:
        """Structure the extracted data for downstream processing."""

        # If already structured, return as-is
        if "TAXONOMY:" in content and "COLLECTION:" in content:
            return content

        # Otherwise, attempt basic structuring
        lines = content.strip().split('\n')
        structured_lines = []

        current_section = "RAW_TEXT"
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to identify content types
            if re.search(r'\b[A-Z][a-z]+\s+[a-z]+\b', line):
                if current_section != "TAXONOMY":
                    structured_lines.append("\nTAXONOMY:")
                    current_section = "TAXONOMY"

            elif re.search(r'(coll|leg|collector|det|determined)', line, re.IGNORECASE):
                if current_section not in ["COLLECTION", "IDENTIFICATION"]:
                    structured_lines.append("\nCOLLECTION:")
                    current_section = "COLLECTION"

            structured_lines.append(line)

        return '\n'.join(structured_lines)


def image_to_text(
    image: Path,
    extraction_focus: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    context: Optional[HerbariumContext] = None
) -> Tuple[str, List[float]]:
    """Extract text from herbarium specimen image using contextual GPT processing.

    Parameters
    ----------
    image:
        Path to the herbarium specimen image.
    extraction_focus:
        Optional focus area (e.g., "taxonomic information", "collection data").
    api_key:
        OpenAI API key (if not set in environment).
    model:
        GPT model to use (default: gpt-4o-mini).
    context:
        Herbarium-specific context configuration.

    Returns
    -------
    Tuple[str, List[float]]
        Extracted text and confidence scores.
    """

    engine = HerbariumGPTEngine(api_key=api_key, model=model, context=context)
    return engine.process_specimen_image(image, extraction_focus)


# Register the task
register_task("image_to_text", "gpt_herbarium", __name__, "image_to_text")

# Type checking
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text", "HerbariumGPTEngine", "HerbariumContext"]