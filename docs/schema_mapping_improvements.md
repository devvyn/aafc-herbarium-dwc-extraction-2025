# Schema and Mapping Improvements

This document describes the enhancements made to address issues #188 "Parse official DwC and ABCD schemas" and #189 "Auto-generate Darwin Core term mappings".

## Overview

The schema and mapping system has been significantly enhanced to provide:

1. **Official Schema Parsing**: Direct fetching and parsing of Darwin Core and ABCD schemas from their canonical TDWG sources
2. **Automatic Mapping Generation**: Dynamic generation of field mappings based on parsed schemas
3. **Enhanced Validation**: Validation against official schema definitions with compatibility checking
4. **Dynamic Configuration**: Runtime configuration of mapping rules and schema handling
5. **Improved Compatibility**: Version compatibility checking between different schema versions

## Key Components

### 1. Enhanced Schema Module (`dwc/schema.py`)

#### New Features:
- **Official Schema URLs**: Canonical sources for DwC and ABCD schemas
- **Schema Fetching**: Network-based retrieval of schemas with caching
- **Detailed Parsing**: Extraction of term metadata including descriptions and data types
- **Version Compatibility**: Cross-schema compatibility validation

#### Key Functions:
```python
# Fetch official schemas from TDWG sources
schemas = fetch_official_schemas(use_cache=True)

# Load terms from official sources
terms = load_schema_terms_from_official_sources(['dwc_simple', 'abcd_206'])

# Configure terms from official sources
configure_terms_from_official_sources(['dwc_simple'])

# Validate term compatibility
compatibility = validate_schema_compatibility(terms, target_schemas)
```

#### Official Schema Sources:
- **Darwin Core**: `http://rs.tdwg.org/dwc/xsd/tdwg_dwc_simple.xsd`
- **ABCD 2.06**: `https://abcd.tdwg.org/xml/ABCD_2.06.xsd`

### 2. Enhanced Mapper Module (`dwc/mapper.py`)

#### New Features:
- **Dynamic Mappings**: Runtime-generated mappings based on official schemas
- **Fuzzy Matching**: Similarity-based field matching with configurable thresholds
- **Automatic Generation**: Schema-driven mapping rule generation
- **Validation Integration**: Built-in validation against target schemas

#### Key Functions:
```python
# Generate automatic mappings
mappings = auto_generate_mappings_from_schemas(
    schema_names=['dwc_simple'],
    include_fuzzy=True,
    similarity_threshold=0.6
)

# Configure dynamic mappings
configure_dynamic_mappings(['dwc_simple'], include_fuzzy=True)

# Validate mapped records
validation = validate_mapping_against_schemas(record, ['dwc_simple'])

# Get mapping suggestions
suggestions = suggest_mapping_improvements(unmapped_fields)
```

### 3. Schema Manager (`dwc/schema_manager.py`)

A comprehensive management system for schema handling:

#### Features:
- **Centralized Management**: Single interface for all schema operations
- **Caching System**: Local caching of downloaded schemas with update intervals
- **Status Monitoring**: Detailed status and health reporting
- **Compatibility Analysis**: Cross-schema compatibility reporting

#### Usage Example:
```python
from dwc import SchemaManager

# Initialize manager
manager = SchemaManager(
    cache_dir=Path("cache"),
    update_interval_days=30,
    preferred_schemas=["dwc_simple", "abcd_206"]
)

# Get schemas and generate mappings
schemas = manager.get_schemas()
mappings = manager.generate_mappings()
suggestions = manager.suggest_mappings(unmapped_fields)

# Compatibility analysis
report = manager.get_schema_compatibility_report("dwc_simple", ["abcd_206"])
```

## Configuration Enhancements

### Updated Configuration (`config/config.default.toml`)

New schema-related configuration options:

```toml
[dwc]
# Schema source configuration
use_official_schemas = false  # Enable official schema fetching
preferred_official_schemas = ["dwc_simple", "abcd_206"]
schema_cache_enabled = true
schema_update_interval_days = 30
schema_compatibility_check = true

# Existing configuration...
schema = "dwc-abcd"
schema_uri = "http://rs.tdwg.org/dwc/terms/"
schema_files = ["dwc.xsd", "abcd.xsd"]
```

## Mapping Improvements

### 1. Dynamic Mapping Generation

