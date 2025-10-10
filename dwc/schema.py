from __future__ import annotations

import logging
import urllib.request
import urllib.error
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

DEFAULT_SCHEMA_URI = "http://rs.tdwg.org/dwc/terms/"

# Official schema sources
OFFICIAL_DWC_SCHEMA_URLS = {
    "simple": "http://rs.tdwg.org/dwc/xsd/tdwg_dwc_simple.xsd",
    "terms": "http://rs.tdwg.org/dwc/xsd/tdwg_dwcterms.xsd",
    "classes": "http://rs.tdwg.org/dwc/xsd/tdwg_dwc_class_terms.xsd",
}

OFFICIAL_ABCD_SCHEMA_URLS = {
    "abcd_206": "https://abcd.tdwg.org/xml/ABCD_2.06.xsd",
    "abcd_206d": "https://abcd.tdwg.org/xml/ABCD_2.06d.xsd",
}

# Project-specific terms appended after schema loading
PROJECT_TERMS = [
    "scientificName_verbatim",
    "verbatimEventDate",
    "eventDateUncertaintyInDays",
    "datasetName",
    "verbatimLabel",
    "flags",
]


class SchemaType(Enum):
    """Enumeration of supported schema types."""

    DWC = "dwc"
    ABCD = "abcd"
    CUSTOM = "custom"


@dataclass
class SchemaInfo:
    """Information about a parsed schema."""

    name: str
    version: str
    namespace: str
    terms: List[str]
    source_url: Optional[str] = None
    last_updated: Optional[datetime] = None
    schema_type: SchemaType = SchemaType.CUSTOM


@dataclass
class TermDefinition:
    """Definition of a schema term with metadata."""

    name: str
    namespace: str
    description: Optional[str] = None
    data_type: Optional[str] = None
    required: bool = False
    deprecated: bool = False
    source_schema: Optional[str] = None


def resolve_term(term: str) -> str:
    """Return the local Darwin Core term from a URI or prefixed name."""

    if term.startswith("http://") or term.startswith("https://"):
        term = term.rstrip("/").split("/")[-1]
    if ":" in term:
        term = term.split(":", 1)[1]
    return term


def _parse_schema(path: Path) -> List[str]:
    """Parse a local schema file and extract element names."""
    terms: List[str] = []
    try:
        tree = ET.parse(path)
    except Exception:  # pragma: no cover - malformed schemas
        return terms
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    for elem in tree.findall(".//xs:element", ns):
        name = elem.get("name")
        if name:
            terms.append(name)
    return terms


def _fetch_schema_from_url(url: str, timeout: int = 30) -> Optional[ET.Element]:
    """Fetch and parse an XML schema from a URL."""
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Fetching schema from {url}")
        with urllib.request.urlopen(url, timeout=timeout) as response:
            content = response.read()
            return ET.fromstring(content)
    except (urllib.error.URLError, ET.ParseError) as e:
        logger.error(f"Failed to fetch or parse schema from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching schema from {url}: {e}")
        return None


def _parse_schema_xml(root: ET.Element) -> SchemaInfo:
    """Parse an XML schema element and extract detailed information."""
    ns = {
        "xs": "http://www.w3.org/2001/XMLSchema",
        "dwc": "http://rs.tdwg.org/dwc/terms/",
        "abcd": "http://www.bgbm.org/TDWG/2005/ABCD/",
    }

    # Extract basic schema information
    target_namespace = root.get("targetNamespace", "")
    version = root.get("version", "unknown")

    # Determine schema type based on namespace
    schema_type = SchemaType.CUSTOM
    if "dwc" in target_namespace or "darwin" in target_namespace.lower():
        schema_type = SchemaType.DWC
    elif "abcd" in target_namespace or "bgbm" in target_namespace:
        schema_type = SchemaType.ABCD

    # Extract terms
    terms: List[str] = []
    term_definitions: List[TermDefinition] = []

    for elem in root.findall(".//xs:element", ns):
        name = elem.get("name")
        if name:
            terms.append(name)

            # Extract additional metadata
            elem_type = elem.get("type", "xs:string")
            min_occurs = elem.get("minOccurs", "0")
            deprecated = elem.get("deprecated", "false").lower() == "true"

            # Try to extract documentation
            doc_elem = elem.find(".//xs:documentation", ns)
            description = doc_elem.text if doc_elem is not None else None

            term_def = TermDefinition(
                name=name,
                namespace=target_namespace,
                description=description,
                data_type=elem_type,
                required=min_occurs != "0",
                deprecated=deprecated,
            )
            term_definitions.append(term_def)

    return SchemaInfo(
        name=f"{schema_type.value}_schema",
        version=version,
        namespace=target_namespace,
        terms=terms,
        last_updated=datetime.now(),
        schema_type=schema_type,
    )


