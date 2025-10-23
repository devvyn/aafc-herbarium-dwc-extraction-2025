#!/bin/bash
#
# Pre-commit hook to prevent absolute documentation URLs
#
# This script checks for absolute URLs pointing to our documentation site,
# which should use relative markdown links instead for MkDocs compatibility.
#
# Usage:
#   Called automatically by pre-commit framework
#   Manual: .github/scripts/check-doc-links.sh
#
# Exit codes:
#   0 - No issues found
#   1 - Absolute doc URLs found (commit blocked)

set -e

echo "Checking for absolute documentation URLs..."

# Get list of staged markdown files
STAGED_MD_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$' || true)

if [ -z "$STAGED_MD_FILES" ]; then
    echo "✅ No markdown files to check"
    exit 0
fi

# Check for absolute aafc.devvyn.ca URLs in docs/ paths
# Exclude README.md badges (those are fine as external references)
FOUND_ISSUES=0

for file in $STAGED_MD_FILES; do
    # Skip if file doesn't exist (deleted)
    [ -f "$file" ] || continue

    # Check for problematic patterns
    if grep -n 'https://aafc\.devvyn\.ca/docs/' "$file" 2>/dev/null; then
        echo ""
        echo "❌ Found absolute doc URL in: $file"
        echo ""
        echo "Use relative links instead:"
        echo "  ❌ https://aafc.devvyn.ca/docs/RELEASE_2_0_PLAN.md"
        echo "  ✅ RELEASE_2_0_PLAN.md"
        echo ""
        FOUND_ISSUES=1
    fi

    # Also catch URLs without /docs/ prefix that might still be problematic
    if grep -n 'https://aafc\.devvyn\.ca/[A-Z_].*\.md' "$file" 2>/dev/null; then
        echo ""
        echo "⚠️  Found potential absolute doc URL in: $file"
        echo "   (URLs with .md extension should use relative paths)"
        echo ""
        FOUND_ISSUES=1
    fi
done

if [ $FOUND_ISSUES -eq 1 ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "ERROR: Absolute documentation URLs detected"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "MkDocs converts docs/file.md → https://aafc.devvyn.ca/file/"
    echo "Absolute URLs break when files move or site structure changes."
    echo ""
    echo "Fix by using relative markdown links:"
    echo "  - Same directory:     [Link](file.md)"
    echo "  - Subdirectory:       [Link](subdir/file.md)"
    echo "  - Parent directory:   [Link](../file.md)"
    echo ""
    echo "See CONTRIBUTING.md for complete guidelines."
    echo ""
    exit 1
fi

echo "✅ No absolute documentation URLs found"
exit 0