The system now automatically generates mappings based on:
- **Case variations**: `catalognumber` → `catalogNumber`
- **Format variations**: `scientific_name` → `scientificName`
- **Common aliases**: `lat` → `decimalLatitude`, `collector` → `recordedBy`
- **Fuzzy matching**: Similarity-based suggestions for unmapped fields

### 2. Enhanced Field Resolution

Mapping priority order:
1. **Static rules** (from `config/rules/dwc_rules.toml`)
2. **Dynamic mappings** (generated from schemas)
3. **Custom mappings** (from configuration)

### 3. Validation and Quality Control

- **Schema compliance**: Validate fields against official schema definitions
- **Compatibility scoring**: Quantitative compatibility assessment
- **Error flagging**: Automatic flagging of invalid or deprecated fields
- **Suggestion system**: Intelligent suggestions for unmapped fields

## API Reference

### New Imports Available:

```python
from dwc import (
    SchemaManager,                          # Schema management
    configure_terms_from_official_sources,  # Official schema configuration
    configure_dynamic_mappings,             # Dynamic mapping setup
    auto_generate_mappings_from_schemas,    # Mapping generation
    validate_mapping_against_schemas,       # Record validation
    validate_schema_compatibility,          # Term compatibility checking
    suggest_mapping_improvements,           # Mapping suggestions
    fetch_official_schemas,                 # Schema fetching
)
```

## Examples and Testing

### Demo Script
Run the comprehensive demo to see all features in action:
```bash
python examples/schema_mapping_demo.py
```

### Test Coverage
New test suites cover:
- Schema manager functionality (`tests/unit/test_schema_manager.py`)
- Enhanced mapping integration (`tests/integration/test_enhanced_mapping.py`)

## Performance Considerations

### Caching Strategy
- **Local caching**: Downloaded schemas cached with configurable update intervals
- **Lazy loading**: Schemas fetched only when needed
- **Memory efficiency**: Schemas cached in memory during session

### Network Resilience
- **Fallback behavior**: Falls back to local schemas if official sources unavailable
- **Timeout handling**: Configurable timeouts for schema fetching
- **Error recovery**: Graceful degradation when official schemas can't be accessed

## Migration Guide

### For Existing Codebases

1. **No breaking changes**: All existing functionality preserved
2. **Optional features**: Enhanced features are opt-in via configuration
3. **Backward compatibility**: Existing mapping rules continue to work

### To Enable Enhanced Features

1. **Update configuration**:
   ```toml
   [dwc]
   use_official_schemas = true
   schema_compatibility_check = true
   ```

2. **Use SchemaManager** for advanced features:
   ```python
   from dwc import SchemaManager
   manager = SchemaManager()
   manager.configure_dynamic_mappings()
   ```

3. **Leverage automatic mappings**:
   ```python
   from dwc import configure_dynamic_mappings
   configure_dynamic_mappings(include_fuzzy=True)
   ```

## Future Enhancements

### Planned Improvements
- **ABCD 3.0 support**: Integration with upcoming ABCD 3.0 specification
- **Custom schema support**: User-defined schema integration
- **Machine learning**: ML-based mapping suggestion improvements
- **Real-time validation**: Live validation during data entry

### Community Integration
- **GBIF integration**: Enhanced GBIF backbone validation
- **iDigBio compatibility**: Support for iDigBio data standards
- **Community schemas**: Support for community-specific extensions

## Troubleshooting

### Common Issues

1. **Network connectivity**: Official schemas require internet access
   - **Solution**: Enable caching and configure appropriate timeouts

2. **Schema parsing errors**: Malformed or inaccessible schemas
   - **Solution**: System falls back to local schemas automatically

3. **Mapping conflicts**: Multiple mappings for the same field
   - **Solution**: Clear priority order ensures consistent behavior

### Debug Information

Enable detailed logging to troubleshoot:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dwc')
```

## Conclusion

These enhancements significantly improve the schema and mapping capabilities of the herbarium DwC extraction system. The implementation provides:

- **Standards compliance**: Direct integration with official TDWG specifications
- **Automation**: Reduced manual configuration requirements
- **Flexibility**: Configurable and extensible mapping system
- **Quality assurance**: Enhanced validation and compatibility checking
- **Future-proofing**: Foundation for ongoing standards evolution

The improvements address the core requirements of issues #188 and #189 while maintaining backward compatibility and providing a path for future enhancements.
