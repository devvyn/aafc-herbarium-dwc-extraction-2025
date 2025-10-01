# Retroactive Specification: Quality Control Review System

**Feature ID**: `retro-006-quality-control-review-system`
**Development Phase**: v0.1.2 - v0.2.0 (Enhancement through Production Scale)
**Implementation Date**: September 3, 2024 - September 24, 2024
**Source Files**: `review.py`, `review_tui.py`, `review_web.py`, `io_utils/candidates.py`, `io_utils/spreadsheets.py`

## Reverse-Engineered Requirements

### Background Context
Based on code analysis and documentation, this system provides comprehensive quality control and curator review capabilities for OCR extraction results. It enables multiple review interfaces (CLI, TUI, Web, Spreadsheet) with versioned bundles and audit trails for institutional curation workflows.

### User Stories (Inferred)
- **As a curator**, I need multiple review interfaces to accommodate different reviewing preferences and workflows
- **As a team lead**, I need to distribute review work across multiple curators without database conflicts
- **As a quality manager**, I need audit trails and version tracking for all curatorial decisions
- **As an institution**, I need review bundles that can be shared and archived for compliance
- **As a remote worker**, I need spreadsheet-based review for offline curation workflows
- **As a developer**, I need programmatic import/export of review decisions for workflow automation

### Functional Requirements (Reverse-Engineered)

#### Core Review Architecture
1. **Multi-Interface Review System**
   - **CLI Review**: Simple command-line candidate selection
   - **TUI Review**: Rich terminal interface with image preview (ASCII art)
   - **Web Review**: Browser-based interface with full image display
   - **Spreadsheet Review**: Excel/Google Sheets integration for team workflows

2. **Candidate Management System**
   - Candidate storage with confidence ranking
   - Engine attribution and error tracking
   - Decision recording with timestamp and curator attribution
   - Conflict detection for duplicate decisions

3. **Review Bundle System**
   - Self-contained review packages (ZIP archives)
   - Versioned bundles with semantic versioning
   - Manifest-based metadata and integrity tracking
   - Image inclusion for offline review workflows

4. **Decision Import/Export**
   - Review bundle export for distribution
   - Decision import with conflict detection
   - Spreadsheet import/export for team workflows
   - Audit trail preservation across imports

#### Multi-Interface Architecture

##### CLI Review Interface
```python
def review_candidates(db_path: Path, image: str) -> Decision | None:
    # 1. Load candidates ranked by confidence
    # 2. Display numbered list of options
    # 3. Accept user selection input
    # 4. Record decision with timestamp
```

##### TUI Review Interface
```python
class ReviewApp(App[Decision | None]):
    # Rich terminal interface with:
    # - ASCII art image preview
    # - Interactive candidate list
    # - Keyboard navigation
    # - Decision recording
```

##### Web Review Interface
```python
class ReviewHandler(BaseHTTPRequestHandler):
    # HTTP server providing:
    # - Full image display
    # - AJAX candidate selection
    # - Progress tracking
    # - Metadata headers (commit, version)
```

##### Spreadsheet Review Interface
```python
def export_candidates_to_spreadsheet(conn, version: str, output_path: Path):
    # Excel export with:
    # - Candidate options per row
    # - Selection column for curators
    # - Version and metadata tracking
```

### Technical Implementation (From Code Analysis)

#### Candidate Data Model
```python
class Candidate(BaseModel):
    value: str          # OCR extracted text
    engine: str         # Engine that produced candidate
    confidence: float   # Confidence score (0.0-1.0)
    error: bool        # Error flag for failed extractions

class Decision(BaseModel):
    value: str         # Selected candidate value
    engine: str        # Engine that produced selected value
    run_id: str | None # Processing run identifier
    decided_at: str    # ISO timestamp of decision
```

#### Review Bundle Structure
```
review_v1.2.0.zip
├── candidates.db          # SQLite database with candidates/decisions
├── manifest.json         # Bundle metadata and integrity info
├── export_version.txt    # Version tracking
└── images/              # Specimen images for review
    ├── specimen_001.jpg
    ├── specimen_002.jpg
    └── ...
```

#### Database Schema (Inferred)
```sql
-- Candidates table
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    image TEXT NOT NULL,
    value TEXT NOT NULL,
    engine TEXT NOT NULL,
    confidence REAL NOT NULL,
    error BOOLEAN DEFAULT FALSE
);

-- Decisions table
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    image TEXT NOT NULL,
    value TEXT NOT NULL,
    engine TEXT NOT NULL,
    decided_at TEXT NOT NULL
);
```

