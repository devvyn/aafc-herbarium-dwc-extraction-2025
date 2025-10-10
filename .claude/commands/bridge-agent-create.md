---
name: bridge-agent-create
description: Create native Claude Code subagent with bridge system integration
usage: /bridge-agent-create [type] [name] [description]
args:
  - name: type
    description: Agent specialization (darwin-core, ocr-benchmark, pattern-analysis, scientific-review)
    required: true
  - name: name
    description: Agent name (will be normalized for bridge compatibility)
    required: true
  - name: description
    description: Agent description and purpose
    required: false
---

# Bridge-Integrated Agent Creator

Creates a specialized Claude Code subagent and automatically registers it with the bridge system.

## Usage Examples

```bash
/bridge-agent-create darwin-core "DwC Validator" "Validates taxonomic accuracy"
/bridge-agent-create ocr-benchmark "OCR Tester" "Evaluates OCR engines"
/bridge-agent-create pattern-analysis "Pattern Expert" "Applies historical patterns"
/bridge-agent-create scientific-review "Science Reviewer" "Reviews for accuracy"
```

## Agent Types

- **darwin-core**: Taxonomic validation and Darwin Core compliance
- **ocr-benchmark**: OCR engine evaluation and performance testing
- **pattern-analysis**: Historical pattern application from INTER_AGENT_MEMO
- **scientific-review**: Scientific accuracy and domain expertise validation

## Implementation

```bash
#!/bin/bash

AGENT_TYPE="$1"
AGENT_NAME="$2"
AGENT_DESC="${3:-Specialized agent for $AGENT_TYPE tasks}"

if [ -z "$AGENT_TYPE" ] || [ -z "$AGENT_NAME" ]; then
    echo "Usage: /bridge-agent-create [type] [name] [description]"
    exit 1
fi

# Auto-detect bridge location (extraction-ready)
if [ -d "$HOME/infrastructure/agent-bridge/bridge" ]; then
    BRIDGE_ROOT="$HOME/infrastructure/agent-bridge"
elif [ -d "$HOME/devvyn-meta-project/bridge" ]; then
    BRIDGE_ROOT="$HOME/devvyn-meta-project"
else
    echo "ERROR: Bridge system not found"
    exit 1
fi

echo "🤖 Creating bridge-integrated agent: $AGENT_NAME ($AGENT_TYPE)"
echo "Bridge root: $BRIDGE_ROOT"

# Configure by agent type
case "$AGENT_TYPE" in
    "darwin-core")
        TOOLS="Read,Write,Edit,Grep,WebFetch,Bash"
        PROMPT="Darwin Core validation specialist. Focus on taxonomic accuracy."
        ;;
    "ocr-benchmark")
        TOOLS="Bash,Read,Write,Task,Glob"
        PROMPT="OCR engine evaluation specialist. Focus on systematic testing."
        ;;
    "pattern-analysis")
        TOOLS="Read,Grep,Glob,Task,Edit"
        PROMPT="Pattern application specialist. Focus on INTER_AGENT_MEMO patterns."
        ;;
    "scientific-review")
        TOOLS="Read,Grep,WebFetch"
        PROMPT="Scientific accuracy reviewer. Focus on domain expertise."
        ;;
    *)
        echo "Unknown agent type: $AGENT_TYPE"
        exit 1
        ;;
esac

echo "Tools: $TOOLS"
echo
echo "Next steps:"
echo "1. Use /agents command to create: $AGENT_NAME"
echo "2. Configure with tools: $TOOLS"
echo "3. Set prompt: $PROMPT"
echo "4. Agent will be registered with bridge system"

echo "✅ Agent specification ready!"
```
