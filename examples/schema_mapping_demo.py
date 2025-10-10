#!/usr/bin/env python3
"""
Demonstration of enhanced schema and mapping functionality.

This script showcases the improvements made to address issues #188 and #189:
- Parse official DwC and ABCD schemas from canonical sources
- Auto-generate Darwin Core term mappings
- Dynamic and configurable mapping system
- Schema version compatibility checking
- Validation against official schema definitions

Usage:
    python examples/schema_mapping_demo.py
"""

import logging
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from dwc import (
    SchemaManager,
    configure_dynamic_mappings,
    map_ocr_to_dwc,
    auto_generate_mappings_from_schemas,
    validate_mapping_against_schemas,
    suggest_mapping_improvements,
)

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def demo_schema_manager():
    """Demonstrate SchemaManager functionality."""
    print("\n" + "=" * 60)
    print("SCHEMA MANAGER DEMO")
    print("=" * 60)

    # Initialize schema manager
    cache_dir = Path("output/schema_cache")
    manager = SchemaManager(
        cache_dir=cache_dir, preferred_schemas=["dwc_simple", "abcd_206"], update_interval_days=7
    )

    # Get status
    status = manager.get_status()
    print(f"Cache directory: {status['cache_dir']}")
    print(f"Preferred schemas: {status['preferred_schemas']}")
    print(f"Update interval: {status['update_interval_days']} days")

    # List available schemas
    print(f"\nAvailable schemas: {manager.list_available_schemas()}")

    # Get schema terms
    terms = manager.get_schema_terms()
    print(f"Total terms available: {len(terms)}")
    print(f"First 10 terms: {terms[:10]}")

    return manager


def demo_automatic_mappings():
    """Demonstrate automatic mapping generation."""
    print("\n" + "=" * 60)
    print("AUTOMATIC MAPPING GENERATION DEMO")
    print("=" * 60)

    # Generate mappings from schemas
    mappings = auto_generate_mappings_from_schemas(
        schema_names=["dwc_simple"], include_fuzzy=True, similarity_threshold=0.7
    )

    print(f"Generated {len(mappings)} automatic mappings")

    # Show some examples
    example_mappings = {k: v for k, v in list(mappings.items())[:10]}
    print("\nExample mappings:")
    for source, target in example_mappings.items():
        print(f"  '{source}' -> '{target}'")

    return mappings


def demo_dynamic_mapping_configuration():
    """Demonstrate dynamic mapping configuration and usage."""
    print("\n" + "=" * 60)
    print("DYNAMIC MAPPING CONFIGURATION DEMO")
    print("=" * 60)

    # Configure dynamic mappings
    configure_dynamic_mappings(
        schema_names=["dwc_simple"], include_fuzzy=True, similarity_threshold=0.6
    )
    print("Dynamic mappings configured!")

    # Test OCR data with various field formats
    ocr_data = {
        "barcode": "HERB123456",  # Standard mapping via rules
        "scientific_name": "Plantus testicus",  # Dynamic mapping
        "collector": "Dr. Jane Smith",  # Standard mapping via rules
        "collection_date": "2023-07-15",  # Dynamic mapping
        "lat": "45.5231",  # Dynamic mapping
        "lng": "-75.6919",  # Dynamic mapping
        "country": "Canada",  # Direct mapping
        "province": "Ontario",  # Standard mapping via rules
        "locality": "Algonquin Park",  # Direct mapping
        "family": "Plantaceae",  # Direct mapping
        "habitat": "Mixed forest",  # Direct mapping
        "specimen_id": "ALG2023-0542",  # Not mapped (should be suggested)
    }

    print(f"\nOriginal OCR data ({len(ocr_data)} fields):")
    for field, value in ocr_data.items():
        print(f"  {field}: {value}")

    # Map to Darwin Core
    record = map_ocr_to_dwc(ocr_data)

    print("\nMapped Darwin Core record:")
    record_dict = record.to_dict()
    populated_fields = {k: v for k, v in record_dict.items() if v}
    for field, value in populated_fields.items():
        print(f"  {field}: {value}")

    print("\nMapping statistics:")
    print(f"  Original fields: {len(ocr_data)}")
    print(f"  Mapped fields: {len(populated_fields)}")
    print(f"  Mapping success rate: {len(populated_fields)/len(ocr_data)*100:.1f}%")

    return record


