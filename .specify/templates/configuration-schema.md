# Configuration Schema Template

Use this template when introducing new configuration options or restructuring existing configuration to ensure proper validation, documentation, and migration strategy.

## Configuration Schema: [Configuration Section/Feature]

**Feature**: [Name of feature requiring configuration]
**Date**: [YYYY-MM-DD]
**Configuration Section**: [e.g., `[ocr]`, `[qc.gbif]`, `[pipeline]`]
**Schema Version**: [Version number for this configuration schema]

## Configuration Requirements

### Functional Requirements
- [ ] **Purpose**: [What does this configuration control?]
- [ ] **Scope**: [Which components use this configuration?]
- [ ] **Dependencies**: [What other configuration sections does this depend on?]
- [ ] **Conflicts**: [Are there any conflicting or mutually exclusive options?]

### User Experience Requirements
- [ ] **Defaults**: [What should the default behavior be?]
- [ ] **Required vs Optional**: [Which settings are mandatory?]
- [ ] **Validation**: [What validation rules apply?]
- [ ] **Error Handling**: [How should invalid configuration be handled?]

## Schema Definition

### TOML Configuration Structure
```toml
[section.subsection]
# Configuration options with types and constraints
option_name = "default_value"    # Type: string, Required: false, Description: Purpose
numeric_option = 42              # Type: integer, Range: 1-100, Description: Purpose
boolean_flag = true              # Type: boolean, Default: true, Description: Purpose
list_option = ["item1", "item2"] # Type: array of strings, Description: Purpose

# Nested configuration
[section.subsection.nested]
nested_option = "value"          # Type: string, Pattern: "^[a-z]+$", Description: Purpose
```

### JSON Schema Validation (if applicable)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "section": {
      "type": "object",
      "properties": {
        "subsection": {
          "type": "object",
          "properties": {
            "option_name": {
              "type": "string",
              "description": "Purpose and usage",
              "default": "default_value"
            },
            "numeric_option": {
              "type": "integer",
              "minimum": 1,
              "maximum": 100,
              "default": 42,
              "description": "Purpose and valid range"
            }
          }
        }
      }
    }
  }
}
```

## Configuration Options

### Option 1: [option_name]
- **Type**: [string|integer|boolean|array]
- **Required**: [yes|no]
- **Default**: [default value]
- **Valid Values**: [constraints, ranges, patterns]
- **Description**: [What this option controls]
- **Examples**:
  ```toml
  option_name = "example_value"
  ```
- **Impact**: [What happens when this option changes]

### Option 2: [numeric_option]
- **Type**: [string|integer|boolean|array]
- **Required**: [yes|no]
- **Default**: [default value]
- **Valid Values**: [constraints, ranges, patterns]
- **Description**: [What this option controls]
- **Examples**:
  ```toml
  numeric_option = 50
  ```
- **Impact**: [What happens when this option changes]

[Continue for all configuration options]

## Configuration Validation

### Validation Rules
1. **Type Validation**:
   - [ ] All options have correct data types
   - [ ] Numeric options are within valid ranges
   - [ ] String options match required patterns
   - [ ] Array options contain valid elements

2. **Business Logic Validation**:
   - [ ] Mutually exclusive options are not both set
   - [ ] Dependent options are present when required
   - [ ] Combinations that don't make sense are rejected

3. **External Dependency Validation**:
   - [ ] File paths exist and are accessible
   - [ ] URLs are reachable (if validation at startup is desired)
   - [ ] API keys are present when required

### Error Messages
- **Invalid Type**: [Clear message for type mismatches]
- **Out of Range**: [Message for values outside valid ranges]
- **Missing Required**: [Message for missing mandatory options]
- **Invalid Combination**: [Message for conflicting options]

## Default Configuration

### Recommended Defaults
```toml
[section.subsection]
# Production-ready defaults
option_name = "production_value"
numeric_option = 42
boolean_flag = true

