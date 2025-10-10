# Architecture Decision Record Template

Use this template for documenting significant architecture decisions that impact system design, external dependencies, or long-term maintainability.

## ADR-[NUMBER]: [Decision Title]

**Date**: [YYYY-MM-DD]
**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Deciders**: [List of people involved in decision]
**Technical Story**: [Reference to issue/requirement that triggered this decision]

## Context and Problem Statement

[Describe the context and problem statement that led to this decision. What circumstances require this decision? What constraints or forces are at play?]

### Current Situation
- [Describe existing state]
- [Highlight problems or limitations]
- [Note any time or resource constraints]

### Requirements
- [List functional requirements]
- [List non-functional requirements (performance, security, etc.)]
- [List institutional or compliance requirements]

## Decision Drivers

[List the key factors that influenced this decision]

- [Driver 1: e.g., Performance requirements]
- [Driver 2: e.g., Cost constraints]
- [Driver 3: e.g., Team expertise]
- [Driver 4: e.g., Integration requirements]

## Considered Options

### Option 1: [Name]
**Description**: [Brief description of approach]
**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Cost/Effort**: [Implementation effort and ongoing costs]
**Risk**: [Technical, operational, or business risks]

### Option 2: [Name]
**Description**: [Brief description of approach]
**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Cost/Effort**: [Implementation effort and ongoing costs]
**Risk**: [Technical, operational, or business risks]

### Option 3: [Name]
[Continue for additional options as needed]

## Decision Outcome

**Chosen Option**: [Selected option name]

**Rationale**: [Why this option was selected over others. Reference specific decision drivers and how this option addresses them best.]

### Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Success Metrics
- [How will we know this decision was successful?]
- [What metrics will we track?]
- [What are the acceptance criteria?]

## Consequences

### Positive Consequences
- [Expected benefits]
- [Capabilities enabled]
- [Problems solved]

### Negative Consequences
- [Trade-offs accepted]
- [Limitations introduced]
- [Technical debt incurred]

### Risk Mitigation
- [How will negative consequences be mitigated?]
- [What contingency plans exist?]
- [When should this decision be revisited?]

## Implementation Details

### Technical Changes Required
- [Code changes needed]
- [Configuration updates]
- [Database schema changes]
- [Infrastructure modifications]

### Dependencies
- [External libraries or services]
- [Internal system dependencies]
- [Team skill requirements]

### Migration Strategy
- [How to transition from current state]
- [Backward compatibility considerations]
- [Rollback procedures]

## Validation and Testing

### Validation Plan
- [How will the decision be validated?]
- [What tests are needed?]
- [Performance benchmarks]
- [Security validation]

### Monitoring
- [What metrics will be monitored post-implementation?]
- [What alerts or thresholds should be set?]
- [How often should effectiveness be reviewed?]

## Follow-up Actions

- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] [Review date: when to reassess this decision]

## References

- [Links to relevant documentation]
- [Research papers or articles consulted]
- [Related ADRs]
- [Meeting notes or discussion records]

---

**Notes for Authors**:
- Keep technical jargon to a minimum
- Focus on business and technical rationale
- Include sufficient context for future readers
- Update status as decision progresses through lifecycle
- Reference this ADR in related implementation work
