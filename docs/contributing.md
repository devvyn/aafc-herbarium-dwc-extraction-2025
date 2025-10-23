# Contributing

## Quick Start

1. **Install dependencies**: Run `./bootstrap.sh`
2. **Read guidelines**: See [AGENTS.md](AGENTS.md) for development conventions
3. **Before every commit**: Run pre-commit checks (see [Pre-Commit Checklist](.github/PRE_COMMIT_CHECKLIST.md))
4. **Open PR**: Include `Resolves #<issue-number>` if closing an issue

### Essential Pre-Commit Workflow

```bash
# Quick check before EVERY commit
uv run ruff check . --fix && \
uv run ruff format . && \
uv run python -m pytest tests/unit/ -q && \
git diff --check
```

**Why?** Catches 95% of issues before CI runs. See complete checklist: [.github/PRE_COMMIT_CHECKLIST.md](.github/PRE_COMMIT_CHECKLIST.md)

Review [development.md](docs/development.md) for development conventions and consult the [roadmap](docs/roadmap.md) for open tasks and priorities.

## Spec-Driven Development Workflow

This project follows **spec-driven development** using GitHub's spec-kit. All new features must follow this workflow:

### 1. Constitution Compliance
Before starting any feature, review the [project constitution](.specify/memory/constitution.md) to ensure alignment with:
- Scientific accuracy requirements (95%+ taxonomic accuracy)
- Dual-nature architecture (extraction vs curation layers)
- Multi-agent collaboration framework
- Pattern-driven development principles

### 2. Feature Specification Process

#### 2a. Quick Assessment (Required for All Changes)
Before any development, assess whether full specification is needed:

```bash
# Copy assessment template
cp .specify/templates/quick-feature-assessment.md .specify/current-assessment.md

# Complete assessment to determine approach:
# - Full Specification: Complex features requiring /specify workflow
# - Lightweight Documentation: Moderate changes with commit documentation
# - Simple Implementation: Minor changes with rationale
```

#### 2b. Full Specification Workflow (For Complex Features)
For features requiring full specification, use the spec-driven workflow:

```bash
# Create feature specification
/specify "Your feature description here"

# Resolve ambiguities
/clarify

# Create implementation plan
/plan

# Generate actionable tasks
/tasks

# Execute implementation
/implement
```

#### 2c. Architecture Decisions (When Applicable)
For significant architecture decisions, document using ADR template:

```bash
# Copy ADR template
cp .specify/templates/architecture-decision-record.md .specify/decisions/adr-XXX-decision-name.md
# Complete with decision context, options, and rationale
```

### 3. Specification Review Gates
All specifications must pass these quality gates:
- **No implementation details** - Focus on WHAT users need, not HOW to build it
- **Testable requirements** - Every requirement must be verifiable
- **Scientific validation** - Domain experts must approve taxonomic/botanical aspects
- **Constitution compliance** - Features must align with core principles

### 4. Branch Strategy for Specs
- Specifications live in feature branches: `001-feature-name`, `002-feature-name`
- Each spec includes complete user scenarios, requirements, and acceptance criteria
- Merge specs to main only after stakeholder approval
- Implementation follows in separate development branches

### 5. Commit Message Standards

All commits must reference appropriate specification documents:

```bash
# Full specification features
git commit -m "feat: implement user authentication system

Ref: .specify/features/001-user-auth/spec.md
ADR: .specify/decisions/adr-001-auth-strategy.md
Tasks: Completes tasks 1-3 from implementation plan"

# Lightweight documentation features
git commit -m "refactor: optimize database query performance

Purpose: Reduce query time from 2s to 500ms for large datasets
Approach: Added compound index on (user_id, created_at) columns
Testing: Added performance test with 10k record benchmark
Impact: Affects user dashboard load time, no API changes"

# Simple implementations
git commit -m "fix: correct typo in error message

Rationale: User reported unclear error message in validation
Change: Updated 'Invalid input' to 'Email format invalid'
Testing: Manual verification of error display"
```

### 6. Pull Request Requirements

All PRs must include:
- **Specification Reference**: Link to relevant spec, ADR, or assessment
- **Testing Evidence**: Test results, screenshots, or validation proof
- **Breaking Changes**: Clear documentation of any breaking changes
- **Performance Impact**: Note any performance implications

### 7. Documentation Integration
- Central index: [SPECIFICATIONS.md](docs/architecture/SPECIFICATIONS.md)
- Architecture decisions: [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- Retroactive specifications: [.specify/retro-specs/](.specify/retro-specs/)
- Specification templates: [.specify/templates/](.specify/templates/)

This approach ensures features solve real user problems before technical implementation begins while maintaining comprehensive documentation of decisions and rationale.
