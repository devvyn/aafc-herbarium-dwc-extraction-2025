#!/bin/bash
# Weekend Project Mode - Safe experimentation without blocking production

set -e

MODE=${1:-status}

case "$MODE" in
    start)
        echo "🎨 Starting Weekend Project Mode"
        echo ""

        # Check current branch
        CURRENT=$(git branch --show-current)
        echo "Current branch: $CURRENT"

        # Save work in progress
        if [[ -n $(git status -s) ]]; then
            echo "📦 Stashing current work..."
            git stash push -m "Weekend mode: saved from $CURRENT at $(date)"
        fi

        # Create/switch to experimental branch
        if git show-ref --verify --quiet refs/heads/experimental/weekend-projects; then
            echo "🔄 Switching to existing weekend branch..."
            git checkout experimental/weekend-projects
        else
            echo "🆕 Creating new weekend branch..."
            git checkout -b experimental/weekend-projects
        fi

        echo ""
        echo "✅ Weekend Mode Active!"
        echo ""
        echo "📋 Guidelines:"
        echo "  - Experiment freely - this won't block Monday work"
        echo "  - Document in .coordination/WEEKEND_PROJECTS.md"
        echo "  - Cherry-pick useful commits back to main branches"
        echo ""
        echo "🔙 Return to weekday work: ./scripts/weekend-mode.sh end"
        ;;

    end)
        echo "🎯 Ending Weekend Project Mode"
        echo ""

        # Check what's changed
        if [[ -n $(git status -s) ]]; then
            echo "📝 You have uncommitted changes:"
            git status -s
            echo ""
            read -p "Commit weekend work? (y/n): " COMMIT

            if [[ "$COMMIT" == "y" ]]; then
                read -p "Commit message: " MSG
                git add -A
                git commit -m "weekend: $MSG"
                echo "✅ Weekend work committed"
            else
                echo "⚠️  Changes left uncommitted (you can commit later)"
            fi
        fi

        # Switch back to feature branch
        echo "🔄 Switching back to feature/v2-accessibility-first..."
        git checkout feature/v2-accessibility-first

        # Restore stashed work if any
        if git stash list | grep -q "Weekend mode"; then
            echo "📦 Restoring weekday work..."
            git stash pop
        fi

        echo ""
        echo "✅ Back to Weekday Mode!"
        echo ""
        echo "📋 Monday morning checklist:"
        echo "  1. Review .coordination/INTER_AGENT_MEMO.md"
        echo "  2. Check any weekend insights worth porting"
        echo "  3. Continue with v2 accessibility work"
        ;;

    status)
        echo "🔍 Project Mode Status"
        echo ""

        CURRENT=$(git branch --show-current)
        echo "Current branch: $CURRENT"

        if [[ "$CURRENT" == "experimental/weekend-projects" ]]; then
            echo "Mode: 🎨 WEEKEND (experimental)"
            echo ""
            echo "Active weekend projects:"
            if [[ -f .coordination/WEEKEND_PROJECTS.md ]]; then
                grep "^### " .coordination/WEEKEND_PROJECTS.md | head -5
            fi
        else
            echo "Mode: 🎯 WEEKDAY (production)"
            echo ""
            echo "Current focus: Accessibility-first review system"
            echo "Phase 2 Status: ✅ Complete (2A, 2B, 2C)"
        fi

        echo ""
        echo "Available commands:"
        echo "  ./scripts/weekend-mode.sh start  - Switch to weekend mode"
        echo "  ./scripts/weekend-mode.sh end    - Return to weekday mode"
        echo "  ./scripts/weekend-mode.sh status - Show current mode"
        ;;

    *)
        echo "Usage: $0 {start|end|status}"
        exit 1
        ;;
esac
