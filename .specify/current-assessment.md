# Quick Feature Assessment Template

Use this template for rapid evaluation of whether a feature requires full specification.

## Feature: [Name]

**Effort Estimate**:
- [ ] < 1 day (Simple change, single function/file)
- [ ] 1-3 days (Moderate change, multiple functions, limited scope)
- [ ] > 3 days (Complex change, multiple modules, significant scope)

**Scope Assessment**:
- [ ] Single module (Changes confined to one component)
- [ ] Cross-module (Changes affect multiple components)
- [ ] Architecture (Changes affect system design or external dependencies)

**Risk Assessment**:
- [ ] Low (Well-understood change, minimal dependencies)
- [ ] Medium (Some complexity, moderate dependencies)
- [ ] High (Complex interactions, significant dependencies, performance impact)

**External Dependencies**:
- [ ] None (Self-contained within existing codebase)
- [ ] API/Service (Requires external API or service integration)
- [ ] Library (Requires new library or significant library changes)
- [ ] Platform (Platform-specific functionality or requirements)

## Decision Matrix

**Full Specification Required If Any Of:**
- [ ] Effort > 3 days
- [ ] Scope = Cross-module OR Architecture
- [ ] Risk = High
- [ ] External Dependencies = API/Service, Library, or Platform

**Alternative: Lightweight Documentation Required If:**
- [ ] Effort = 1-3 days AND Scope = Single module AND Risk = Low/Medium

**Simple Implementation If:**
- [ ] Effort < 1 day AND Scope = Single module AND Risk = Low

## Recommended Action

Based on the assessment above:

- [ ] **Full Specification** → Use `/specify` workflow (spec → clarify → plan → tasks → implement)
- [ ] **Lightweight Documentation** → Document in commit message with purpose, approach, and testing
- [ ] **Simple Implementation** → Proceed with implementation, document rationale in commit

## Lightweight Documentation Template (if applicable)

```markdown
## Feature: [Name]
**Purpose**: What problem this solves
**Approach**: How it's implemented (key decisions and rationale)
**Testing**: How it's validated (tests added/modified)
**Impact**: What changes and what remains the same
```

## Notes

- When in doubt, choose the more rigorous option
- Complex features discovered during implementation should trigger specification upgrade
- Architecture changes always require full specification regardless of effort estimate