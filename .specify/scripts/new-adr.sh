#!/bin/bash
# New Architecture Decision Record Script
# Creates a new ADR with proper numbering

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${RED}Usage: $0 \"decision-title-in-kebab-case\"${NC}"
    echo -e "Example: $0 \"database-selection-strategy\""
    exit 1
fi

DECISION_TITLE="$1"
DECISIONS_DIR=".specify/decisions"
TEMPLATE_FILE=".specify/templates/architecture-decision-record.md"

# Find next ADR number
LAST_NUM=$(find "$DECISIONS_DIR" -name "adr-*.md" | grep -o "adr-[0-9]\+" | sed 's/adr-//' | sort -n | tail -1)
if [ -z "$LAST_NUM" ]; then
    NEXT_NUM="001"
else
    NEXT_NUM=$(printf "%03d" $((LAST_NUM + 1)))
fi

ADR_FILE="$DECISIONS_DIR/adr-$NEXT_NUM-$DECISION_TITLE.md"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_FILE${NC}"
    exit 1
fi

if [ -f "$ADR_FILE" ]; then
    echo -e "${RED}Error: ADR file already exists at $ADR_FILE${NC}"
    exit 1
fi

# Copy template and update with ADR number and title
cp "$TEMPLATE_FILE" "$ADR_FILE"

# Replace placeholders in the new ADR
sed -i.bak "s/ADR-\[NUMBER\]/ADR-$NEXT_NUM/g" "$ADR_FILE"
sed -i.bak "s/\[Decision Title\]/$(echo "$DECISION_TITLE" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')/g" "$ADR_FILE"
sed -i.bak "s/\[YYYY-MM-DD\]/$(date +%Y-%m-%d)/g" "$ADR_FILE"
rm "$ADR_FILE.bak"

echo -e "${GREEN}✅ New ADR created: $ADR_FILE${NC}"
echo -e "${BLUE}📝 Opening ADR for editing...${NC}"

# Open in default editor
if [ -n "$EDITOR" ]; then
    $EDITOR "$ADR_FILE"
elif command -v code &> /dev/null; then
    code "$ADR_FILE"
elif command -v vim &> /dev/null; then
    vim "$ADR_FILE"
else
    echo -e "${YELLOW}Please open $ADR_FILE in your preferred editor${NC}"
fi

echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Complete all sections of the ADR"
echo -e "  2. Review with stakeholders"
echo -e "  3. Update status to 'Accepted' when approved"
echo -e "  4. Add to decisions/README.md index"
echo -e "  5. Reference in implementation commits"