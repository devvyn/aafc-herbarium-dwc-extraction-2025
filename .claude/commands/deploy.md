---
description: Deploy project components with discovery and dependency resolution
---

# Deployment Registry System

The user can provide a component name and options after `/deploy`. The input is available in `$ARGUMENTS`.

User input: $ARGUMENTS

## Quick Usage

```bash
/deploy                         # Show all deployable components
/deploy list                    # Show all deployable components
/deploy hybrid-orchestration    # Deploy bridge + native agent integration
/deploy specialized-agents      # Deploy Darwin Core, OCR, Pattern agents
/deploy bridge-extraction-plan  # Execute bridge system migration
```

## Implementation

Parse the arguments and execute the deployment:

```bash
#!/bin/bash

# Parse arguments from user input
ARGS="$ARGUMENTS"
COMPONENT="${ARGS%% *}"  # First word is component
OPTIONS="${ARGS#* }"     # Rest are options

# Default to list if no component specified
if [ -z "$COMPONENT" ] || [ "$COMPONENT" = "$OPTIONS" ]; then
    COMPONENT="list"
    OPTIONS=""
fi

echo "🚀 Deployment Registry System"
echo "Component: $COMPONENT"

case "$COMPONENT" in
    "list")
        echo
        echo "=== DEPLOYABLE COMPONENTS ==="
        echo
        echo "🔧 Infrastructure:"
        echo "   bridge-extraction-plan    Execute bridge system migration"
        echo "   hybrid-orchestration      Bridge + native /agents integration"
        echo "   bridge-backup-system      Safety backup procedures"
        echo
        echo "🤖 Agent Systems:"
        echo "   specialized-agents        Darwin Core, OCR, Pattern, Review agents"
        echo "   agent-discovery-system    Registry and discovery mechanisms"
        echo
        echo "📋 Specifications:"
        echo "   spec-driven-development   Complete .specify/ system"
        echo "   ocr-extraction-pipeline   OCR pipeline implementation"
        echo
        echo "🔬 Research Pipeline:"
        echo "   darwin-core-validation    Taxonomic accuracy system"
        echo "   pattern-analysis-toolkit  Historical pattern application"
        echo
        echo "⚙️ Development:"
        echo "   multi-agent-framework     v2.1 collaboration framework"
        echo "   quality-assurance         Testing and validation automation"
        echo
        echo "Usage: /deploy [component-name] [--dry-run|--backup]"
        ;;

    "hybrid-orchestration")
        echo
        echo "=== DEPLOYING: Hybrid Orchestration ==="
        echo
        if [ -f ".claude/commands/bridge-agent-create.md" ]; then
            echo "✅ Already deployed!"
            echo "   Available commands:"
            echo "   - /bridge-agent-create"
            echo "   - /session-handoff"
            echo "   - /sync-with-native"
            echo "   - /bridge-extraction-prep"
            echo "   - /extraction-verify"
        else
            echo "❌ Deployment files missing"
            echo "💡 Commands should be in .claude/commands/"
        fi
        ;;

    "specialized-agents")
        echo
        echo "=== DEPLOYING: Specialized Agents ==="
        echo
        echo "Creating specialized agent types:"
        echo "   🔬 Darwin Core Validator"
        echo "   🔍 OCR Benchmark Agent"
        echo "   📊 Pattern Analysis Expert"
        echo "   ✅ Scientific Reviewer"
        echo
        echo "💡 Use: /bridge-agent-create [type] [name] to create agents"
        echo "💡 Example: /bridge-agent-create darwin-core \"DwC Validator\""
        ;;

    "bridge-extraction-plan")
        echo
        echo "=== DEPLOYING: Bridge Extraction Plan ==="
        echo
        echo "🚨 This will migrate bridge system to ~/infrastructure/agent-bridge/"
        echo
        if [[ "$OPTIONS" == *"--dry-run"* ]]; then
            echo "🔍 DRY RUN - would execute:"
            echo "   1. Validate current bridge system"
            echo "   2. Create safety backup"
            echo "   3. Execute extraction phases 1-7"
            echo "   4. Verify operation at new location"
        else
            echo "⚠️  CRITICAL OPERATION"
            echo "💡 Recommend: /bridge-extraction-prep ready-check first"
            echo "💡 Use --dry-run to preview steps"
        fi
        ;;

    *)
        echo
        echo "❌ Unknown component: $COMPONENT"
        echo "💡 Use '/deploy list' to see available components"
        exit 1
        ;;
esac

echo
echo "🎯 Deployment registry ready!"
```