#### Workflow Integration
```python
# Export workflow
def create_review_bundle(schema_version: str):
    # 1. Package candidates.db
    # 2. Include relevant images
    # 3. Generate manifest with metadata
    # 4. Create versioned ZIP archive

# Import workflow
def import_decisions(dest: Session, src: Session):
    # 1. Extract decisions from source
    # 2. Check for conflicts in destination
    # 3. Merge with duplicate detection
    # 4. Preserve audit trail
```

### Success Criteria (Observed)
- ✅ Multiple review interfaces accommodating different curator preferences
- ✅ Self-contained review bundles enabling offline and distributed workflows
- ✅ Comprehensive audit trail with timestamp and curator attribution
- ✅ Conflict detection preventing data loss from concurrent reviews
- ✅ Spreadsheet integration for team-based review workflows
- ✅ Version tracking and manifest-based integrity validation

### Quality Attributes
- **Usability**: Multiple interfaces serve different curator preferences and contexts
- **Reliability**: Conflict detection and audit trails prevent data loss
- **Scalability**: Bundle-based distribution enables team collaboration
- **Traceability**: Complete decision history with timestamp and attribution
- **Flexibility**: Spreadsheet integration supports institutional review workflows
- **Integrity**: Manifest-based validation ensures bundle completeness

### Decisions Made (Inferred from Implementation)

#### Multi-Interface Strategy
- **Design Philosophy**: Provide options rather than force single workflow
- **CLI**: Minimal interface for quick decisions
- **TUI**: Rich terminal experience with image preview
- **Web**: Full-featured browser interface for detailed review
- **Spreadsheet**: Institutional workflow compatibility

#### Bundle Architecture
- **Self-Contained**: Include all necessary data and images
- **Versioned**: Semantic versioning for bundle tracking
- **Manifest-Based**: Integrity validation and metadata tracking
- **ZIP Format**: Standard archive format for portability

#### Data Management Strategy
- **SQLite Database**: Embedded database for candidate/decision storage
- **Pydantic Models**: Type-safe data structures with validation
- **Conflict Detection**: Prevent duplicate decisions during import
- **Audit Trail**: Complete history preservation with timestamps

## Critical Decision Points Identified

### Should Have Been Specified Upfront

#### 1. **Review Workflow Strategy**
- **Missing**: Clear definition of review responsibilities and quality thresholds
- **Impact**: Unclear when reviews are "complete" or decisions are "final"
- **Resolution**: Ad-hoc review completion without formal criteria

#### 2. **Conflict Resolution Strategy**
- **Missing**: How to handle disagreements between reviewers
- **Impact**: Import failures when multiple curators review same images
- **Resolution**: Simple conflict detection without resolution workflow

#### 3. **Quality Assurance Requirements**
- **Missing**: What percentage of images require review? What accuracy is acceptable?
- **Impact**: No systematic approach to review prioritization
- **Resolution**: Manual review selection without quality metrics

#### 4. **User Experience Requirements**
- **Missing**: What review throughput is expected? How long should reviews take?
- **Impact**: No optimization for curator efficiency or ergonomics
- **Resolution**: Basic interfaces without workflow optimization

#### 5. **Integration Requirements**
- **Missing**: How does review integrate with institutional curatorial systems?
- **Impact**: Manual export/import without automated workflows
- **Resolution**: Standalone system requiring manual integration

### Technical Decisions Missing Documentation

#### Interface Selection Criteria
- **Choice**: Four different review interfaces
- **Rationale**: Accommodate different curator preferences vs complexity
- **Trade-offs**: High maintenance burden vs user flexibility

#### Bundle Distribution Model
- **Choice**: ZIP archives with embedded database
- **Rationale**: Self-contained packages vs centralized review system
- **Trade-offs**: Manual distribution vs automated workflow integration

#### Decision Data Model
- **Choice**: Simple value/engine/timestamp recording
- **Rationale**: Minimal metadata vs comprehensive decision context
- **Trade-offs**: Limited analysis capabilities vs storage efficiency

#### Conflict Detection Strategy
- **Choice**: Import-time conflict detection vs preventive locking
- **Rationale**: Simple implementation vs concurrent review support
- **Trade-offs**: Review workflow interruption vs system complexity

