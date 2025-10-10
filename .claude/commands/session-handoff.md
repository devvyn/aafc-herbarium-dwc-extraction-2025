---
name: session-handoff
description: Coordinate with other agents via bridge system with context preservation
usage: /session-handoff [target-agent] [priority] [message-title]
args:
  - name: target-agent
    description: Target agent (chat, gpt, codex, human, bspec, or custom agent name)
    required: true
  - name: priority
    description: Message priority (CRITICAL, HIGH, NORMAL, LOW)
    required: false
    default: NORMAL
  - name: message-title
    description: Brief message title
    required: false
---

# Session Handoff Coordinator

Coordinates between agent sessions using the bridge system with automatic context preservation and intelligent handoff protocols.

## Usage Examples

```bash
/session-handoff chat HIGH "OCR Evaluation Complete - Need Strategic Review"
/session-handoff human CRITICAL "Scientific Validation Required"
/session-handoff gpt NORMAL "Documentation Generation Request"
/session-handoff darwin-core-validator NORMAL "Ready for DwC Compliance Check"
```

## Implementation

```bash
#!/bin/bash

# Parse arguments
TARGET_AGENT="$1"
PRIORITY="${2:-NORMAL}"
MESSAGE_TITLE="${3:-Session Handoff Request}"

# Validate arguments
if [ -z "$TARGET_AGENT" ]; then
    echo "Usage: /session-handoff [target-agent] [priority] [message-title]"
    echo "Target agents: chat, gpt, codex, human, bspec, or custom agent name"
    echo "Priorities: CRITICAL, HIGH, NORMAL, LOW"
    exit 1
fi

# Validate priority
case "$PRIORITY" in
    CRITICAL|HIGH|NORMAL|LOW) ;;
    *)
        echo "Invalid priority: $PRIORITY"
        echo "Valid priorities: CRITICAL, HIGH, NORMAL, LOW"
        exit 1
        ;;
esac

# Auto-detect bridge location (extraction-ready)
resolve_bridge_path() {
    if [ -d "$HOME/infrastructure/agent-bridge/bridge" ]; then
        echo "$HOME/infrastructure/agent-bridge"
    elif [ -d "$HOME/devvyn-meta-project/bridge" ]; then
        echo "$HOME/devvyn-meta-project"
    else
        echo "ERROR: Bridge system not found" >&2
        return 1
    fi
}

BRIDGE_ROOT=$(resolve_bridge_path) || exit 1

echo "🔄 Initiating session handoff to: $TARGET_AGENT"
echo "Priority: $PRIORITY"
echo "Bridge root: $BRIDGE_ROOT"

# Create handoff context file
HANDOFF_FILE="/tmp/session-handoff-$(date +%s).md"

cat > "$HANDOFF_FILE" << EOF
# Session Handoff: $MESSAGE_TITLE

**From**: code agent
**To**: $TARGET_AGENT
**Priority**: $PRIORITY
**Project**: $(basename $(pwd))
**Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Current Session Context

### Project State
- **Working Directory**: $(pwd)
- **Git Status**: $(git status --porcelain | wc -l) modified files
- **Current Branch**: $(git branch --show-current 2>/dev/null || echo "not a git repo")
- **Last Commit**: $(git log -1 --format="%h %s" 2>/dev/null || echo "no commits")

### Bridge System Status
- **Bridge Location**: $BRIDGE_ROOT
- **Queue Health**: $(ls "$BRIDGE_ROOT/bridge/queue/pending/" 2>/dev/null | wc -l) pending messages
- **Active Agents**: $(ls "$BRIDGE_ROOT/bridge/registry/" 2>/dev/null | grep -v "\.json" | wc -l) registered

### Development Context
$(if [ -f "CLAUDE.md" ]; then
    echo "**Project Instructions**: CLAUDE.md present"
    echo "**Framework Version**: $(grep "Framework Version" CLAUDE.md | head -1 | cut -d: -f2 | xargs)"
fi)

$(if [ -f "INTER_AGENT_MEMO.md" ]; then
    echo "**Inter-Agent Memo**: Available"
    echo "**Last Updated**: $(stat -f "%Sm" INTER_AGENT_MEMO.md 2>/dev/null || stat -c "%y" INTER_AGENT_MEMO.md 2>/dev/null || echo "unknown")"
fi)

$(if [ -f ".claude/commands/agents" ] && [ -d ".claude/commands/agents" ]; then
    echo "**Native Agents**: $(ls .claude/commands/agents/*.json 2>/dev/null | wc -l) configured"
fi)

### Recent Activity
$(echo "Recent git commits:")
$(git log --oneline -5 2>/dev/null || echo "No git history available")

### Current Task Context
$(if [ -f "session-sync.md" ]; then
    echo "**Session Sync**: Available"
    tail -10 session-sync.md
else
    echo "**Task Context**: No session-sync.md found"
fi)

## Handoff Request

**Requested Action**: $MESSAGE_TITLE

**Context for $TARGET_AGENT**:
$(case "$TARGET_AGENT" in
    "chat")
        echo "- Strategic review and framework guidance needed"
        echo "- Consider architectural implications and cross-project patterns"
        echo "- Provide high-level direction for technical implementation"
        ;;
    "gpt"|"codex")
        echo "- Content generation or algorithm development requested"
        echo "- Technical implementation guidance needed"
        echo "- Consider integration with existing codebase patterns"
        ;;
    "human")
        echo "- Human expertise or approval required"
        echo "- Scientific validation or stakeholder communication needed"
        echo "- Strategic decision or quality threshold confirmation"
        ;;
    "bspec")
        echo "- Specification development or validation needed"
        echo "- Requirements clarification or feature planning"
        echo "- Integration with spec-driven development workflow"
        ;;
    *)
        echo "- Specialized agent coordination requested"
        echo "- Check agent configuration in .claude/commands/agents/"
        echo "- Custom workflow or domain-specific task"
        ;;
esac)

## Recommended Next Steps

1. **Review Context**: Understand current project state and development phase
2. **Check Dependencies**: Verify any pending work or blockers
3. **Coordinate Response**: Use bridge system for coordination if needed
4. **Update Progress**: Document outcomes in appropriate project files

## Bridge Coordination

**Return Path**: Send responses to 'code' agent via bridge system
**Project Coordination**: Update INTER_AGENT_MEMO.md for cross-session continuity
**Status Updates**: Use session-sync.md for immediate coordination needs

---

**Bridge Message ID**: Will be auto-generated
**Handoff Complete**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

echo "📝 Context file created: $HANDOFF_FILE"

# Send via bridge system
echo "📤 Sending handoff message via bridge..."
if [ -f "$BRIDGE_ROOT/scripts/bridge-send.sh" ]; then
    "$BRIDGE_ROOT/scripts/bridge-send.sh" code "$TARGET_AGENT" "$PRIORITY" "$MESSAGE_TITLE" "$HANDOFF_FILE"

    if [ $? -eq 0 ]; then
        echo "✅ Handoff message sent successfully"
        echo "   Target: $TARGET_AGENT"
        echo "   Priority: $PRIORITY"
        echo "   Title: $MESSAGE_TITLE"

        # Check if target agent should be notified to check messages
        case "$TARGET_AGENT" in
            "chat"|"human")
                echo
                echo "💡 Suggestion: Notify $TARGET_AGENT to check bridge messages:"
                echo "   $BRIDGE_ROOT/scripts/bridge-receive.sh $TARGET_AGENT"
                ;;
        esac

    else
        echo "❌ Failed to send handoff message"
        echo "Debug: Check bridge system status"
        echo "Manual path: $HANDOFF_FILE"
        exit 1
    fi
else
    echo "❌ Bridge send script not found at $BRIDGE_ROOT/scripts/bridge-send.sh"
    echo "Manual handoff file created at: $HANDOFF_FILE"
    exit 1
fi

# Update local session tracking
if [ -f "session-sync.md" ]; then
    echo >> session-sync.md
    echo "## Handoff: $(date)" >> session-sync.md
    echo "- **Target**: $TARGET_AGENT ($PRIORITY)" >> session-sync.md
    echo "- **Message**: $MESSAGE_TITLE" >> session-sync.md
    echo "- **Status**: Sent via bridge system" >> session-sync.md
    echo "📝 Updated session-sync.md with handoff record"
fi

# Clean up temporary file (keep for debugging if send failed)
if [ $? -eq 0 ]; then
    rm -f "$HANDOFF_FILE"
fi

echo
echo "🎯 Session handoff complete!"
echo "Next: Monitor bridge for responses or continue with other tasks"
```
