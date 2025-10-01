# ADR-002: Configuration Management Approach

**Date**: 2024-09-01 (Reverse-Engineered from v0.1.0 Foundation)
**Status**: Accepted
**Deciders**: Development Team
**Technical Story**: Need for flexible, hierarchical configuration system supporting diverse institutional requirements

## Context and Problem Statement

The herbarium digitization system required a configuration management approach that could:
- Support diverse institutional deployment scenarios
- Enable engine selection and parameter tuning
- Provide sensible defaults while allowing customization
- Handle complex nested configuration structures

### Current Situation
- Multiple OCR engines with different configuration requirements
- Institutional variations in processing requirements
- Need for both default and override configuration
- Complex parameter dependencies between system components

### Requirements
- **Flexibility**: Support diverse institutional configuration needs
- **Usability**: Provide working defaults out of the box
- **Maintainability**: Clear configuration structure and validation
- **Extensibility**: Easy addition of new configuration options

## Decision Drivers

- **Institutional Diversity**: Different organizations have different requirements
- **Engine Complexity**: Multiple OCR engines with distinct parameter sets
- **Developer Experience**: Need clear, readable configuration format
- **Deployment Simplicity**: Minimal configuration required for basic usage
- **Override Capability**: Institutional customization without modifying defaults

## Considered Options

### Option 1: Single JSON Configuration File
**Description**: Single JSON file with all configuration options
**Pros**:
- Simple file structure
- Wide tool support
- Easy parsing

**Cons**:
- No comments or documentation
- Difficult to merge defaults and overrides
- Poor human readability for complex structures

**Cost/Effort**: Low implementation
**Risk**: Medium - maintainability issues

### Option 2: YAML Configuration with Overrides
**Description**: YAML files with default + override merge capability
**Pros**:
- Human readable
- Comment support
- Hierarchical structure
- Good merge semantics

**Cons**:
- YAML parsing complexity
- Indentation sensitivity
- Less familiar to some developers

**Cost/Effort**: Medium implementation
**Risk**: Low - proven approach

### Option 3: TOML with Deep Merge Strategy
**Description**: TOML format with hierarchical defaults and user overrides
**Pros**:
- Excellent human readability
- Strong typing support
- Clear section structure
- Comment support
- Simple parsing

**Cons**:
- Less familiar format
- Requires deep merge implementation
- Additional dependency

**Cost/Effort**: Medium implementation
**Risk**: Low - good balance of features

### Option 4: Environment Variables Only
**Description**: Configure entirely through environment variables
**Pros**:
- Deployment-friendly
- No file management
- Clear precedence

**Cons**:
- Poor for complex nested configuration
- Difficult to document
- Not suitable for large parameter sets

**Cost/Effort**: Low implementation
**Risk**: High - insufficient for complex configuration needs

## Decision Outcome

**Chosen Option**: TOML with Deep Merge Strategy (Option 3)

**Rationale**:
- TOML provides excellent readability for complex configuration
- Deep merge strategy allows clean separation of defaults and overrides
- Section-based structure maps well to system components
- Comment support enables self-documenting configuration
- Strong typing reduces configuration errors

### Implementation Plan
1. Create comprehensive default configuration in TOML format
2. Implement deep merge function for configuration override
3. Structure configuration by system component ([ocr], [dwc], [qc], etc.)
4. Add configuration validation and error reporting
5. Document configuration options and examples

### Success Metrics
- **Usability**: System works with zero configuration for basic use cases
- **Flexibility**: Institutions can customize any aspect without modifying defaults
- **Clarity**: Configuration options are self-documenting and discoverable
- **Reliability**: Invalid configuration is detected and reported clearly

## Consequences

### Positive Consequences
- **Clear Structure**: Component-based configuration sections improve organization
- **Self-Documenting**: Comments and clear naming reduce documentation burden
- **Flexible Deployment**: Easy institutional customization without default modification
- **Developer Friendly**: Readable format improves development experience

### Negative Consequences
- **Additional Complexity**: Deep merge logic adds system complexity
- **Format Learning**: TOML less familiar than JSON to some developers
- **Validation Requirement**: Need comprehensive validation to catch configuration errors

### Risk Mitigation
- **Comprehensive Defaults**: Provide working configuration out of the box
- **Clear Documentation**: Document all configuration options with examples
- **Validation Implementation**: Early validation with clear error messages
- **Migration Support**: Tools to help migrate configuration between versions

## Implementation Details

### Technical Changes Required
- TOML parsing library integration (tomllib for Python 3.11+, tomli for earlier)
- Deep merge function implementation for nested dictionaries
- Configuration validation framework
- Default configuration file creation
- Command-line override support

### Configuration Structure
```toml
[ocr]
preferred_engine = "vision"
enabled_engines = ["vision", "google", "azure"]
confidence_threshold = 0.80

[ocr.vision]
# Apple Vision specific settings

[ocr.google]
# Google Vision API settings
credentials_path = ".google-credentials.json"

[pipeline]
steps = ["image_to_text", "text_to_dwc"]

[preprocess]
pipeline = ["grayscale", "deskew", "binarize"]

[dwc]
schema = "dwc-abcd"
strict_minimal_fields = ["catalogNumber", "scientificName"]

[qc]
dupes = ["catalog", "sha256", "phash"]

[qc.gbif]
enabled = false
timeout = 10.0
```

### Dependencies
- **tomllib/tomli**: TOML parsing capability
- **Deep merge implementation**: Recursive dictionary merging
- **Validation framework**: Configuration structure and value validation

### Migration Strategy
- **Default Bundling**: Comprehensive defaults included with application
- **Override Discovery**: User configuration loaded from predictable locations
- **Version Compatibility**: Graceful handling of configuration format evolution

## Validation and Testing

### Validation Plan
- **Format Validation**: TOML syntax and structure validation
- **Value Validation**: Type checking and range validation for all options
- **Dependency Validation**: Check that dependent options are properly configured
- **Integration Testing**: Verify configuration affects system behavior correctly

### Monitoring
- **Configuration Loading**: Log successful configuration loading and sources
- **Override Tracking**: Track which values come from defaults vs overrides
- **Validation Failures**: Alert on configuration errors with clear remediation
- **Usage Patterns**: Monitor which configuration options are commonly overridden

## Follow-up Actions

- [x] Implement TOML parsing and deep merge functionality
- [x] Create comprehensive default configuration
- [x] Add configuration validation framework
- [x] Document configuration options and examples
- [ ] Create configuration migration tools for version upgrades
- [ ] Add configuration validation to CI/CD pipeline
- [ ] Implement configuration drift detection for production deployments

## References

- [Configuration Documentation](../../docs/configuration.md)
- [Default Configuration File](../../config/config.default.toml)
- [Processing Pipeline Configuration Retroactive Specification](../retro-specs/processing-pipeline-configuration.md)
- [Configuration Template](../templates/configuration-schema.md)

---

**Note**: This ADR is reverse-engineered from implementation decisions made during v0.1.0 foundation development. The TOML + deep merge approach has proven effective for managing complex configuration across diverse deployment scenarios.