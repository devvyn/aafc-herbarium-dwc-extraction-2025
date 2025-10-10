---
name: sync-with-native
description: Synchronize bridge system state with native Claude Code agents
usage: /sync-with-native [action]
args:
  - name: action
    description: Sync action (status, register-all, cleanup, health-check)
    required: false
    default: status
---

# Bridge-Native Agent Synchronizer

Synchronizes the bridge system state with native Claude Code `/agents` subagents, ensuring hybrid orchestration works seamlessly.

## Usage Examples

```bash
/sync-with-native status          # Show sync status between systems
/sync-with-native register-all    # Register all configured agents with bridge
/sync-with-native cleanup         # Remove stale bridge registrations
/sync-with-native health-check    # Comprehensive system health verification
```

## Implementation

```bash
#!/bin/bash

# Parse arguments
ACTION="${1:-status}"

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
AGENT_CONFIG_DIR=".claude/commands/agents"

echo "🔄 Bridge-Native Synchronization"
echo "Bridge root: $BRIDGE_ROOT"
echo "Action: $ACTION"
echo

case "$ACTION" in
    "status")
        echo "=== SYNC STATUS ==="
        echo

        # Check native agent configurations
        if [ -d "$AGENT_CONFIG_DIR" ]; then
            NATIVE_COUNT=$(ls "$AGENT_CONFIG_DIR"/*.json 2>/dev/null | wc -l)
            echo "📱 Native Agents Configured: $NATIVE_COUNT"

            if [ $NATIVE_COUNT -gt 0 ]; then
                echo "   Agents:"
                for config in "$AGENT_CONFIG_DIR"/*.json; do
                    if [ -f "$config" ]; then
                        AGENT_NAME=$(basename "$config" .json)
                        AGENT_TYPE=$(grep '"agent_type"' "$config" | cut -d'"' -f4 2>/dev/null || echo "unknown")
                        echo "   - $AGENT_NAME ($AGENT_TYPE)"
                    fi
                done
            fi
        else
            echo "📱 Native Agents Configured: 0 (no .claude/commands/agents directory)"
        fi

        echo

        # Check bridge registrations
        if [ -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            echo "🌉 Bridge System Status:"
            "$BRIDGE_ROOT/scripts/bridge-register.sh" list | grep -E "(Registered Agents|Active Sessions)" -A 20
        else
            echo "🌉 Bridge System: Not accessible"
        fi

        echo

        # Check synchronization
        echo "🔄 Synchronization Status:"
        if [ -d "$AGENT_CONFIG_DIR" ] && [ -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            SYNC_ISSUES=0

            for config in "$AGENT_CONFIG_DIR"/*.json; do
                if [ -f "$config" ]; then
                    BRIDGE_NAME=$(basename "$config" .json)
                    AGENT_NAME=$(grep '"agent_name"' "$config" | cut -d'"' -f4 2>/dev/null)

                    # Check if registered in bridge
                    if "$BRIDGE_ROOT/scripts/bridge-register.sh" list | grep -q "$BRIDGE_NAME"; then
                        echo "   ✅ $AGENT_NAME ($BRIDGE_NAME) - Synchronized"
                    else
                        echo "   ❌ $AGENT_NAME ($BRIDGE_NAME) - Not registered in bridge"
                        SYNC_ISSUES=$((SYNC_ISSUES + 1))
                    fi
                fi
            done

            if [ $SYNC_ISSUES -eq 0 ]; then
                echo "   🎉 All agents synchronized!"
            else
                echo "   ⚠️  $SYNC_ISSUES agents need synchronization"
                echo "   💡 Run: /sync-with-native register-all"
            fi
        else
            echo "   ❓ Cannot verify synchronization (missing components)"
        fi
        ;;

    "register-all")
        echo "=== REGISTERING ALL AGENTS ==="
        echo

        if [ ! -d "$AGENT_CONFIG_DIR" ]; then
            echo "❌ No native agent configurations found"
            echo "💡 Use /bridge-agent-create to create agents first"
            exit 1
        fi

        if [ ! -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            echo "❌ Bridge registration script not found"
            exit 1
        fi

        REGISTERED=0
        FAILED=0

        for config in "$AGENT_CONFIG_DIR"/*.json; do
            if [ -f "$config" ]; then
                BRIDGE_NAME=$(basename "$config" .json)
                AGENT_NAME=$(grep '"agent_name"' "$config" | cut -d'"' -f4 2>/dev/null)

                echo "Registering: $AGENT_NAME ($BRIDGE_NAME)"

                if "$BRIDGE_ROOT/scripts/bridge-register.sh" register "$BRIDGE_NAME" "$(date +%s)" 2>/dev/null; then
                    echo "   ✅ Registered successfully"
                    REGISTERED=$((REGISTERED + 1))
                else
                    echo "   ❌ Registration failed"
                    FAILED=$((FAILED + 1))
                fi
            fi
        done

        echo
        echo "📊 Registration Summary:"
        echo "   ✅ Successful: $REGISTERED"
        echo "   ❌ Failed: $FAILED"

        if [ $FAILED -gt 0 ]; then
            echo "💡 Check bridge system health with: /sync-with-native health-check"
        fi
        ;;

    "cleanup")
        echo "=== CLEANUP STALE REGISTRATIONS ==="
        echo

        if [ ! -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            echo "❌ Bridge registration script not found"
            exit 1
        fi

        echo "🧹 Identifying stale registrations..."

        # Get list of currently configured agents
        CONFIGURED_AGENTS=""
        if [ -d "$AGENT_CONFIG_DIR" ]; then
            for config in "$AGENT_CONFIG_DIR"/*.json; do
                if [ -f "$config" ]; then
                    BRIDGE_NAME=$(basename "$config" .json)
                    CONFIGURED_AGENTS="$CONFIGURED_AGENTS $BRIDGE_NAME"
                fi
            done
        fi

        echo "Configured agents:$CONFIGURED_AGENTS"

        # TODO: Implement cleanup logic when bridge system supports listing registrations
        echo "⚠️  Cleanup implementation pending - requires bridge list functionality"
        echo "💡 Manual cleanup: check $BRIDGE_ROOT/bridge/registry/ for stale entries"
        ;;

    "health-check")
        echo "=== COMPREHENSIVE HEALTH CHECK ==="
        echo

        HEALTH_SCORE=0
        MAX_SCORE=0

        # Check 1: Bridge system accessible
        MAX_SCORE=$((MAX_SCORE + 1))
        echo "🔍 Bridge System Accessibility"
        if [ -d "$BRIDGE_ROOT/bridge" ] && [ -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            echo "   ✅ Bridge system found and accessible"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo "   ❌ Bridge system not accessible"
        fi

        # Check 2: Native agent configuration
        MAX_SCORE=$((MAX_SCORE + 1))
        echo "🔍 Native Agent Configuration"
        if [ -d "$AGENT_CONFIG_DIR" ] && [ $(ls "$AGENT_CONFIG_DIR"/*.json 2>/dev/null | wc -l) -gt 0 ]; then
            echo "   ✅ Native agents configured"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo "   ⚠️  No native agents configured"
        fi

        # Check 3: Bridge queue health
        MAX_SCORE=$((MAX_SCORE + 1))
        echo "🔍 Bridge Queue Health"
        if [ -d "$BRIDGE_ROOT/bridge/queue/pending" ]; then
            PENDING_COUNT=$(ls "$BRIDGE_ROOT/bridge/queue/pending" 2>/dev/null | wc -l)
            if [ $PENDING_COUNT -lt 100 ]; then
                echo "   ✅ Queue healthy ($PENDING_COUNT pending messages)"
                HEALTH_SCORE=$((HEALTH_SCORE + 1))
            else
                echo "   ⚠️  Queue congested ($PENDING_COUNT pending messages)"
            fi
        else
            echo "   ❌ Queue directory not found"
        fi

        # Check 4: Message sending capability
        MAX_SCORE=$((MAX_SCORE + 1))
        echo "🔍 Message Sending Capability"
        if [ -f "$BRIDGE_ROOT/scripts/bridge-send.sh" ]; then
            echo "   ✅ Bridge send script available"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo "   ❌ Bridge send script not found"
        fi

        # Check 5: Agent registry
        MAX_SCORE=$((MAX_SCORE + 1))
        echo "🔍 Agent Registry"
        if [ -d "$BRIDGE_ROOT/bridge/registry" ]; then
            echo "   ✅ Registry directory exists"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            echo "   ❌ Registry directory not found"
        fi

        echo
        echo "📊 Health Score: $HEALTH_SCORE/$MAX_SCORE"

        if [ $HEALTH_SCORE -eq $MAX_SCORE ]; then
            echo "🎉 System fully healthy!"
        elif [ $HEALTH_SCORE -ge $((MAX_SCORE * 3 / 4)) ]; then
            echo "✅ System mostly healthy"
        elif [ $HEALTH_SCORE -ge $((MAX_SCORE / 2)) ]; then
            echo "⚠️  System has issues"
        else
            echo "❌ System needs attention"
        fi

        echo
        echo "💡 Recommendations:"
        if [ $HEALTH_SCORE -lt $MAX_SCORE ]; then
            echo "   - Check bridge system installation"
            echo "   - Verify file permissions"
            echo "   - Consider running bridge extraction plan"
        fi
        echo "   - Use /bridge-agent-create to add specialized agents"
        echo "   - Use /session-handoff for cross-agent coordination"
        ;;

    *)
        echo "❌ Unknown action: $ACTION"
        echo "Valid actions: status, register-all, cleanup, health-check"
        exit 1
        ;;
esac

echo
echo "🔄 Sync operation complete!"
```
