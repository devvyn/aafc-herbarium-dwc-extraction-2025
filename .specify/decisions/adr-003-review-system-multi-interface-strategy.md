# ADR-003: Review System Multi-Interface Strategy

**Date**: 2024-09-03 (Reverse-Engineered from v0.1.2 Implementation)
**Status**: Accepted
**Deciders**: Development Team, User Experience Considerations
**Technical Story**: Need for flexible curator review workflows accommodating different user preferences and institutional contexts

## Context and Problem Statement

The quality control system required curator review capabilities to validate and correct OCR extraction results. Different curators and institutions have varying preferences for review interfaces and workflows.

### Current Situation
- OCR extraction produces multiple candidate values per field
- Manual review required for quality assurance
- Diverse curator preferences (CLI, GUI, spreadsheet workflows)
- Institutional requirements for audit trails and review distribution

### Requirements
- **Accessibility**: Support different user interface preferences
- **Workflow Integration**: Fit into existing institutional processes
- **Audit Trail**: Complete tracking of reviewer decisions
- **Distribution**: Enable review work distribution across team members
- **Offline Capability**: Support disconnected review workflows

## Decision Drivers

- **User Diversity**: Curators have different interface preferences and technical skills
- **Institutional Workflows**: Need integration with existing curatorial processes
- **Review Distribution**: Enable parallel review work without conflicts
- **Quality Assurance**: Comprehensive audit trail for institutional compliance
- **Technical Constraints**: Development resources and maintenance considerations

## Considered Options

### Option 1: Single Web Interface
**Description**: Comprehensive web-based review interface only
**Pros**:
- Rich user interface capabilities
- Cross-platform compatibility
- Real-time collaboration features
- Professional appearance

**Cons**:
- Requires web server deployment
- Not suitable for all curator workflows
- Network dependency for review
- Single point of failure

**Cost/Effort**: Medium implementation, ongoing hosting
**Risk**: Medium - doesn't accommodate all user preferences

### Option 2: Desktop Application
**Description**: Native desktop application for review
**Pros**:
- Rich interface capabilities
- Offline functionality
- Native OS integration
- No server requirements

**Cons**:
- Platform-specific development
- Complex distribution and updates
- High development and maintenance cost
- Limited collaboration features

**Cost/Effort**: High implementation and maintenance
**Risk**: High - significant development burden

### Option 3: Command Line Interface Only
**Description**: Simple CLI-based review workflow
**Pros**:
- Minimal development effort
- Scriptable and automatable
- Fast for experienced users
- Cross-platform compatible

**Cons**:
- Poor user experience for many curators
- No image display capabilities
- Limited adoption potential
- Insufficient for complex review tasks

**Cost/Effort**: Low implementation
**Risk**: High - insufficient for user needs

### Option 4: Multi-Interface Strategy
**Description**: Multiple interface options (CLI, TUI, Web, Spreadsheet)
**Pros**:
- Accommodates diverse user preferences
- Flexible workflow integration
- Offline and online capabilities
- Incremental development possible

**Cons**:
- Higher development and maintenance cost
- Interface consistency challenges
- More complex testing requirements
- Feature parity considerations

**Cost/Effort**: High implementation, medium maintenance
**Risk**: Medium - complexity vs user satisfaction trade-off

## Decision Outcome

**Chosen Option**: Multi-Interface Strategy (Option 4)

**Rationale**:
- Different curators have strong preferences for different interface types
- Institutional workflows vary significantly across organizations
- Multi-interface approach maximizes adoption and user satisfaction
- Incremental development allows prioritization based on usage
- Shared data model ensures consistency across interfaces

### Implementation Plan
1. **Phase 1**: CLI and TUI interfaces for basic review workflows
2. **Phase 2**: Web interface for rich visual review experience
3. **Phase 3**: Spreadsheet integration for team-based workflows
4. **Phase 4**: Bundle export/import system for distributed review

