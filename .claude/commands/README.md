# Hybrid Agent Orchestration Commands

Bridge integration commands that combine Claude Code's native `/agents` system with the bridge system for comprehensive multi-agent coordination.

## Commands Overview

### Core Integration Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/bridge-agent-create` | Create native subagent with bridge integration | `[type] [name] [description]` |
| `/session-handoff` | Coordinate between agent sessions via bridge | `[target-agent] [priority] [title]` |
| `/sync-with-native` | Synchronize bridge and native agent states | `[action]` |

### Bridge Extraction Support

| Command | Description | Usage |
|---------|-------------|-------|
| `/bridge-extraction-prep` | Prepare for bridge system extraction | `[phase]` |
| `/extraction-verify` | Verify bridge operation during transition | `[test-type]` |

## Quick Start

### 1. Create Your First Hybrid Agent
```bash
/bridge-agent-create darwin-core "DwC Validator" "Validates taxonomic accuracy and Darwin Core compliance"
```

### 2. Test System Health
```bash
/sync-with-native health-check
```

### 3. Coordinate with Other Agents
```bash
/session-handoff chat HIGH "Ready for strategic review"
```

### 4. Prepare for Infrastructure Evolution
```bash
/bridge-extraction-prep ready-check
```

## Agent Types

### Specialized Agent Types
- **`darwin-core`**: Taxonomic validation and Darwin Core compliance
- **`ocr-benchmark`**: OCR engine evaluation and performance testing
- **`pattern-analysis`**: Historical pattern application from INTER_AGENT_MEMO
- **`scientific-review`**: Scientific accuracy and domain expertise validation

Each type comes pre-configured with appropriate tools, models, and specialized prompts.

## Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐
│ Claude Code     │    │ Bridge System   │
│ Native /agents  │◄──►│ Cross-session   │
│ (tactical)      │    │ (strategic)     │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
              Hybrid Commands
         (Best of both worlds)
```

### Benefits of Hybrid Approach
- **Native Strengths**: Immediate delegation, tool configuration, model selection
- **Bridge Strengths**: Cross-session persistence, multi-project coordination
- **Integration**: Seamless coordination between tactical and strategic orchestration

## Bridge Extraction Ready

All commands are designed to work across bridge system locations:
- Current: `~/devvyn-meta-project/bridge/`
- Future: `~/infrastructure/agent-bridge/bridge/`

Commands automatically detect the bridge location and work seamlessly during the extraction transition.

## Usage Patterns

### Scientific Research Workflow
```bash
# 1. Create specialized agents
/bridge-agent-create ocr-benchmark "OCR Tester"
/bridge-agent-create darwin-core "Taxonomic Validator"

# 2. Coordinate research phases
/session-handoff ocr-tester NORMAL "Ready for engine evaluation"
/session-handoff human CRITICAL "Scientific validation needed"

# 3. Maintain system health
/sync-with-native status
```

### Development Workflow
```bash
# 1. Check system state
/sync-with-native health-check

# 2. Create task-specific agent
/bridge-agent-create pattern-analysis "Pattern Expert"

# 3. Hand off between sessions
/session-handoff chat HIGH "Implementation complete, need strategic review"
```

### Infrastructure Migration
```bash
# 1. Prepare for extraction
/bridge-extraction-prep validate
/bridge-extraction-prep backup

# 2. Verify during transition
/extraction-verify connectivity
/extraction-verify messaging

# 3. Confirm post-migration
/sync-with-native health-check
```

## Configuration

### Agent Storage
- Native agent configs: `.claude/commands/agents/[agent-name].json`
- Bridge registrations: Auto-managed via bridge system
- Coordination state: Maintained in bridge message queue

### Path Resolution
Commands automatically resolve bridge paths:
1. `~/infrastructure/agent-bridge/` (post-extraction)
2. `~/devvyn-meta-project/` (current)
3. Error if neither found

## Troubleshooting

### Common Issues

**Agent creation fails:**
```bash
/sync-with-native health-check  # Check system state
/bridge-extraction-prep validate  # Verify bridge integrity
```

**Session handoff not received:**
```bash
# Check bridge queue
ls ~/devvyn-meta-project/bridge/queue/pending/
# Or post-extraction:
ls ~/infrastructure/agent-bridge/bridge/queue/pending/
```

**Bridge extraction concerns:**
```bash
/bridge-extraction-prep backup     # Create safety backup
/extraction-verify rollback        # Verify rollback capability
```

## Integration with Project Framework

These commands integrate with the multi-agent collaboration framework v2.1:
- **Technical Authority**: Agent orchestration and coordination
- **Human Authority**: Scientific validation and strategic direction
- **Shared Success**: Both code quality AND scientific accuracy

The hybrid orchestration system preserves authority domains while enabling seamless coordination across agent types and session boundaries.