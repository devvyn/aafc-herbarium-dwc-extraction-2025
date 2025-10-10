# Session Sync Protocol - AAFC Herbarium Project

**Framework**: Multi-Agent Collaboration v2.1
**Purpose**: Bidirectional communication between Claude Chat and Claude Code
**Project**: aafc-herbarium-dwc-extraction-2025

## Communication Protocol

### From Chat → Code
**Updated**: [Never updated yet]
**Priority**: [LOW/MEDIUM/HIGH] - [Brief description]
**Message**: [Specific guidance, feedback, or direction]
**Action Required**: [YES/NO] - [What specifically needs to be done]
**Context**: [Relevant background or decision point]

### From Code → Chat
**Updated**: [Never updated yet]
**Question**: [Specific question or clarification needed]
**Context**: [Relevant code, decision point, or implementation detail]
**Priority**: [blocking/important/background]
**Blocking**: [YES/NO] - [What is blocked]

## Usage Guidelines

### For Chat Agent Updates
- Update when providing strategic guidance that affects current work
- Set priority based on impact: HIGH=blocking work, MEDIUM=affects decisions, LOW=background info
- Be specific about required actions
- Include timestamp in format: 2025-MM-DDTHH:MM:SSZ

### For Code Agent Updates
- Post questions when needing clarification on scientific/strategic matters
- Mark as blocking if it prevents forward progress
- Provide sufficient context for informed responses
- Include relevant code snippets or decision points

### Checking Protocol
Code agent checks this file:
- At session start
- Before major architectural decisions
- When explicitly mentioned by human
- After completing significant tasks

Chat agent checks this file:
- When human references questions from Code agent
- During strategic planning sessions
- When providing project guidance

## Integration with Existing Files

- **key-answers.md**: Strategic decisions, research priorities (unchanged)
- **INTER_AGENT_MEMO.md**: Historical patterns, proven solutions (enhanced with feedback)
- **session-sync.md**: Active session coordination (new)

---

**Status**: Template created, ready for use
**Next**: Update other communication files with protocol references
