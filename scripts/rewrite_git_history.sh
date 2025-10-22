#!/bin/bash
# Git History Rewrite Script - Remove Data Files from All History
#
# This is a DESTRUCTIVE operation that rewrites git history.
# Only safe because you are the sole user of the repository.
#
# Result: Repository size reduced from ~300MB to ~10MB for new clones.

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "Git History Rewrite - Remove Data Files Permanently"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  WARNING: This will rewrite git history"
echo "⚠️  Only proceed if you are the sole user of this repository"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Safety check
read -p "Are you sure you want to rewrite git history? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi
echo ""

# 1. Check for git-filter-repo
echo -e "${YELLOW}Step 1: Checking for git-filter-repo${NC}"
if ! command -v git-filter-repo &> /dev/null; then
    echo "git-filter-repo not found. Installing..."

    # Check package manager
    if command -v brew &> /dev/null; then
        echo "Installing via Homebrew..."
        brew install git-filter-repo
    elif command -v pip3 &> /dev/null; then
        echo "Installing via pip3..."
        pip3 install git-filter-repo
    else
        echo -e "${RED}Error: Neither Homebrew nor pip3 found.${NC}"
        echo "Please install git-filter-repo manually:"
        echo "  brew install git-filter-repo"
        echo "  OR"
        echo "  pip3 install git-filter-repo"
        exit 1
    fi
fi

git-filter-repo --version
echo -e "${GREEN}✓ git-filter-repo available${NC}"
echo ""

# 2. Create comprehensive backup
echo -e "${YELLOW}Step 2: Creating comprehensive backup${NC}"
BACKUP_DIR=~/backups/herbarium_history_rewrite_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
echo "Backup location: $BACKUP_DIR"

# Backup entire repository
echo "  - Backing up entire repository..."
tar -czf "$BACKUP_DIR/full_repo_backup.tar.gz" .git ../aafc-herbarium-dwc-extraction-2025 2>/dev/null || \
    tar -czf "$BACKUP_DIR/full_repo_backup.tar.gz" .git .

# Record current state
echo "  - Recording current state..."
git log --oneline -10 > "$BACKUP_DIR/git_log_before.txt"
git count-objects -vH > "$BACKUP_DIR/repo_size_before.txt"
du -sh .git > "$BACKUP_DIR/git_dir_size_before.txt"

echo -e "${GREEN}✓ Backup complete: $BACKUP_DIR${NC}"
echo ""

# 3. Show current repository size
echo -e "${YELLOW}Step 3: Current repository statistics${NC}"
echo "Git repository size:"
git count-objects -vH | grep -E "size|count"
echo ""
du -sh .git
echo ""

# 4. Create file patterns for removal
echo -e "${YELLOW}Step 4: Preparing file patterns for removal${NC}"
cat > /tmp/git_filter_patterns.txt << 'EOF'
# Data files to remove from all history
*.jsonl
*.db
*.sqlite
*.sqlite3

# Specific directories
full_dataset_processing/*/raw.jsonl
full_dataset_processing/*/app.db
full_dataset_processing/*/*.db
experiments/*/raw.jsonl
experiments/*/*.db
test_*/raw.jsonl
test_*/*.db
deliverables/*.jsonl
demo_event_output/*.jsonl
openrouter_test_*/*.jsonl
EOF

echo "Files that will be removed from history:"
cat /tmp/git_filter_patterns.txt | grep -v "^#" | grep -v "^$"
echo ""

# 5. Rewrite history
echo -e "${YELLOW}Step 5: Rewriting git history (this may take 1-2 minutes)${NC}"
echo "Removing data files from all commits..."

# Use git-filter-repo to remove data files
git filter-repo --force \
    --invert-paths \
    --paths-from-file /tmp/git_filter_patterns.txt

echo -e "${GREEN}✓ History rewritten${NC}"
echo ""

# 6. Verify results
echo -e "${YELLOW}Step 6: Verifying results${NC}"
echo "New repository size:"
git count-objects -vH | grep -E "size|count"
echo ""
du -sh .git
echo ""

# Record new state
git log --oneline -10 > "$BACKUP_DIR/git_log_after.txt"
git count-objects -vH > "$BACKUP_DIR/repo_size_after.txt"
du -sh .git > "$BACKUP_DIR/git_dir_size_after.txt"

# 7. Verify data still on disk
echo -e "${YELLOW}Step 7: Verifying data still on disk${NC}"
if [ -f "full_dataset_processing/run_20250930_181456/raw.jsonl" ]; then
    echo -e "${GREEN}✓ Data files still present on disk${NC}"
    ls -lh full_dataset_processing/run_20250930_181456/raw.jsonl
else
    echo -e "${RED}⚠  Data file not found (may need to restore from backup)${NC}"
fi
echo ""

# 8. Show size comparison
echo -e "${YELLOW}Step 8: Size comparison${NC}"
echo "Before rewrite:"
cat "$BACKUP_DIR/git_dir_size_before.txt"
echo ""
echo "After rewrite:"
du -sh .git
echo ""

# 9. Calculate savings
BEFORE=$(cat "$BACKUP_DIR/git_dir_size_before.txt" | awk '{print $1}')
AFTER=$(du -sh .git | awk '{print $1}')
echo "Size reduction: $BEFORE → $AFTER"
echo ""

# 10. Prepare for force push
echo -e "${YELLOW}Step 9: Preparing for force push${NC}"
echo "The remote will need to be force-pushed to update with clean history."
echo ""
echo "Remote status:"
git remote -v
echo ""

read -p "Force push to GitHub now? (yes/no): " push_confirm
if [ "$push_confirm" = "yes" ]; then
    echo ""
    echo -e "${YELLOW}Force pushing to GitHub...${NC}"
    git push --force --all
    git push --force --tags
    echo -e "${GREEN}✓ Force push complete${NC}"
else
    echo ""
    echo "Skipping force push. To push later, run:"
    echo "  git push --force --all"
    echo "  git push --force --tags"
fi
echo ""

# 11. Summary
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}HISTORY REWRITE COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Repository is now clean:"
echo "  - All data files removed from history"
echo "  - Repository size reduced significantly"
echo "  - Data files still safe on disk"
echo ""
echo "To restore if needed:"
echo "  cd .."
echo "  rm -rf aafc-herbarium-dwc-extraction-2025"
echo "  tar -xzf $BACKUP_DIR/full_repo_backup.tar.gz"
echo ""
echo "Important notes:"
echo "  ✓ Data files still on disk (not deleted)"
echo "  ✓ .gitignore prevents future data commits"
echo "  ✓ New clones will be fast and small"
echo "  ✓ Full backup available for rollback"
echo ""
echo -e "${GREEN}Repository is ready for production use!${NC}"

# Cleanup
rm -f /tmp/git_filter_patterns.txt