### Integration Complexity Not Addressed

#### Institutional Workflow Integration
- **Issue**: No integration with existing curatorial management systems
- **Risk**: Manual data transfer introduces errors and inefficiency
- **Missing**: API interfaces and automated workflow integration

#### Review Quality Management
- **Issue**: No systematic approach to review quality assurance
- **Risk**: Inconsistent review standards and curator bias
- **Missing**: Inter-curator agreement metrics and quality monitoring

#### Performance Optimization
- **Issue**: No optimization for large-scale review workflows
- **Risk**: Poor curator experience with large image collections
- **Missing**: Batch review capabilities and workflow optimization

#### Version Control Integration
- **Issue**: Bundle versioning separate from main processing pipeline
- **Risk**: Version drift between processing and review data
- **Missing**: Integrated version management across processing and review

## Lessons for Future Specifications

### What Worked Well
- **Multi-Interface Strategy**: Successfully accommodates diverse curator preferences
- **Self-Contained Bundles**: Enables offline and distributed review workflows
- **Audit Trail Design**: Comprehensive decision tracking with proper attribution
- **Conflict Detection**: Prevents data loss from concurrent review workflows

### Missing from Original Development
- **Review Quality Metrics**: No systematic approach to measuring review effectiveness
- **Workflow Optimization**: Limited focus on curator efficiency and ergonomics
- **Integration Planning**: No strategy for institutional system integration
- **Performance Analysis**: No testing of review throughput and scalability

### Critical Gaps That Should Have Been Addressed

#### 1. **Review Quality Framework**
```markdown
## Required Specification
**Quality Metrics**: Inter-curator agreement rates, review completion times
**Review Standards**: Accuracy thresholds, quality assurance protocols
**Performance Monitoring**: Curator efficiency metrics, error detection rates
**Training Integration**: Onboarding workflows and competency validation
```

#### 2. **Institutional Integration Strategy**
```markdown
## Required Specification
**API Design**: Programmatic interfaces for review data integration
**Workflow Automation**: Automated distribution and collection of review bundles
**System Integration**: Connections to existing curatorial management systems
**Compliance Support**: Audit trail formats for institutional requirements
```

#### 3. **Scalability and Performance Framework**
```markdown
## Required Specification
**Throughput Requirements**: Target review rates and batch processing capabilities
**User Experience Optimization**: Interface responsiveness and workflow efficiency
**Large Dataset Handling**: Strategies for collections with thousands of specimens
**Resource Management**: Database optimization and storage management
```

### Recommendation for Similar Features

1. **Define review quality standards early**
   - What constitutes a "good" review?
   - How do you measure and improve review quality?
   - What training and competency validation is required?

2. **Plan institutional integration from the start**
   - How will this integrate with existing systems?
   - What APIs and automation are needed?
   - How will data flow between systems?

3. **Optimize for curator experience**
   - What review throughput is expected?
   - How can interfaces be optimized for efficiency?
   - What training and support do curators need?

4. **Design for scale**
   - How will performance change with large datasets?
   - What are the storage and computational requirements?
   - How will you monitor and optimize performance?

5. **Plan version and workflow management**
   - How do review versions relate to processing versions?
   - What happens when processing data changes?
   - How do you handle review workflow errors and recovery?

## Future Enhancement Opportunities

### Immediate Improvements
- **Review Quality Metrics**: Inter-curator agreement measurement and reporting
- **Workflow Optimization**: Batch review capabilities and keyboard shortcuts
- **Performance Monitoring**: Review throughput and efficiency metrics
- **Conflict Resolution**: Workflow for handling reviewer disagreements

### Strategic Enhancements
- **Institutional Integration**: APIs for curatorial management system integration
- **Machine Learning Integration**: AI-assisted review prioritization and quality prediction
- **Advanced Analytics**: Review pattern analysis and curator performance insights
- **Mobile Interface**: Tablet-optimized review for field and remote workflows

This retroactive specification reveals that while the Quality Control Review System successfully implements a comprehensive multi-interface review capability with robust audit trails, it lacks systematic quality assurance, institutional integration planning, and performance optimization that would be essential for production deployment at institutional scale. The multi-interface strategy and self-contained bundle approach demonstrate excellent user-centric design thinking, but the absence of quality metrics and institutional workflow integration represents significant operational gaps.