### Success Metrics
- **Adoption**: Multiple interfaces actively used by different curator types
- **Satisfaction**: Positive feedback on interface options and flexibility
- **Efficiency**: Improved review throughput compared to manual processes
- **Quality**: Consistent decision quality across different interfaces

## Consequences

### Positive Consequences
- **User Satisfaction**: Curators can use their preferred interface type
- **Workflow Flexibility**: Accommodates diverse institutional processes
- **Adoption Rate**: Higher adoption due to interface choice availability
- **Team Collaboration**: Spreadsheet workflow enables distributed review

### Negative Consequences
- **Development Complexity**: Multiple interfaces increase implementation burden
- **Maintenance Overhead**: More interfaces to maintain and test
- **Feature Consistency**: Ensuring feature parity across interfaces
- **User Training**: More options may create confusion for some users

### Risk Mitigation
- **Shared Data Model**: Common candidate/decision model ensures consistency
- **Incremental Development**: Prioritize most valuable interfaces first
- **Interface Standards**: Establish consistency guidelines across interfaces
- **User Guidance**: Clear documentation on when to use which interface

## Implementation Details

### Technical Changes Required
- **CLI Interface**: Simple text-based candidate selection
- **TUI Interface**: Rich terminal interface with ASCII image preview
- **Web Interface**: HTTP server with image display and AJAX selection
- **Spreadsheet Integration**: Excel/CSV export and import capabilities
- **Bundle System**: Versioned review packages for distribution

### Interface Architecture
```python
# Shared data model
class Candidate:
    value: str
    engine: str
    confidence: float

class Decision:
    value: str
    engine: str
    decided_at: str

# Interface implementations
class CLIReview:
    def review_candidates(candidates) -> Decision

class TUIReview:
    def review_candidates(candidates) -> Decision

class WebReview:
    def serve_review_interface()

class SpreadsheetReview:
    def export_for_review()
    def import_decisions()
```

### Dependencies
- **CLI**: Basic terminal I/O
- **TUI**: Textual library for rich terminal interfaces
- **Web**: HTTP server and template rendering
- **Spreadsheet**: Pandas/OpenPyXL for Excel integration
- **Bundle System**: ZIP archive creation and validation

### Migration Strategy
- **Incremental Rollout**: Introduce interfaces based on user demand
- **Data Compatibility**: Ensure all interfaces work with same data format
- **Training Materials**: Create interface-specific documentation and tutorials

## Validation and Testing

### Validation Plan
- **Usability Testing**: Test each interface with representative curators
- **Performance Testing**: Ensure interfaces handle large candidate sets
- **Integration Testing**: Verify data consistency across interfaces
- **Workflow Testing**: Validate institutional workflow integration

### Monitoring
- **Usage Analytics**: Track which interfaces are used most frequently
- **Performance Metrics**: Monitor review throughput by interface type
- **Error Tracking**: Identify interface-specific issues and usability problems
- **User Feedback**: Regular surveys on interface satisfaction and preferences

## Follow-up Actions

- [x] Implement CLI review interface with basic candidate selection
- [x] Create TUI interface with Textual for rich terminal experience
- [x] Build web interface with image display and real-time selection
- [x] Add spreadsheet export/import for team-based review workflows
- [x] Create review bundle system for distributed workflows
- [ ] Conduct usability studies with representative curator groups
- [ ] Establish interface usage monitoring and analytics
- [ ] Create comprehensive training materials for each interface type

## References

- [Review Workflow Documentation](../../docs/review_workflow.md)
- [Quality Control Review System Retroactive Specification](../retro-specs/quality-control-review-system.md)
- [TUI Interface Implementation](../../review_tui.py)
- [Web Interface Implementation](../../review_web.py)
- [Spreadsheet Integration](../../io_utils/spreadsheets.py)

---

**Note**: This ADR is reverse-engineered from implementation decisions made during v0.1.2 development. The multi-interface strategy has proven successful in accommodating diverse curator preferences and institutional workflows, though it has required ongoing maintenance of multiple codebases.