# Development-friendly alternatives
# option_name = "development_value"
# numeric_option = 10
# boolean_flag = false
```

### Default Rationale
- **option_name**: [Why this default was chosen]
- **numeric_option**: [Rationale for default value]
- **boolean_flag**: [Reasoning for default state]

## Migration Strategy

### Version Compatibility
- **Current Version**: [What version does this replace?]
- **Breaking Changes**: [What changes are not backward compatible?]
- **Deprecated Options**: [Which options are being removed?]

### Migration Steps
1. **Phase 1 - Introduction**: [How new options are introduced]
2. **Phase 2 - Deprecation**: [How old options are deprecated]
3. **Phase 3 - Removal**: [When old options are removed]

### Migration Scripts
```python
def migrate_config_v1_to_v2(old_config: dict) -> dict:
    """Migrate configuration from v1 to v2 format."""
    new_config = old_config.copy()

    # Handle renamed options
    if 'old_option_name' in old_config:
        new_config['new_option_name'] = old_config['old_option_name']
        del new_config['old_option_name']

    # Handle restructured sections
    if 'flat_option' in old_config:
        new_config.setdefault('section', {})['nested_option'] = old_config['flat_option']
        del new_config['flat_option']

    return new_config
```

## Documentation

### User Documentation
```markdown
## [Section] Configuration

The `[section.subsection]` configuration controls [purpose].

### Options

- `option_name` (string, optional, default: "default_value")
  Purpose and usage description.

  Example:
  ```toml
  option_name = "custom_value"
  ```

- `numeric_option` (integer, required, range: 1-100)
  Purpose and valid range description.

  Example:
  ```toml
  numeric_option = 75
  ```
```

### Developer Documentation
- **Code Location**: [Where this configuration is used in code]
- **Loading Logic**: [How configuration is loaded and processed]
- **Validation Logic**: [Where and how validation occurs]
- **Usage Patterns**: [Common ways this configuration is used]

## Testing Strategy

### Configuration Testing
- [ ] **Valid Configuration**: Test all valid configuration combinations
- [ ] **Invalid Configuration**: Test validation catches all invalid options
- [ ] **Default Behavior**: Test system works with default configuration
- [ ] **Edge Cases**: Test boundary values and edge conditions

### Migration Testing
- [ ] **Forward Migration**: Old configurations migrate to new format
- [ ] **Backward Compatibility**: New code handles old configuration
- [ ] **Error Handling**: Invalid migrations are handled gracefully

### Integration Testing
- [ ] **Component Integration**: Configuration properly affects component behavior
- [ ] **Performance Impact**: Configuration changes don't degrade performance
- [ ] **Dependency Testing**: Related components work with new configuration

## Monitoring and Observability

### Configuration Monitoring
- [ ] **Active Configuration**: Log current configuration on startup
- [ ] **Configuration Changes**: Log when configuration is reloaded
- [ ] **Validation Failures**: Alert on configuration validation errors
- [ ] **Performance Impact**: Monitor performance effects of configuration changes

### Debugging Support
- [ ] **Configuration Dump**: Ability to export current configuration
- [ ] **Validation Details**: Detailed validation error reporting
- [ ] **Override Tracking**: Track which values come from defaults vs overrides

## Security Considerations

### Sensitive Information
- [ ] **Secrets Handling**: How are API keys and passwords managed?
- [ ] **File Permissions**: What permissions should configuration files have?
- [ ] **Environment Variables**: Which options can be set via environment?
- [ ] **Logging Safety**: Ensure secrets are not logged

### Access Control
- [ ] **Read Access**: Who can read configuration?
- [ ] **Write Access**: Who can modify configuration?
- [ ] **Audit Trail**: Are configuration changes logged?

## Implementation Checklist

### Development Tasks
- [ ] Define configuration schema
- [ ] Implement validation logic
- [ ] Create migration functions
- [ ] Write unit tests for validation
- [ ] Write integration tests
- [ ] Update documentation

### Deployment Tasks
- [ ] Update default configuration files
- [ ] Create migration scripts
- [ ] Test migration on staging
- [ ] Plan rollback procedures
- [ ] Update monitoring and alerting

---

**Notes**:
- Configuration should be self-documenting with clear option names
- Provide sensible defaults that work for most users
- Validate configuration early to provide clear error messages
- Plan for configuration evolution and backward compatibility
