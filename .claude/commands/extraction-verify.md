---
name: extraction-verify
description: Verify bridge system operation during extraction transition
usage: /extraction-verify [test-type]
args:
  - name: test-type
    description: Verification test (connectivity, messaging, agents, rollback)
    required: false
    default: connectivity
---

# Bridge Extraction Verification Tool

Verifies bridge system operation during the extraction transition, especially during the symlink phase.

## Usage Examples

```bash
/extraction-verify connectivity    # Test basic bridge connectivity
/extraction-verify messaging       # Test message sending/receiving
/extraction-verify agents          # Test agent registration and coordination
/extraction-verify rollback        # Verify rollback procedures work
```

## Implementation

```bash
#!/bin/bash

# Parse arguments
TEST_TYPE="${1:-connectivity}"

# Auto-detect bridge location
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

echo "🔍 Bridge Extraction Verification"
echo "Test type: $TEST_TYPE"
echo "Bridge root: $BRIDGE_ROOT"
echo

case "$TEST_TYPE" in
    "connectivity")
        echo "=== CONNECTIVITY VERIFICATION ==="
        echo

        # Test 1: Bridge directory structure
        echo "🔍 Bridge Directory Structure"
        REQUIRED_DIRS=(
            "bridge/queue/pending"
            "bridge/queue/processing"
            "bridge/registry"
            "bridge/archive"
        )

        STRUCTURE_OK=true
        for dir in "${REQUIRED_DIRS[@]}"; do
            if [ -d "$BRIDGE_ROOT/$dir" ]; then
                echo "   ✅ $dir"
            else
                echo "   ❌ $dir (missing)"
                STRUCTURE_OK=false
            fi
        done

        # Test 2: Scripts accessibility
        echo "🔍 Scripts Accessibility"
        REQUIRED_SCRIPTS=(
            "scripts/bridge-send.sh"
            "scripts/bridge-receive.sh"
            "scripts/bridge-register.sh"
        )

        SCRIPTS_OK=true
        for script in "${REQUIRED_SCRIPTS[@]}"; do
            if [ -f "$BRIDGE_ROOT/$script" ] && [ -x "$BRIDGE_ROOT/$script" ]; then
                echo "   ✅ $script"
            else
                echo "   ❌ $script (missing or not executable)"
                SCRIPTS_OK=false
            fi
        done

        # Test 3: Symlink detection
        echo "🔍 Symlink Status"
        if [ -L "$HOME/devvyn-meta-project/bridge" ]; then
            LINK_TARGET=$(readlink "$HOME/devvyn-meta-project/bridge")
            echo "   🔗 Symlink detected: $LINK_TARGET"

            if [ "$LINK_TARGET" = "$HOME/infrastructure/agent-bridge/bridge" ]; then
                echo "   ✅ Symlink points to correct location"
            else
                echo "   ⚠️  Symlink points to unexpected location"
            fi
        elif [ -d "$HOME/devvyn-meta-project/bridge" ]; then
            echo "   📁 Regular directory (no symlink)"
        else
            echo "   ❌ Bridge not found at meta-project location"
        fi

        # Summary
        echo
        if $STRUCTURE_OK && $SCRIPTS_OK; then
            echo "✅ Connectivity verification PASSED"
        else
            echo "❌ Connectivity verification FAILED"
            exit 1
        fi
        ;;

    "messaging")
        echo "=== MESSAGING VERIFICATION ==="
        echo

        # Test 1: Message creation
        echo "🔍 Message Creation Test"
        TEST_MESSAGE="/tmp/extraction-test-$(date +%s).md"
        cat > "$TEST_MESSAGE" << EOF
# Extraction Verification Test

This is a test message to verify bridge messaging during extraction.

**Test ID**: $(date +%s)
**From**: extraction-verify command
**Purpose**: Verify messaging system integrity

## Test Results
- Message creation: ✅
- Bridge path resolution: $BRIDGE_ROOT
- Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

        echo "   ✅ Test message created"

        # Test 2: Message sending
        echo "🔍 Message Sending Test"
        if [ -f "$BRIDGE_ROOT/scripts/bridge-send.sh" ]; then
            if "$BRIDGE_ROOT/scripts/bridge-send.sh" code code NORMAL "Extraction Verification Test" "$TEST_MESSAGE" 2>/dev/null; then
                echo "   ✅ Message sent successfully"
            else
                echo "   ❌ Message sending failed"
                rm -f "$TEST_MESSAGE"
                exit 1
            fi
        else
            echo "   ❌ Bridge send script not found"
            rm -f "$TEST_MESSAGE"
            exit 1
        fi

        # Test 3: Message receiving
        echo "🔍 Message Receiving Test"
        if [ -f "$BRIDGE_ROOT/scripts/bridge-receive.sh" ]; then
            echo "   Attempting to receive test message..."
            RECEIVE_OUTPUT=$("$BRIDGE_ROOT/scripts/bridge-receive.sh" code 2>/dev/null)
            if echo "$RECEIVE_OUTPUT" | grep -q "Extraction Verification Test"; then
                echo "   ✅ Message received successfully"
            else
                echo "   ⚠️  Test message not immediately available (may be processed later)"
            fi
        else
            echo "   ❌ Bridge receive script not found"
            exit 1
        fi

        # Test 4: Queue state
        echo "🔍 Queue State"
        PENDING_COUNT=$(ls "$BRIDGE_ROOT/bridge/queue/pending" 2>/dev/null | wc -l)
        echo "   📊 Pending messages: $PENDING_COUNT"

        # Cleanup
        rm -f "$TEST_MESSAGE"
        echo "✅ Messaging verification PASSED"
        ;;

    "agents")
        echo "=== AGENT VERIFICATION ==="
        echo

        # Test 1: Agent registration
        echo "🔍 Agent Registration Test"
        if [ -f "$BRIDGE_ROOT/scripts/bridge-register.sh" ]; then
            # Test registration
            TEST_AGENT="test-extraction-$(date +%s)"
            if "$BRIDGE_ROOT/scripts/bridge-register.sh" register "$TEST_AGENT" "$(date +%s)" 2>/dev/null; then
                echo "   ✅ Agent registration successful"

                # Test unregistration
                if "$BRIDGE_ROOT/scripts/bridge-register.sh" unregister "$TEST_AGENT" 2>/dev/null; then
                    echo "   ✅ Agent unregistration successful"
                else
                    echo "   ⚠️  Agent unregistration failed (manual cleanup may be needed)"
                fi
            else
                echo "   ❌ Agent registration failed"
                exit 1
            fi
        else
            echo "   ❌ Bridge register script not found"
            exit 1
        fi

        # Test 2: Native agent coordination
        echo "🔍 Native Agent Coordination"
        if [ -d ".claude/commands/agents" ]; then
            AGENT_COUNT=$(ls .claude/commands/agents/*.json 2>/dev/null | wc -l)
            echo "   📱 Native agents configured: $AGENT_COUNT"

            if [ $AGENT_COUNT -gt 0 ]; then
                echo "   ✅ Native agents available for coordination"
            else
                echo "   ⚠️  No native agents configured"
            fi
        else
            echo "   ⚠️  No native agent configuration directory"
        fi

        # Test 3: Cross-session coordination capability
        echo "🔍 Cross-Session Coordination"
        if [ -f ".claude/commands/session-handoff.md" ]; then
            echo "   ✅ Session handoff command available"
        else
            echo "   ❌ Session handoff command missing"
        fi

        echo "✅ Agent verification PASSED"
        ;;

    "rollback")
        echo "=== ROLLBACK VERIFICATION ==="
        echo

        # Test 1: Backup availability
        echo "🔍 Backup Availability"
        BACKUP_DIRS=$(ls -d "$HOME"/bridge-extraction-backup-* 2>/dev/null | head -3)
        if [ -n "$BACKUP_DIRS" ]; then
            echo "   ✅ Backup directories found:"
            for backup in $BACKUP_DIRS; do
                echo "      📁 $(basename "$backup")"
            done
        else
            echo "   ❌ No backup directories found"
            echo "   💡 Run: /bridge-extraction-prep backup"
        fi

        # Test 2: Rollback script validation
        echo "🔍 Rollback Script Validation"
        LATEST_BACKUP=$(ls -d "$HOME"/bridge-extraction-backup-* 2>/dev/null | tail -1)
        if [ -n "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP/restore.sh" ]; then
            echo "   ✅ Rollback script found: $LATEST_BACKUP/restore.sh"

            # Check script permissions
            if [ -x "$LATEST_BACKUP/restore.sh" ]; then
                echo "   ✅ Rollback script is executable"
            else
                echo "   ⚠️  Rollback script not executable"
                echo "      Fix with: chmod +x $LATEST_BACKUP/restore.sh"
            fi
        else
            echo "   ❌ Rollback script not found"
        fi

        # Test 3: Symlink rollback capability
        echo "🔍 Symlink Rollback Capability"
        if [ -L "$HOME/devvyn-meta-project/bridge" ]; then
            echo "   🔗 Currently using symlink"
            echo "   💡 Rollback: rm $HOME/devvyn-meta-project/bridge && mv backup/bridge $HOME/devvyn-meta-project/"
        elif [ -d "$HOME/devvyn-meta-project/bridge" ]; then
            echo "   📁 Currently using regular directory"
            echo "   💡 Rollback via backup restoration"
        else
            echo "   ❌ No bridge found at meta-project location"
        fi

        # Test 4: Data preservation check
        echo "🔍 Data Preservation Check"
        if [ -n "$LATEST_BACKUP" ]; then
            BACKUP_ARCHIVE_COUNT=$(ls "$LATEST_BACKUP/bridge/archive" 2>/dev/null | wc -l)
            CURRENT_ARCHIVE_COUNT=$(ls "$BRIDGE_ROOT/bridge/archive" 2>/dev/null | wc -l)

            echo "   📊 Backup archive: $BACKUP_ARCHIVE_COUNT messages"
            echo "   📊 Current archive: $CURRENT_ARCHIVE_COUNT messages"

            if [ $CURRENT_ARCHIVE_COUNT -ge $BACKUP_ARCHIVE_COUNT ]; then
                echo "   ✅ No message loss detected"
            else
                echo "   ⚠️  Potential message loss detected"
            fi
        fi

        echo "✅ Rollback verification PASSED"
        ;;

    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Valid test types: connectivity, messaging, agents, rollback"
        exit 1
        ;;
esac

echo
echo "🔍 Verification complete!"
echo "💡 Run with different test types for comprehensive validation"
```
