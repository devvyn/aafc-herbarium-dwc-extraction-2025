# AAFC Herbarium DWC Extraction - Multi-Agent Collaboration Workspace

**Context Level**: 3 (Project-Specific)
**Inherits From**: `~/devvyn-meta-project/CLAUDE.md` (Bridge v3.0, coordination protocols)
**User Tools**: `~/.claude/CLAUDE.md` (fd, uv, rg tool preferences)

**Framework Version**: 2.1 (Inclusive Collaboration Design)
**Project Tier**: 1 (Production-Critical)
**Agent Authority**: Technical implementation, pattern application, optimization
**Human Authority**: Scientific validation, stakeholder communication, strategic priorities

## Project Context

This toolkit extracts Darwin Core data from herbarium specimen images using OCR and AI assistance. Built for Agriculture and Agri-Food Canada (AAFC) with production-ready processing capabilities.

## Multi-Agent Collaboration Benefits

### Agent Strengths Applied
- **Pattern Recognition**: Implementing proven gist patterns from historical development
- **Technical Optimization**: OCR engine evaluation, performance tuning, code quality
- **Architecture Decisions**: Pipeline design, error handling, modular system structure
- **Quality Assurance**: Automated testing, validation protocols, data integrity

### Human Domain Preserved
- **Scientific Accuracy**: Taxonomic validation, specimen interpretation, domain expertise
- **Stakeholder Relations**: AAFC communication, requirements gathering, success criteria
- **Strategic Direction**: Research priorities, publication planning, institutional goals
- **Quality Standards**: Acceptable accuracy thresholds, output format requirements

## Shared Authority Implementation

### Git Commit Protocol (CRITICAL)

**Rule**: Commit and push every 30-45 minutes of development work or after completing any significant feature.

**When to commit**:
- ✅ After implementing a new feature or module
- ✅ After fixing a bug or passing new tests
- ✅ Before starting a risky refactor
- ✅ After creating important documentation
- ✅ Every 30-45 minutes during active development

**Commit checklist**:
1. `git status` - Review changes
2. `git add <files>` - Stage relevant changes (exclude test directories)
3. `git commit -m "..."` - Write clear commit message
4. `git push` - Push to GitHub immediately

**Why**: GitHub is the safe storage. Local work can be lost to crashes, context limits, or session ends. Frequent commits = no wipeout moments.

### Technical Implementation (Agent Authority)

**Pre-Commit Checks** (run before EVERY commit):
```bash
# Quick check (always run before commit)
uv run ruff check . --fix && \
uv run ruff format . && \
uv run python -m pytest tests/unit/ -q && \
git diff --check

# Full checks (for significant changes)
uv run python -m pytest tests/  # All tests
./test-regression.sh            # Regression validation
```

**Development Workflows**:
```bash
# Code quality
uv run ruff check src/ --fix    # Auto-fix issues
uv run ruff format src/         # Format code

# Testing
uv run python -m pytest tests/unit/     # Fast unit tests
uv run python -m pytest tests/          # Full test suite
./test-regression.sh                     # Database compatibility

# Integration testing
uv run python cli.py check-deps         # Verify dependencies
```

**Commit Frequency**:
- Every 30-45 minutes during active development
- After completing any significant feature
- Before starting risky refactors
- **ALWAYS after running pre-commit checks**

See [.github/PRE_COMMIT_CHECKLIST.md](.github/PRE_COMMIT_CHECKLIST.md) for complete workflow.

### Scientific Validation (Human Authority)
- Specimen identification accuracy assessment
- Darwin Core field mapping verification
- Taxonomic authority validation
- Output format compliance review

### Collaborative Decision Points
- **OCR Engine Selection**: Technical evaluation (agent) + accuracy requirements (human)
- **Performance Optimization**: Implementation approach (agent) + acceptable trade-offs (human)
- **Error Handling**: Technical patterns (agent) + business logic (human)
- **Feature Priorities**: Implementation feasibility (agent) + scientific value (human)

## Context Preservation Protocols

### INTER_AGENT_MEMO Integration
- **Historical Patterns**: CSV Magic Reader, API exploration templates, Jupyter evaluation workflows
- **Proven Solutions**: Character tree analysis, systematic testing, incremental validation
- **Future Guidance**: Battle-tested approaches from gist analysis inform new implementations

### Session Handoff Standards
```
## HANDOFF CONTEXT
**Project Phase**: [Current development focus]
**Technical State**: [Code status, pending changes, test results]
**Scientific Requirements**: [Accuracy needs, validation pending, stakeholder feedback]
**Next Priorities**: [Immediate technical tasks + scientific validation needs]
```

## v2.1 Optimization Features

### Context Efficiency
- **Session Design**: Focused technical sessions with clear handoff protocols
- **Pattern Reuse**: Historical gist patterns applied systematically
- **Quality Gates**: Automated validation before human scientific review

