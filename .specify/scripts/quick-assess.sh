#!/bin/bash
# Quick Feature Assessment Script
# Streamlines the assessment process for new features

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create assessment from template
ASSESSMENT_FILE=".specify/current-assessment.md"
TEMPLATE_FILE=".specify/templates/quick-feature-assessment.md"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_FILE${NC}"
    exit 1
fi

# Copy template to current assessment
cp "$TEMPLATE_FILE" "$ASSESSMENT_FILE"

echo -e "${GREEN}✅ Assessment template created at $ASSESSMENT_FILE${NC}"
echo -e "${BLUE}📝 Opening assessment for editing...${NC}"

# Open in default editor
if [ -n "$EDITOR" ]; then
    $EDITOR "$ASSESSMENT_FILE"
elif command -v code &> /dev/null; then
    code "$ASSESSMENT_FILE"
elif command -v vim &> /dev/null; then
    vim "$ASSESSMENT_FILE"
else
    echo -e "${YELLOW}Please open $ASSESSMENT_FILE in your preferred editor${NC}"
fi

echo ""
echo -e "${GREEN}Assessment Outcomes:${NC}"
echo -e "  ${BLUE}Full Spec Required${NC} → Run: /specify \"Your feature description\""
echo -e "  ${BLUE}Lightweight Docs${NC} → Document in commit message with purpose/approach/testing"
echo -e "  ${BLUE}Simple Implementation${NC} → Include rationale in commit message"
echo ""
echo -e "${YELLOW}Remember to save your assessment for future reference!${NC}"