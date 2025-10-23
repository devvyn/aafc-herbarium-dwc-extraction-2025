#!/bin/bash
#
# Audit and optionally fix absolute documentation URLs
#
# This script finds absolute URLs pointing to aafc.devvyn.ca in markdown files
# and can optionally convert them to relative links.
#
# Usage:
#   ./scripts/audit-doc-links.sh [--fix]
#
# Options:
#   --fix    Automatically convert absolute URLs to relative links
#
# Exit codes:
#   0 - No issues found (or all fixed)
#   1 - Issues found (audit mode only)

set -e

FIX_MODE=false
if [ "$1" = "--fix" ]; then
    FIX_MODE=true
fi

echo "════════════════════════════════════════════════════════════"
echo "Documentation Link Audit"
echo "════════════════════════════════════════════════════════════"
echo ""

# Find all markdown files
MD_FILES=$(find docs -name "*.md" 2>/dev/null || true)
MD_FILES="$MD_FILES $(find . -maxdepth 1 -name "*.md" 2>/dev/null || true)"

ISSUES_FOUND=0
FILES_WITH_ISSUES=()

for file in $MD_FILES; do
    # Skip if file doesn't exist
    [ -f "$file" ] || continue

    # Check for problematic patterns
    MATCHES=$(grep -n 'https://aafc\.devvyn\.ca/docs/' "$file" 2>/dev/null || true)

    if [ -n "$MATCHES" ]; then
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        FILES_WITH_ISSUES+=("$file")

        echo "❌ $file"
        echo "$MATCHES" | while IFS=: read -r line_num content; do
            echo "   Line $line_num: $content"
        done
        echo ""

        if [ "$FIX_MODE" = true ]; then
            # Convert absolute URLs to relative
            # https://aafc.devvyn.ca/docs/FILE.md → FILE.md
            # https://aafc.devvyn.ca/docs/subdir/FILE.md → subdir/FILE.md
            sed -i '' 's|https://aafc\.devvyn\.ca/docs/||g' "$file"
            echo "   ✅ Fixed automatically"
            echo ""
        fi
    fi
done

echo "════════════════════════════════════════════════════════════"
echo "Summary"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ No absolute documentation URLs found"
    echo ""
    echo "All documentation links use relative paths correctly."
    exit 0
fi

if [ "$FIX_MODE" = true ]; then
    echo "✅ Fixed $ISSUES_FOUND file(s) with absolute URLs"
    echo ""
    echo "Changed files:"
    for f in "${FILES_WITH_ISSUES[@]}"; do
        echo "  - $f"
    done
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff"
    echo "  2. Test locally: uv run mkdocs serve"
    echo "  3. Commit: git add . && git commit -m 'docs: Fix absolute URLs'"
    exit 0
else
    echo "❌ Found $ISSUES_FOUND file(s) with absolute URLs"
    echo ""
    echo "Affected files:"
    for f in "${FILES_WITH_ISSUES[@]}"; do
        echo "  - $f"
    done
    echo ""
    echo "Fix options:"
    echo "  1. Automatic: ./scripts/audit-doc-links.sh --fix"
    echo "  2. Manual: Edit files to use relative links"
    echo ""
    echo "Example fix:"
    echo "  ❌ https://aafc.devvyn.ca/docs/RELEASE_2_0_PLAN.md"
    echo "  ✅ RELEASE_2_0_PLAN.md"
    echo ""
    exit 1
fi
