# Agent Documentation Outline

## Overview
This document provides a quick reference to all documentation that primarily instructs automated agents, scripts, and AI tools working on this repository.

## Primary Agent Instruction Documents

### 1. `/AGENTS.md` - Repository-level agent guidelines
**Purpose**: General development conventions for AI agents and scripts
**Key sections**:
- Data & folder conventions (`./input/`, `./output/`, SQLite usage)
- Digitization workflow separation (pipeline vs main database)
- Export versioning with semantic tags
- Coding style (Ruff formatting, PEP 8)
- Commit & PR guidelines (gitmoji, small focused commits)
- Issue management (GitHub syntax, roadmap updates)
- Release guidelines (substantial changes only)
- **Complete release process** (version updates, git tagging, CHANGELOG verification)
- Human-in-the-loop generative development

### 2. `/docs/AGENTS.md` - Documentation-specific agent guidelines
**Purpose**: Instructions for agents working on documentation
**Key sections**:
- Documentation formatting (Markdown, sentence-case headings)
- Workflow organization (preprocessing → OCR → mapping → QC → import → export)
- Link conventions (relative links, no duplication)
- Testing requirements (`ruff check docs`, `pytest`)
- Issue management synchronization
- **Release and version management** (coordinate with complete release process)

### 3. `/dwc/AGENTS.md` - Darwin Core module agent guidelines
**Purpose**: Instructions for agents working on DwC/ABCD data modules
**Key sections**:
- Schema management (`schema.py` canonical terms, consistent ordering)
- Mapping logic (`mapper.py`, `normalize.py` pure functions)
- ABCD field conventions (comments with equivalent terms)
- Testing requirements (module-specific linting and tests)

## Supporting Automation

### 4. `/scripts/create_roadmap_issues.py`
**Purpose**: "Designed for agents that manage issue trackers and project boards"
**Function**: Creates GitHub issues from roadmap entries and syncs to GitHub Projects
**Usage**: Referenced in `/docs/roadmap.md` for automated agent workflows

### 5. `/docs/roadmap.md`
**Purpose**: Strategic priorities with agent automation integration
**Agent features**:
- References issue creation script for automated workflows
- Designed to sync with GitHub Projects for automated agents
- Links roadmap entries to GitHub issues for tracking

## Document Tree Structure

```
Repository Root
├── AGENTS.md                    # Primary agent guidelines
├── docs/
│   ├── AGENTS.md               # Documentation agent guidelines
│   └── roadmap.md              # Strategic priorities with automation
├── dwc/
│   └── AGENTS.md               # Darwin Core module guidelines
└── scripts/
    └── create_roadmap_issues.py # Agent-designed issue automation
```

## Agent Workflow Integration

**Issue Management Flow**:
1. Agent reads `/docs/roadmap.md` for strategic priorities
2. Uses `/scripts/create_roadmap_issues.py` to sync roadmap with GitHub
3. Follows `/AGENTS.md` for commit/PR conventions
4. Updates documentation per `/docs/AGENTS.md` guidelines
5. Handles DwC modules per `/dwc/AGENTS.md` guidelines

**Quality Assurance**:
- All documents require `ruff check` and `pytest` before commits
- GitHub issue linking (`#123`) required for traceability
- Roadmap synchronization after issue resolution

## Quick-start Alignment Checklist

Use this checklist when a new human or automated contributor joins mid-stream so context survives narrow windows:

1. **Confirm scope** – skim this outline, then jump to the scoped `AGENTS.md` files that match the task (code, docs, or DwC modules).
2. **Sync roadmap** – review the active entry in `docs/roadmap.md` and note any open questions or blockers for handoff.
3. **State assumptions** – log current decisions, TODOs, and outstanding QA in the working document or issue thread for the next collaborator.
4. **Reference QA gates** – explicitly note which checks (e.g., `ruff`, `pytest`, DwC validators) have run so successors avoid duplication.
5. **Queue human review** – flag any steps requiring curator sign-off in `HUMAN_WORK_LIST.md` or the relevant issue to keep human-in-the-loop commitments visible.

## Handoff Notes Template

When switching between Claude, Codex, or human partners, append a short checklist to the issue or PR description using the following structure:

```
Scope: <docs | code | dwc | mixed>
Instructions consulted: [/AGENTS.md](../AGENTS.md), [/docs/AGENTS.md](AGENTS.md), [/dwc/AGENTS.md](../dwc/AGENTS.md)
Current roadmap item: <link to docs/roadmap.md section or issue>
QA status: ruff ✅ / pytest ✅ / other tools (list)
Next actions: <bullet list of remaining steps or questions>
Human review needed: <yes/no + pointer to HUMAN_WORK_LIST.md entry>
```

This lightweight template mirrors the repository’s commit and release conventions, helping collaborators realign without rereading the full documentation stack.

## Key Principles for Agents

1. **Separation of Concerns**: Pipeline vs main database separation
2. **Reproducibility**: Semantic versioning, commit hashes, timestamps
3. **Traceability**: GitHub issue linking, audit trails
4. **Quality**: Automated testing and linting before commits
5. **Release integrity**: Git tags must match CHANGELOG version references
6. **Human-in-the-loop**: Small reviewable steps, early feedback
7. **Documentation synchronization**: Update roadmap when closing issues
