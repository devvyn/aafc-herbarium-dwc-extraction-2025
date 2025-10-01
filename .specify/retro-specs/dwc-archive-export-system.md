# Retroactive Specification: Darwin Core Archive Export System

**Feature ID**: `retro-003-dwc-archive-export`
**Development Phase**: v0.2.0 (Phase 1 Major Enhancements)
**Implementation Date**: September 24, 2024
**Source Issues**: [#158](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/158)

## Reverse-Engineered Requirements

### Background Context
Based on changelog analysis, this feature created a production-ready export system for Darwin Core Archives with versioning, provenance tracking, and institutional compliance requirements.

### User Stories (Inferred)
- **As a museum curator**, I need versioned exports to track data changes over time
- **As a GBIF contributor**, I need compliant Darwin Core Archive format
- **As a data manager**, I need provenance tracking for audit trails
- **As a researcher**, I need bundle formats suitable for different use cases

### Functional Requirements (Reverse-Engineered)

#### Core Export Capabilities
1. **Versioned Export System**
   - Semantic versioning for data releases
   - Git integration for change tracking
   - Timestamp-based provenance records
   - Configurable version increment strategies

2. **Bundle Format Options**
   - **"Rich" Format**: Full metadata, provenance, checksums
   - **"Simple" Format**: Minimal compliance for basic users
   - **Configurable Components**: User-selectable bundle contents

3. **Manifest System**
   - **File Checksums**: SHA-256 hashing for integrity
   - **Metadata Tracking**: Processing parameters, engine versions
   - **Dependency Records**: Schema versions, tool versions used
   - **Change Documentation**: What changed since last version

4. **CLI Integration**
   - New `cli.py export` command
   - Streamlined workflow from processing to export
   - Configuration-driven behavior
   - Integration with existing processing pipeline

#### Darwin Core Compliance
- **TDWG Standards**: Official Darwin Core Archive format
- **Schema Validation**: Automatic compliance checking
- **Field Mapping**: Configurable term mappings
- **Vocabulary Compliance**: Controlled vocabulary validation

### Technical Implementation (From Code Analysis)

#### Archive Structure
```
dwc-archive-v1.2.3/
├── meta.xml              # Darwin Core Archive metadata
├── occurrence.txt         # Core occurrence data
├── identification.txt     # Identification history
├── manifest.json         # Bundle provenance and checksums
└── metadata/
    ├── processing-config.toml
    ├── version-info.json
    └── changelog.md
```

#### Key Components
- **Archive Builder**: `dwc/archive.py` - Creates compliant DwC-A packages
- **Version Manager**: Semantic versioning with git integration
- **Manifest Generator**: Comprehensive metadata and checksums
- **Configuration System**: Export format preferences and validation

### Success Criteria (Observed)
- ✅ GBIF-compliant Darwin Core Archive format
- ✅ Full provenance tracking with git integration
- ✅ Configurable bundle formats for different use cases
- ✅ Automated integrity checking with checksums
- ✅ Streamlined CLI workflow integration

### Quality Attributes
- **Compliance**: 100% Darwin Core Archive standard adherence
- **Traceability**: Complete provenance from raw images to export
- **Integrity**: SHA-256 checksums for all exported files
- **Usability**: Single command export workflow
- **Flexibility**: Multiple bundle formats for different needs

### Decisions Made (Inferred from Implementation)
- **Versioning Strategy**: Semantic versioning over timestamp-based
- **Git Integration**: Leverage existing VCS for change tracking
- **Bundle Options**: Rich vs simple to serve different user needs
- **Manifest Format**: JSON for machine readability
- **CLI Design**: Extend existing CLI rather than separate tool

## Critical Decision Points Identified

### Should Have Been Specified Upfront
1. **Version Strategy**: Why semantic versioning vs date-based?
2. **Bundle Formats**: What specific needs do "rich" vs "simple" serve?
3. **Manifest Content**: What metadata is essential vs optional?
4. **Performance Requirements**: How large can archives be?
5. **Backward Compatibility**: How to handle format changes?

### Technical Decisions Missing Documentation
- **Checksum Algorithm**: Why SHA-256 vs alternatives?
- **Archive Compression**: ZIP vs TAR vs uncompressed trade-offs
- **Schema Caching**: How to handle schema version changes?
- **Export Resumption**: Can interrupted exports be resumed?

### Integration Complexity Not Addressed
- **Pipeline Coupling**: How tightly coupled to processing pipeline?
- **Configuration Management**: How do export configs relate to processing configs?
- **Error Handling**: What happens when export fails mid-process?
- **Storage Requirements**: How much disk space needed for archives?

## Lessons for Future Specifications

### What Worked Well
- **Standards Compliance**: Clear adherence to Darwin Core Archive format
- **Provenance Focus**: Comprehensive tracking for institutional needs
- **User Options**: Multiple formats serve different stakeholder needs

### Missing from Original Development
- **Performance Analysis**: No testing of large dataset exports
- **Storage Strategy**: No planning for archive storage and retention
- **User Experience**: No usability testing of export workflows
- **Migration Planning**: No strategy for format version upgrades

### Recommendation for Similar Features
1. **Define performance targets** (export time, file size limits)
2. **Plan storage strategy** (where archives live, retention policies)
3. **Design migration path** for format changes
4. **Specify error recovery** (resumable exports, partial failures)
5. **Document compliance testing** (how to verify standard adherence)
6. **Plan user training** (documentation, examples, tutorials)