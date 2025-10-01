<!--
Sync Impact Report (2025-09-27):
- Version change: Initial template → 1.0.0
- Initial constitution creation from project analysis
- Added sections: Core Principles (5), Scientific Standards, Technical Requirements, Governance
- Templates requiring updates: ✅ constitution created / ⚠ plan/spec/tasks templates need alignment
- Follow-up TODOs: None - all placeholders filled
-->

# AAFC Herbarium DWC Extraction Constitution

## Core Principles

### I. Scientific Accuracy (NON-NEGOTIABLE)
Darwin Core data extraction must maintain taxonomic precision and specimen integrity. All outputs require scientific validation before publication. Accuracy takes precedence over speed - 95% taxonomic accuracy minimum for production use. Domain expertise from AAFC scientists preserved throughout development.

### II. Dual-Nature Architecture
System explicitly supports both extraction (images → data) and curation (data → standards) paradigms. Extraction layer handles OCR processing, curation layer manages review workflow. Clear separation prevents architectural confusion and over-complexity.

### III. Multi-Agent Collaboration Framework
Technical implementation delegated to agents, scientific validation retained by human experts. Agent authority covers code quality, performance optimization, architectural decisions. Human authority covers taxonomic accuracy, stakeholder relations, scientific requirements.

### IV. Pattern-Driven Development
Proven solutions from INTER_AGENT_MEMO and historical gists take precedence over new approaches. CSV Magic Reader, GBIF API methodologies, and OCR evaluation templates provide battle-tested foundations. Innovation occurs within established patterns.

### V. Production-Ready Quality Gates
All code passes ruff linting, comprehensive testing, and performance benchmarks before deployment. Memory usage optimized for 2,800+ specimen processing. Error handling comprehensive with audit trails for institutional compliance.

## Scientific Standards

Darwin Core field mapping validated by AAFC domain experts. Taxonomic authority verification through GBIF integration. Specimen interpretation maintains botanical accuracy. Publication-ready outputs meet institutional standards.

## Technical Requirements

Python 3.11+ compatibility maintained. UV package management for dependency control. OCR engines evaluated systematically with performance metrics. Database schema supports audit trails and multi-source data integration.

## Governance

Constitution supersedes conflicting development practices. All feature additions must align with dual-nature architecture. Scientific accuracy validation required before technical completion. Multi-agent collaboration boundaries respected - no micromanagement of technical implementation, no automated override of scientific decisions.

Code reviews verify constitutional compliance. Pattern adherence documented in commit messages. INTER_AGENT_MEMO patterns referenced for consistency.

**Version**: 1.0.0 | **Ratified**: 2025-09-27 | **Last Amended**: 2025-09-27