def load_schema_terms(schema_files: Optional[Iterable[Path]] = None) -> List[str]:
    """Load Darwin Core/ABCD terms from the given schema files."""

    if not schema_files:
        base = resources.files("config").joinpath("schemas")
        schema_files = [base / "dwc.xsd", base / "abcd.xsd"]
    terms: List[str] = []
    for path in schema_files:
        if path.exists():
            terms.extend(_parse_schema(path))
    return terms + PROJECT_TERMS


def fetch_official_schemas(
    use_cache: bool = True, cache_dir: Optional[Path] = None
) -> Dict[str, SchemaInfo]:
    """Fetch and parse official Darwin Core and ABCD schemas.

    Args:
        use_cache: Whether to cache downloaded schemas locally
        cache_dir: Directory to store cached schemas (defaults to config/schemas/cache)

    Returns:
        Dictionary mapping schema names to SchemaInfo objects
    """
    logger = logging.getLogger(__name__)
    schemas: Dict[str, SchemaInfo] = {}

    if cache_dir is None:
        cache_dir = resources.files("config").joinpath("schemas", "cache")
        cache_dir = Path(str(cache_dir))

    # Ensure cache directory exists
    if use_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)

    # Fetch DwC schemas
    for schema_name, url in OFFICIAL_DWC_SCHEMA_URLS.items():
        cache_file = cache_dir / f"dwc_{schema_name}.xsd" if use_cache else None

        # Try to load from cache first
        if use_cache and cache_file and cache_file.exists():
            try:
                tree = ET.parse(cache_file)
                root = tree.getroot()
                logger.info(f"Loaded DwC schema '{schema_name}' from cache")
            except ET.ParseError:
                logger.warning(f"Cache file {cache_file} is corrupted, re-fetching")
                root = _fetch_schema_from_url(url)
        else:
            root = _fetch_schema_from_url(url)

        if root is not None:
            # Cache the schema if requested
            if use_cache and cache_file:
                try:
                    tree = ET.ElementTree(root)
                    tree.write(cache_file, encoding="utf-8", xml_declaration=True)
                    logger.info(f"Cached DwC schema '{schema_name}' to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to cache schema: {e}")

            schema_info = _parse_schema_xml(root)
            schema_info.name = f"dwc_{schema_name}"
            schema_info.source_url = url
            schemas[f"dwc_{schema_name}"] = schema_info

    # Fetch ABCD schemas
    for schema_name, url in OFFICIAL_ABCD_SCHEMA_URLS.items():
        cache_file = cache_dir / f"{schema_name}.xsd" if use_cache else None

        # Try to load from cache first
        if use_cache and cache_file and cache_file.exists():
            try:
                tree = ET.parse(cache_file)
                root = tree.getroot()
                logger.info(f"Loaded ABCD schema '{schema_name}' from cache")
            except ET.ParseError:
                logger.warning(f"Cache file {cache_file} is corrupted, re-fetching")
                root = _fetch_schema_from_url(url)
        else:
            root = _fetch_schema_from_url(url)

        if root is not None:
            # Cache the schema if requested
            if use_cache and cache_file:
                try:
                    tree = ET.ElementTree(root)
                    tree.write(cache_file, encoding="utf-8", xml_declaration=True)
                    logger.info(f"Cached ABCD schema '{schema_name}' to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to cache schema: {e}")

            schema_info = _parse_schema_xml(root)
            schema_info.name = schema_name
            schema_info.source_url = url
            schemas[schema_name] = schema_info

    return schemas


def load_schema_terms_from_official_sources(
    preferred_schemas: Optional[List[str]] = None,
) -> List[str]:
    """Load terms from official Darwin Core and ABCD schema sources.

    Args:
        preferred_schemas: List of schema names to use (e.g., ['dwc_simple', 'abcd_206'])
                          If None, uses all available schemas

    Returns:
        List of unique term names from the specified schemas
    """
    logger = logging.getLogger(__name__)

    try:
        official_schemas = fetch_official_schemas()

        if not official_schemas:
            logger.warning("No official schemas could be loaded, falling back to local schemas")
            return load_schema_terms()

        # Use specified schemas or all available
        if preferred_schemas:
            schemas_to_use = {
                name: schema
                for name, schema in official_schemas.items()
                if name in preferred_schemas
            }
        else:
            schemas_to_use = official_schemas

        # Collect all terms
        all_terms = set()
        for schema_name, schema_info in schemas_to_use.items():
            logger.info(
                f"Loading terms from schema: {schema_name} ({len(schema_info.terms)} terms)"
            )
            all_terms.update(schema_info.terms)

        # Convert to sorted list and add project terms
        terms_list = sorted(list(all_terms))
        return terms_list + PROJECT_TERMS

    except Exception as e:
        logger.error(f"Failed to load official schemas: {e}")
        logger.info("Falling back to local schema files")
        return load_schema_terms()