def demo_validation_and_suggestions():
    """Demonstrate validation and mapping suggestions."""
    print("\n" + "=" * 60)
    print("VALIDATION AND SUGGESTIONS DEMO")
    print("=" * 60)

    # Create a test record with some unmapped fields
    test_data = {
        "catalogNumber": "TEST123",  # Valid DwC term
        "scientificName": "Test species",  # Valid DwC term
        "specimen_id": "ALG001",  # Not a DwC term
        "taxon": "Plantus sp.",  # Not a DwC term
        "when_collected": "2023-01-01",  # Not a DwC term
        "invalid_field": "some value",  # Completely invalid
    }

    record = map_ocr_to_dwc(test_data)

    # Validate the mapping
    validation = validate_mapping_against_schemas(record, ["dwc_simple"])

    print("Validation results:")
    print(f"  Total fields: {validation['total_fields']}")
    print(f"  Valid fields: {validation['valid_fields']}")
    print(f"  Invalid fields: {validation['invalid_fields']}")
    print(f"  Compatibility score: {validation['compatibility_score']:.2f}")

    if validation["invalid_field_names"]:
        print(f"  Invalid field names: {validation['invalid_field_names']}")

    # Get suggestions for unmapped fields
    unmapped_fields = ["specimen_id", "taxon", "when_collected", "collector_name"]
    suggestions = suggest_mapping_improvements(
        unmapped_fields, target_schemas=["dwc_simple"], similarity_threshold=0.5
    )

    print("\nMapping suggestions for unmapped fields:")
    for field, suggested_terms in suggestions.items():
        if suggested_terms:
            print(f"  '{field}' -> {suggested_terms}")
        else:
            print(f"  '{field}' -> No suggestions found")


def demo_schema_compatibility():
    """Demonstrate schema compatibility checking."""
    print("\n" + "=" * 60)
    print("SCHEMA COMPATIBILITY DEMO")
    print("=" * 60)

    manager = SchemaManager(cache_dir=Path("output/schema_cache"))

    # Generate compatibility report
    try:
        report = manager.get_schema_compatibility_report("dwc_simple", ["abcd_206"])

        if "error" not in report:
            print("Darwin Core vs ABCD Compatibility Report:")
            print(f"  Source schema: {report['source_schema']}")
            print(f"  Source term count: {report['source_term_count']}")
            print(f"  Overall compatibility: {report['overall_compatibility']:.2f}")

            for target_name, target_data in report["target_schemas"].items():
                if "error" not in target_data:
                    print(f"\n  Target schema: {target_name}")
                    print(f"    Target term count: {target_data['target_term_count']}")
                    print(f"    Overlapping terms: {target_data['overlapping_terms']}")
                    print(f"    Compatibility score: {target_data['compatibility_score']:.2f}")
                    print(f"    Unique to source: {target_data['unique_to_source']}")
                    print(f"    Unique to target: {target_data['unique_to_target']}")

    except Exception as e:
        print(f"Compatibility report failed: {e}")
        print("This is expected if schemas couldn't be fetched from official sources")


def main():
    """Run all demonstrations."""
    print("Enhanced Schema and Mapping Functionality Demo")
    print("Issues #188 and #189 Implementation")

    try:
        # Demo 1: Schema Manager
        manager = demo_schema_manager()

        # Demo 2: Automatic Mapping Generation
        mappings = demo_automatic_mappings()

        # Demo 3: Dynamic Mapping Configuration
        record = demo_dynamic_mapping_configuration()

        # Demo 4: Validation and Suggestions
        demo_validation_and_suggestions()

        # Demo 5: Schema Compatibility
        demo_schema_compatibility()

        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey improvements implemented:")
        print("✓ Official Darwin Core and ABCD schema parsing")
        print("✓ Automatic term mapping generation")
        print("✓ Dynamic and configurable mapping system")
        print("✓ Schema validation against official definitions")
        print("✓ Schema version compatibility checking")
        print("✓ Enhanced configuration system for dynamic handling")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\nDemo encountered an error: {e}")
        print("This may be due to network connectivity issues or missing dependencies.")


if __name__ == "__main__":
    main()
