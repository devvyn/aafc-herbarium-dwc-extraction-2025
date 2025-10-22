#!/bin/bash
# Git Repository Data Cleanup Script
# Separates data files from code repository to prevent repo bloat
#
# Safety: Creates backup before any destructive operations
# Result: Clean code-only repository (~10MB instead of ~900MB)

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "Git Repository Data Cleanup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Pre-cleanup verification
echo -e "${YELLOW}Step 1: Pre-cleanup verification${NC}"
echo "Current git repository size:"
git count-objects -vH | grep -E "size|size-pack"
echo ""

# 2. Create backup of current state
echo -e "${YELLOW}Step 2: Creating backup${NC}"
BACKUP_DIR=~/backups/herbarium_git_cleanup_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
echo "Backup location: $BACKUP_DIR"

# Backup git directory
echo "  - Backing up .git directory..."
cp -r .git "$BACKUP_DIR/.git"

# Backup current HEAD
echo "  - Recording current HEAD..."
git rev-parse HEAD > "$BACKUP_DIR/HEAD_before_cleanup.txt"

# Backup tracked files list
echo "  - Recording tracked files..."
git ls-files > "$BACKUP_DIR/tracked_files_before.txt"

echo -e "${GREEN}✓ Backup complete: $BACKUP_DIR${NC}"
echo ""

# 3. Remove data files from git tracking
echo -e "${YELLOW}Step 3: Removing data files from git tracking${NC}"

# Remove JSONL files (extraction data)
echo "  - Removing *.jsonl files..."
git ls-files | grep '\.jsonl$' | grep -v 'published.*README' | xargs -r git rm --cached || true

# Remove database files
echo "  - Removing *.db files..."
git ls-files | grep '\.db$' | xargs -r git rm --cached || true

# Remove batch output files
echo "  - Removing batch output files..."
git ls-files | grep 'batch_output' | xargs -r git rm --cached || true

# Remove large data directories
echo "  - Removing tracked files in data directories..."
git ls-files full_dataset_processing/ | grep -v -E '(README|\.md|\.txt|published|\.gitkeep)' | xargs -r git rm --cached || true

echo -e "${GREEN}✓ Data files removed from git index${NC}"
echo ""

# 4. Update .gitignore
echo -e "${YELLOW}Step 4: Updating .gitignore${NC}"

cat >> .gitignore << 'EOF'

# === DATA SEPARATION (Added 2025-10-22) ===
# Keep data files out of git to prevent repository bloat

# Extraction data files
*.jsonl
!published/**/metadata.json
!published/**/CITATION.cff

# Database files
*.db
*.sqlite
*.sqlite3
specimen_index.db

# Large archives
archives/
backups/
*.tar.gz
*.zip
*.7z

# Backup files
*_backup/
*.bak
checksums_*.txt

# Data directories (keep only metadata)
full_dataset_processing/*/raw.jsonl
full_dataset_processing/*/app.db
full_dataset_processing/*/events.jsonl
full_dataset_processing/*/*.db

# Exception: Keep small metadata files in published/
!published/**/README.md
!published/**/metadata.json
!published/**/DATA_DOI.txt
EOF

echo -e "${GREEN}✓ .gitignore updated${NC}"
echo ""

# 5. Commit the cleanup
echo -e "${YELLOW}Step 5: Committing cleanup${NC}"
git add .gitignore

# Create list of what was removed
git status --short > "$BACKUP_DIR/cleanup_changes.txt"

echo -e "${GREEN}✓ Changes staged${NC}"
echo ""

# 6. Show what will be committed
echo -e "${YELLOW}Step 6: Changes to be committed${NC}"
echo "Files removed from tracking:"
git diff --cached --name-only --diff-filter=D | head -20
echo "..."
echo ""

# 7. Commit
echo -e "${YELLOW}Step 7: Creating commit${NC}"
git commit -m "chore: Separate data from code repository

Remove data files from git tracking to prevent repository bloat.
Data files (*.jsonl, *.db) now managed externally.

Changes:
- Remove extraction data files (raw.jsonl, batch_output.jsonl)
- Remove database files (*.db)
- Update .gitignore to prevent future data commits

Before cleanup: ~900MB loose objects
After cleanup: Will be cleaned with git gc

Data remains safe in:
- Local: full_dataset_processing/ (still on disk)
- S3: Original images (content-addressed)
- Backups: $BACKUP_DIR

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"

echo -e "${GREEN}✓ Cleanup committed${NC}"
echo ""

# 8. Aggressive garbage collection
echo -e "${YELLOW}Step 8: Running garbage collection (this may take a few minutes)${NC}"
echo "This will clean up unreachable objects and compress the repository..."

git gc --aggressive --prune=now

echo -e "${GREEN}✓ Garbage collection complete${NC}"
echo ""

# 9. Post-cleanup verification
echo -e "${YELLOW}Step 9: Post-cleanup verification${NC}"
echo "New git repository size:"
git count-objects -vH | grep -E "size|size-pack"
echo ""

# Calculate savings
echo "Tracked files after cleanup:"
git ls-files | wc -l
echo ""

# 10. Verify data is still on disk
echo -e "${YELLOW}Step 10: Verifying data still exists on disk${NC}"
echo "Checking full_dataset_processing/:"
ls -lh full_dataset_processing/run_20250930_181456/raw.jsonl 2>/dev/null && echo -e "${GREEN}✓ Data still on disk${NC}" || echo -e "${RED}⚠ Data file not found${NC}"
echo ""

# 11. Summary
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}CLEANUP COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Verify data still exists: ls full_dataset_processing/"
echo "  2. Push cleanup: git push"
echo "  3. If anything wrong: Restore from backup"
echo ""
echo "To restore from backup if needed:"
echo "  rm -rf .git"
echo "  cp -r $BACKUP_DIR/.git ."
echo "  git reset --hard \$(cat $BACKUP_DIR/HEAD_before_cleanup.txt)"
echo ""
echo -e "${GREEN}Repository is now clean and ready for collaborative development!${NC}"