### Sustainable Collaboration
- **Technical Autonomy**: Agent handles implementation without micromanagement
- **Scientific Authority**: Human maintains domain expertise and quality control
- **Shared Success**: Both code quality AND scientific accuracy achieved

## Project Health Indicators

### Technical Health (Agent Domain)
- ✅ Code passes all linting and tests
- ✅ Performance benchmarks met
- ✅ Error handling comprehensive
- ✅ Documentation current

### Scientific Health (Human Domain)
- 🔬 Taxonomic accuracy validated
- 🔬 Darwin Core compliance verified
- 🔬 Stakeholder requirements met
- 🔬 Publication-ready outputs

### Collaboration Health (Shared)
- 🤝 Smooth technical-scientific handoffs
- 🤝 Authority domains respected
- 🤝 Quality outcomes achieved efficiently
- 🤝 Both human and agent satisfaction high

## Review Requests for Chat Agent

### Current Technical Questions
- [x] **OCR Engine Selection**: Apple Vision primary + remote API calls for gaps ✅
- [x] **Memory Optimization**: 2GB/1000 images acceptable for production ✅
- [x] **Scientific Validation**: Production data volume prioritized over perfect accuracy ✅

### Completed Reviews
- [x] **Darwin Core Mapping**: Field mapping validated by scientific team ✅
- [x] **Error Handling Strategy**: Exception-based monitoring approach approved ✅

*Add new requests here with [domain expertise needed]. Chat agent will review and provide guidance in INTER_AGENT_MEMO feedback sections.*

## Quick Start for Agents

### Current Project State
```bash
# Environment setup
uv sync && uv pip install -e .

# Verify functionality
./test-regression.sh

# Check current development focus
cat .coordination/INTER_AGENT_MEMO.md
```

### Key Implementation Guidelines
1. **Follow Historical Patterns**: Use proven solutions from .coordination/INTER_AGENT_MEMO
2. **Maintain Code Quality**: Ruff linting, comprehensive testing, clear documentation
3. **Optimize Performance**: Profile OCR engines, benchmark processing speed
4. **Preserve Scientific Accuracy**: Implement validation without changing domain logic

### Integration with Meta-Project
- **Status Updates**: Report to `/Users/devvynmurphy/devvyn-meta-project/status/`
- **Pattern Sharing**: Document new patterns for other projects
- **Capacity Management**: Tier 1 priority for resource allocation
- **Framework Evolution**: Contribute lessons learned to v2.1+ development

## Security Boundaries

**Inherits from**: `~/devvyn-meta-project/CLAUDE.md` Security Architecture

### Quick Reference

**SECRET** (requires approval): `~/Secrets/`, `*.env`, `*credentials*`, `*.key`
**PRIVATE** (logged access): `~/devvyn-meta-project/`, `~/infrastructure/`
**PUBLISHED** (full access): `~/Documents/GitHub/*` (this project)

### Project-Specific Security Notes

- **Herbarium specimen data**: PUBLISHED (publicly accessible scientific data)
- **S3 credentials**: SECRET (never include in code, use environment variables)
- **API keys** (.env files): SECRET (requires approval workflow)
- **Processing results**: PUBLISHED (scientific outputs for public use)
- **Strategy documents**: PRIVATE (meta-project coordination files)

**Before accessing credentials or .env files**: Create approval request using template at `~/infrastructure/agent-bridge/bridge/approval-requests/_template-secret-access.md`

**Full security protocols**: See `~/devvyn-meta-project/CLAUDE.md` Security Boundaries section

## KB Context Awareness

**Inherits from**: `~/devvyn-meta-project/CLAUDE.md` KB Context system

### Workspace Context for AAFC-SRDC

**At session start**, I load `.kb-context/context.yaml` which tells me:
- **Workspace**: AAFC-SRDC Saskatoon (work context)
- **Context areas**: Herbarium digitization, Darwin Core extraction, OCR optimization
- **People**: Devvyn Murphy, supervisor, AAFC-SRDC organization
- **Policies**: Public employee policies, public scientific data (no confidentiality concerns)

### Clue-Based Context

**When you mention these keywords**, I know we're in herbarium work context:
- "herbarium", "specimen", "Darwin Core"
- "AAFC", "SRDC", "Agriculture Canada"
- "OCR", "biodiversity", "scientific data"

### Context Logging

**Actions logged** to `~/.kb-conduit/logs/session.log` for:
- Debriefing agents (understand what was accomplished)
- Concierge agents (coordinate between work and personal contexts)
- Handoff between sessions (continuity)

**Load context**: Run `~/.kb-conduit/load-context.sh` at session start

---

**Multi-Agent Success**: This project demonstrates v2.1 principles where technical excellence (agent strength) combines with scientific expertise (human strength) to create superior research tools through genuine collaboration rather than human-tool interaction.
