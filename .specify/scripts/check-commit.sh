#!/bin/bash
# Commit Message Validation Script
# Checks if commits follow specification checkpoint requirements

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"commit message\""
    exit 1
fi

COMMIT_MSG="$1"

echo -e "${BLUE}🔍 Checking commit message for specification compliance...${NC}"

# Check for specification references
has_spec_ref=false
has_purpose=false
has_rationale=false
has_ref=false

if echo "$COMMIT_MSG" | grep -qi "ref:" || echo "$COMMIT_MSG" | grep -qi "spec:"; then
    has_ref=true
fi

if echo "$COMMIT_MSG" | grep -qi "purpose:"; then
    has_purpose=true
fi

if echo "$COMMIT_MSG" | grep -qi "rationale:"; then
    has_rationale=true
fi

# Determine commit type
if echo "$COMMIT_MSG" | grep -qE "^(feat|feature)"; then
    commit_type="feature"
elif echo "$COMMIT_MSG" | grep -qE "^(fix|bugfix)"; then
    commit_type="fix"
elif echo "$COMMIT_MSG" | grep -qE "^(refactor|perf|style)"; then
    commit_type="enhancement"
else
    commit_type="other"
fi

echo -e "${BLUE}Commit type detected: $commit_type${NC}"

# Validation logic
valid=true
suggestions=()

case $commit_type in
    "feature")
        if ! $has_ref && ! $has_purpose; then
            valid=false
            suggestions+=("Feature commits should include either:")
            suggestions+=("  - 'Ref: .specify/features/xxx/spec.md' for full specifications")
            suggestions+=("  - 'Purpose: [description]' for lightweight documentation")
        fi
        ;;
    "enhancement"|"fix")
        if ! $has_ref && ! $has_purpose && ! $has_rationale; then
            valid=false
            suggestions+=("Enhancement/fix commits should include either:")
            suggestions+=("  - 'Ref: [specification]' for documented changes")
            suggestions+=("  - 'Purpose: [description]' for moderate changes")
            suggestions+=("  - 'Rationale: [description]' for simple fixes")
        fi
        ;;
esac

# Report results
if $valid; then
    echo -e "${GREEN}✅ Commit message follows specification guidelines${NC}"
    exit 0
else
    echo -e "${RED}❌ Commit message needs specification reference${NC}"
    echo ""
    echo -e "${YELLOW}Suggestions:${NC}"
    for suggestion in "${suggestions[@]}"; do
        echo -e "  $suggestion"
    done
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "  feat: implement user authentication"
    echo -e "  "
    echo -e "  Ref: .specify/features/001-user-auth/spec.md"
    echo -e "  ADR: .specify/decisions/adr-001-auth-strategy.md"
    echo ""
    echo -e "  fix: optimize database query performance"
    echo -e "  "
    echo -e "  Purpose: Reduce query time from 2s to 500ms"
    echo -e "  Approach: Added compound index on (user_id, created_at)"
    echo -e "  Testing: Added performance test with 10k records"
    exit 1
fi
