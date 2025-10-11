#!/usr/bin/env bash
###############################################################################
# Tmux Integration for Extraction Monitoring
#
# Automatically splits tmux pane and launches TUI monitor
#
# Usage:
#   ./scripts/tmux-monitor.sh <run-directory>
#
# Example:
#   ./scripts/tmux-monitor.sh full_dataset_processing/openrouter_run_20251010_115131
###############################################################################

set -euo pipefail

RUN_DIR="${1:-}"

if [[ -z "$RUN_DIR" ]]; then
    echo "❌ Usage: $0 <run-directory>"
    echo ""
    echo "Example:"
    echo "  $0 full_dataset_processing/openrouter_run_20251010_115131"
    exit 1
fi

if [[ ! -d "$RUN_DIR" ]]; then
    echo "❌ Directory not found: $RUN_DIR"
    exit 1
fi

# Check if we're in tmux
if [[ -z "${TMUX:-}" ]]; then
    echo "⚠️  Not in tmux session. Starting new session..."
    tmux new-session -d -s herbarium-monitor
    tmux split-window -h "cd $(pwd) && uv run python scripts/monitor_tui.py --run-dir $RUN_DIR"
    tmux select-pane -t 0
    tmux attach-session -t herbarium-monitor
else
    echo "🚀 Launching monitor in split pane..."

    # Split window horizontally (side-by-side)
    tmux split-window -h "cd $(pwd) && uv run python scripts/monitor_tui.py --run-dir $RUN_DIR"

    # Focus back on original pane
    tmux select-pane -t 0

    echo "✅ Monitor launched in right pane"
    echo "   Switch with: Ctrl-b →"
    echo "   Close with: Ctrl-b x"
fi
