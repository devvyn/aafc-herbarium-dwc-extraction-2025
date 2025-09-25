# AAFC Herbarium OCR Project - Claude Code Configuration

## Project Context
**Phase**: Production v0.2.0, preparing v1.0 release
**Tech Stack**: Python 3.11+, uv, OCR engines, Darwin Core standard
**Meta-Project Integration**: ~/devvyn-meta-project/ (head office coordination)

## Current Development Focus

### High Priority Patterns (from INTER_AGENT_MEMO)
1. **CSV Magic Reader**: Implement enhanced Darwin Core field access
   - Location: `src/utils/csv_magic.py`
   - Purpose: Cleaner GBIF data handling with scientific_name → scientificName mapping

2. **GBIF API Documentation**: Systematic integration testing methodology
   - Location: `scripts/api_exploration_template.py`
   - Purpose: Methodical approach to new API integrations

### Medium Priority
3. **OCR Engine Evaluation**: Standardized testing templates
   - Location: `docs/templates/jupyter_engine_evaluation.md`
   - Purpose: Consistent engine comparison methodology

4. **Label Pattern Analysis**: Validation utilities for OCR results
   - Location: `src/analysis/label_patterns.py`
   - Purpose: Collector name normalization, date standardization

## Development Guidelines
- Maintain Python 3.11+ compatibility
- Use uv for dependency management
- Follow ruff formatting standards
- Comprehensive testing required
- Link to original gist sources for attribution

## Critical Targets for v1.0
- Finalize Darwin Core export functionality
- Complete GBIF integration testing
- Implement enhanced OCR validation
- Production-ready documentation

## Inter-Workspace Communication
- **Strategic decisions**: Check ~/devvyn-meta-project/key-answers.md
- **Progress updates**: Update INTER_AGENT_MEMO.md with implementation status
- **Blockers/resources**: Escalate to meta-project status files

## Sync Command Response Protocol
When issuing sync command:
1. Read INTER_AGENT_MEMO.md for current patterns
2. Check recent git activity for context
3. Identify immediate development priorities
4. Focus on gist-proven patterns over new solutions
5. Report progress back to meta-project coordination

## Reference Files
- `INTER_AGENT_MEMO.md`: Proven development patterns from historical analysis
- `README.md`: Current project status and installation
- `CHANGELOG.md`: Version history and feature progression

---
**Meta-Project Path**: /Users/devvynmurphy/devvyn-meta-project/
**Session Coordination**: key-answers.md for strategic consultation
**Pattern Source**: Historical gist analysis with battle-tested approaches