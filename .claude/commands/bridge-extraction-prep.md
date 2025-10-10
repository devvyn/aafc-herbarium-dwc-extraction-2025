---
name: bridge-extraction-prep
description: Prepare for Agent Bridge Extraction Plan execution
usage: /bridge-extraction-prep [phase]
args:
  - name: phase
    description: Preparation phase (validate, backup, test-paths, ready-check)
    required: false
    default: ready-check
---

# Bridge Extraction Preparation Tool

Prepares the system for Agent Bridge Extraction Plan execution with comprehensive validation and backup procedures.

## Usage Examples

```bash
/bridge-extraction-prep validate      # Validate current bridge system state
/bridge-extraction-prep backup        # Create safety backup before extraction
/bridge-extraction-prep test-paths    # Test path resolution for both locations
/bridge-extraction-prep ready-check   # Comprehensive readiness assessment
```

## Implementation

```bash
#!/bin/bash

# Parse arguments
PHASE="${1:-ready-check}"

# Bridge paths
OLD_BRIDGE="$HOME/devvyn-meta-project/bridge"
NEW_BRIDGE="$HOME/infrastructure/agent-bridge/bridge"
META_PROJECT="$HOME/devvyn-meta-project"

echo "🚀 Bridge Extraction Preparation"
echo "Phase: $PHASE"
echo

case "$PHASE" in
    "validate")
        echo "=== VALIDATING CURRENT BRIDGE STATE ==="
        echo

        # Check current bridge system
        if [ -d "$OLD_BRIDGE" ]; then
            echo "✅ Current bridge system found at: $OLD_BRIDGE"

            # Check critical components
            COMPONENTS=(
                "queue/pending"
                "queue/processing"
                "registry"
                "archive"
            )

            for component in "${COMPONENTS[@]}"; do
                if [ -d "$OLD_BRIDGE/$component" ]; then
                    echo "   ✅ $component"
                else
                    echo "   ❌ $component (missing)"
                fi
            done

            # Check message count
            PENDING_COUNT=$(ls "$OLD_BRIDGE/queue/pending" 2>/dev/null | wc -l)
            ARCHIVE_COUNT=$(ls "$OLD_BRIDGE/archive" 2>/dev/null | wc -l)
            echo "   📊 Messages: $PENDING_COUNT pending, $ARCHIVE_COUNT archived"

        else
            echo "❌ Current bridge system not found"
            exit 1
        fi

        echo

        # Check TLA+ specifications
        echo "🔍 TLA+ Specifications:"
        TLA_FILES=(
            "ClaudeCodeSystem.tla"
            "claude_code_system.cfg"
            "tla2tools.jar"
        )

        for tla_file in "${TLA_FILES[@]}"; do
            if [ -f "$META_PROJECT/$tla_file" ]; then
                echo "   ✅ $tla_file"
            else
                echo "   ❌ $tla_file (missing)"
            fi
        done

        echo

        # Check agent configurations
        echo "🤖 Agent Configurations:"
        if [ -d ".claude/commands/agents" ]; then
            AGENT_COUNT=$(ls .claude/commands/agents/*.json 2>/dev/null | wc -l)
            echo "   ✅ $AGENT_COUNT native agents configured"
        else
            echo "   ⚠️  No native agents configured"
        fi

        echo "✅ Validation complete"
        ;;

    "backup")
        echo "=== CREATING SAFETY BACKUP ==="
        echo

        BACKUP_DIR="$HOME/bridge-extraction-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        echo "📦 Backup location: $BACKUP_DIR"

        # Backup bridge system
        if [ -d "$OLD_BRIDGE" ]; then
            echo "Backing up bridge system..."
            cp -r "$OLD_BRIDGE" "$BACKUP_DIR/bridge"
            echo "   ✅ Bridge system backed up"
        fi

        # Backup TLA+ specs
        echo "Backing up TLA+ specifications..."
        mkdir -p "$BACKUP_DIR/specs"
        for spec in ClaudeCodeSystem.tla claude_code_system.cfg tla2tools.jar TLA_VERIFICATION_*.md; do
            if [ -f "$META_PROJECT/$spec" ]; then
                cp "$META_PROJECT/$spec" "$BACKUP_DIR/specs/"
            fi
        done
        echo "   ✅ TLA+ specs backed up"

        # Backup agent configurations
        if [ -d ".claude/commands/agents" ]; then
            echo "Backing up agent configurations..."
            cp -r ".claude/commands/agents" "$BACKUP_DIR/agent-configs"
            echo "   ✅ Agent configs backed up"
        fi

        # Create restoration script
        cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
echo "🔄 Restoring bridge system from backup..."

BACKUP_DIR="$(dirname "$0")"
OLD_BRIDGE="$HOME/devvyn-meta-project/bridge"
META_PROJECT="$HOME/devvyn-meta-project"

# Remove current bridge
if [ -d "$OLD_BRIDGE" ]; then
    mv "$OLD_BRIDGE" "$OLD_BRIDGE.replaced-$(date +%s)"
fi

# Restore bridge
cp -r "$BACKUP_DIR/bridge" "$OLD_BRIDGE"
echo "✅ Bridge system restored"

# Restore TLA+ specs
for spec in "$BACKUP_DIR/specs"/*; do
    if [ -f "$spec" ]; then
        cp "$spec" "$META_PROJECT/"
    fi
done
echo "✅ TLA+ specs restored"

echo "🎉 Restoration complete!"
echo "Test bridge connectivity before continuing work."
EOF

        chmod +x "$BACKUP_DIR/restore.sh"

        echo "✅ Backup complete"
        echo "   📁 Location: $BACKUP_DIR"
        echo "   🔄 Restore script: $BACKUP_DIR/restore.sh"
        ;;

    "test-paths")
        echo "=== TESTING PATH RESOLUTION ==="
        echo

        # Test current path resolution
        echo "🔍 Current Path Resolution:"
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

        CURRENT_BRIDGE=$(resolve_bridge_path)
        if [ $? -eq 0 ]; then
            echo "   ✅ Resolves to: $CURRENT_BRIDGE"
        else
            echo "   ❌ Path resolution failed"
        fi

        echo

        # Test future path (simulate extraction)
        echo "🔮 Future Path Resolution (simulated):"
        if [ ! -d "$HOME/infrastructure" ]; then
            echo "   📁 Creating infrastructure directory for test..."
            mkdir -p "$HOME/infrastructure/agent-bridge"
            echo "   ✅ Infrastructure directory created"
        fi

        if [ ! -d "$NEW_BRIDGE" ]; then
            echo "   📁 Creating test bridge structure..."
            mkdir -p "$NEW_BRIDGE"
            touch "$NEW_BRIDGE/.test-marker"
            echo "   ✅ Test bridge structure created"
        fi

        # Test resolution with both paths
        FUTURE_BRIDGE=$(resolve_bridge_path)
        echo "   🔮 Would resolve to: $FUTURE_BRIDGE"

        # Clean up test structure
        if [ -f "$NEW_BRIDGE/.test-marker" ]; then
            rm -rf "$HOME/infrastructure/agent-bridge"
            echo "   🧹 Test structure cleaned up"
        fi

        echo "✅ Path resolution testing complete"
        ;;

    "ready-check")
        echo "=== COMPREHENSIVE READINESS ASSESSMENT ==="
        echo

        READY_SCORE=0
        MAX_READY_SCORE=0

        # Check 1: Bridge system validation
        MAX_READY_SCORE=$((MAX_READY_SCORE + 2))
        echo "🔍 Bridge System Health"
        if [ -d "$OLD_BRIDGE" ] && [ -d "$OLD_BRIDGE/queue" ] && [ -d "$OLD_BRIDGE/registry" ]; then
            echo "   ✅ Bridge system structure valid"
            READY_SCORE=$((READY_SCORE + 1))

            # Check for pending messages
            PENDING_COUNT=$(ls "$OLD_BRIDGE/queue/pending" 2>/dev/null | wc -l)
            if [ $PENDING_COUNT -lt 10 ]; then
                echo "   ✅ Queue state good ($PENDING_COUNT pending)"
                READY_SCORE=$((READY_SCORE + 1))
            else
                echo "   ⚠️  High queue volume ($PENDING_COUNT pending)"
            fi
        else
            echo "   ❌ Bridge system structure invalid"
        fi

        # Check 2: TLA+ specifications
        MAX_READY_SCORE=$((MAX_READY_SCORE + 1))
        echo "🔍 TLA+ Specifications"
        TLA_COUNT=0
        for spec in ClaudeCodeSystem.tla claude_code_system.cfg tla2tools.jar; do
            if [ -f "$META_PROJECT/$spec" ]; then
                TLA_COUNT=$((TLA_COUNT + 1))
            fi
        done

        if [ $TLA_COUNT -eq 3 ]; then
            echo "   ✅ All TLA+ specs present"
            READY_SCORE=$((READY_SCORE + 1))
        else
            echo "   ⚠️  Missing TLA+ specs ($TLA_COUNT/3)"
        fi

        # Check 3: Agent coordination state
        MAX_READY_SCORE=$((MAX_READY_SCORE + 1))
        echo "🔍 Agent Coordination"
        if [ -f "$META_PROJECT/scripts/bridge-register.sh" ]; then
            ACTIVE_AGENTS=$("$META_PROJECT/scripts/bridge-register.sh" list 2>/dev/null | grep -c "active" || echo "0")
            if [ $ACTIVE_AGENTS -gt 0 ]; then
                echo "   ✅ $ACTIVE_AGENTS agents registered"
                READY_SCORE=$((READY_SCORE + 1))
            else
                echo "   ⚠️  No active agents"
            fi
        else
            echo "   ❌ Bridge scripts not found"
        fi

        # Check 4: Infrastructure readiness
        MAX_READY_SCORE=$((MAX_READY_SCORE + 1))
        echo "🔍 Infrastructure Readiness"
        if [ ! -d "$HOME/infrastructure" ]; then
            echo "   📁 Infrastructure directory will be created"
            READY_SCORE=$((READY_SCORE + 1))
        else
            echo "   ✅ Infrastructure directory exists"
            READY_SCORE=$((READY_SCORE + 1))
        fi

        # Check 5: Project integration
        MAX_READY_SCORE=$((MAX_READY_SCORE + 1))
        echo "🔍 Project Integration"
        if [ -f ".claude/commands/bridge-agent-create.md" ] && [ -f ".claude/commands/session-handoff.md" ]; then
            echo "   ✅ Hybrid orchestration commands ready"
            READY_SCORE=$((READY_SCORE + 1))
        else
            echo "   ⚠️  Hybrid orchestration commands incomplete"
        fi

        echo
        echo "📊 Readiness Score: $READY_SCORE/$MAX_READY_SCORE"

        if [ $READY_SCORE -eq $MAX_READY_SCORE ]; then
            echo "🎉 READY FOR EXTRACTION!"
            echo
            echo "Next steps:"
            echo "1. Run: /bridge-extraction-prep backup"
            echo "2. Execute Bridge Extraction Plan Phase 1-3"
            echo "3. Test with: /sync-with-native health-check"
        elif [ $READY_SCORE -ge $((MAX_READY_SCORE * 3 / 4)) ]; then
            echo "✅ MOSTLY READY - minor issues to resolve"
        else
            echo "❌ NOT READY - significant preparation needed"
        fi

        echo
        echo "💡 Recommendations:"
        echo "   - Clear bridge queue: process pending messages"
        echo "   - Ensure TLA+ specs are complete"
        echo "   - Test agent registrations"
        echo "   - Create safety backup before extraction"
        ;;

    *)
        echo "❌ Unknown phase: $PHASE"
        echo "Valid phases: validate, backup, test-paths, ready-check"
        exit 1
        ;;
esac

echo
echo "🚀 Extraction preparation complete!"
```