# Darwin Core terms supported by this project.  These mirror the column order
# used when writing CSV output.  The list is based on the AAFC-SRDC example
# dataset and extended with a few project-specific fields at the end.
DWC_TERMS = load_schema_terms()


def configure_terms(schema_files: Iterable[Path]) -> None:
    """Override ``DWC_TERMS`` using alternative schema files."""

    global DWC_TERMS
    DWC_TERMS = load_schema_terms(schema_files)


def configure_terms_from_official_sources(preferred_schemas: Optional[List[str]] = None) -> None:
    """Override ``DWC_TERMS`` using official schema sources.

    Args:
        preferred_schemas: List of schema names to use (e.g., ['dwc_simple', 'abcd_206'])
    """
    global DWC_TERMS
    DWC_TERMS = load_schema_terms_from_official_sources(preferred_schemas)


def validate_schema_compatibility(
    terms: List[str], target_schemas: List[str]
) -> Dict[str, List[str]]:
    """Validate terms against target schemas and report compatibility issues.

    Args:
        terms: List of terms to validate
        target_schemas: List of schema names to validate against

    Returns:
        Dictionary with validation results:
        - 'valid': Terms found in target schemas
        - 'invalid': Terms not found in any target schema
        - 'deprecated': Terms marked as deprecated in schemas
    """
    logger = logging.getLogger(__name__)

    try:
        official_schemas = fetch_official_schemas()
        target_schema_info = {
            name: schema for name, schema in official_schemas.items() if name in target_schemas
        }

        if not target_schema_info:
            logger.warning(f"None of the target schemas {target_schemas} could be loaded")
            return {"valid": [], "invalid": terms, "deprecated": []}

        # Collect all valid terms from target schemas
        valid_terms = set()
        for schema_info in target_schema_info.values():
            valid_terms.update(schema_info.terms)

        # Categorize input terms
        result = {"valid": [], "invalid": [], "deprecated": []}

        for term in terms:
            if term in PROJECT_TERMS:
                result["valid"].append(term)  # Project terms are always valid
            elif term in valid_terms:
                result["valid"].append(term)
            else:
                result["invalid"].append(term)

        return result

    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return {"valid": [], "invalid": terms, "deprecated": []}


class DwcRecord(BaseModel):
    """Pydantic model representing a single Darwin Core record.

    All fields are optional strings.  When serialised via :meth:`to_dict`
    missing values are converted to empty strings so that CSV output is
    consistent.
    """

    model_config = ConfigDict(extra="allow")

    occurrenceID: Optional[str] = None
    catalogNumber: Optional[str] = None
    otherCatalogNumbers: Optional[str] = None
    institutionCode: Optional[str] = None
    collectionCode: Optional[str] = None
    ownerInstitutionCode: Optional[str] = None
    basisOfRecord: Optional[str] = None
    preparations: Optional[str] = None
    hasFragmentPacket: Optional[str] = None
    disposition: Optional[str] = None
    recordedBy: Optional[str] = None
    recordedByID: Optional[str] = None
    recordNumber: Optional[str] = None
    eventDate: Optional[str] = None
    eventTime: Optional[str] = None
    country: Optional[str] = None
    stateProvince: Optional[str] = None
    county: Optional[str] = None
    municipality: Optional[str] = None
    locality: Optional[str] = None
    verbatimLocality: Optional[str] = None
    decimalLatitude: Optional[str] = None
    decimalLongitude: Optional[str] = None
    geodeticDatum: Optional[str] = None
    coordinateUncertaintyInMeters: Optional[str] = None
    habitat: Optional[str] = None
    eventRemarks: Optional[str] = None
    scientificName: Optional[str] = None
    scientificNameAuthorship: Optional[str] = None
    taxonRank: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    specificEpithet: Optional[str] = None
    infraspecificEpithet: Optional[str] = None
    identificationQualifier: Optional[str] = None
    identifiedBy: Optional[str] = None
    dateIdentified: Optional[str] = None
    identificationRemarks: Optional[str] = None
    identificationReferences: Optional[str] = None
    identificationVerificationStatus: Optional[str] = None
    typeStatus: Optional[str] = None
    associatedOccurrences: Optional[str] = None
    occurrenceRemarks: Optional[str] = None
    dynamicProperties: Optional[str] = None
    scientificName_verbatim: Optional[str] = None
    verbatimEventDate: Optional[str] = None
    eventDateUncertaintyInDays: Optional[str] = None
    datasetName: Optional[str] = None
    verbatimLabel: Optional[str] = None
    flags: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Return a dictionary representation suitable for CSV writing.

        Any ``None`` values are converted to empty strings and only known
        Darwin Core terms are returned.
        """

        return {term: getattr(self, term) or "" for term in DWC_TERMS}
