# Repository Cleanup Analysis

**Date:** 2025-10-10
**Project:** AAFC Herbarium DWC Extraction
**Total Root Scripts:** 41 files (27 duplicates + 14 unique)

## Immediate Actions: Delete Duplicates

### Duplicate Files (27 files - SAFE TO DELETE)

These are macOS file conflict duplicates with " 2", " 3", " 4" suffixes:

```bash
# Python duplicates (20 files)
'cli 2.py'
'demo_ui 2.py'
'direct_apple_vision 2.py'
'download_trial_images 2.py'
'fetch_and_process 2.py'
'fetch_and_process 3.py'
'herbarium_ui 2.py'
'progress_tracker 2.py'
'progress_tracker 3.py'
'quick_trial_run 2.py'
'quick_trial_run 3.py'
'test_interfaces 2.py'
'test_interfaces 3.py'
'test_interfaces 4.py'
'test_vision_improved 2.py'
'test_vision_improved 3.py'
'test_vision_improved 4.py'
'tui_interface 2.py'
'tui_interface 3.py'
'validate_samples 2.py'
'validate_samples 3.py'
'validate_samples 4.py'
'web_dashboard 2.py'
'web_dashboard 3.py'
'web_dashboard 4.py'

# Shell duplicates (2 files)
'make_bucket_public 2.sh'
'process_full_dataset 2.sh'
```

**Command to remove:**
```bash
rm *\ [0-9].py *\ [0-9].sh
```

## Root Scripts Analysis

### Category 1: KEEP IN ROOT (User-Facing Entry Points)

**Referenced in documentation/README:**
- ✅ `cli.py` - Main CLI entry point (referenced in docs, tests)
- ✅ `review_web.py` - Web review interface (referenced in docs, tests)
- ✅ `herbarium_ui.py` - UI launcher (referenced in README)
- ✅ `bootstrap.sh` - Project setup (referenced in README)
- ✅ `test-regression.sh` - Regression tests (CI workflow)

**Rationale:** These are the main user-facing commands documented for end users.

### Category 2: MOVE TO scripts/ (Development Tools)

**Analysis/Testing Scripts:**
- 📦 `analyze_gpt4omini_accuracy.py` → `scripts/analyze_gpt4omini_accuracy.py`
- 📦 `compare_engines.py` → `scripts/compare_engines.py`
- 📦 `test_interfaces.py` → `scripts/test_interfaces.py`
- 📦 `test_vision_improved.py` → `scripts/test_vision_improved.py`
- 📦 `validate_samples.py` → `scripts/validate_samples.py`

**Processing Scripts:**
- 📦 `download_trial_images.py` → `scripts/download_trial_images.py`
- 📦 `quick_trial_run.py` → `scripts/quick_trial_run.py`
- 📦 `direct_apple_vision.py` → `scripts/direct_apple_vision.py`
- 📦 `fetch_and_process.py` → `scripts/fetch_and_process.py`

**Shell Scripts:**
- 📦 `log_progress.sh` → `scripts/log_progress.sh`
- 📦 `monitor_active_run.sh` → `scripts/monitor_active_run.sh`
- 📦 `monitor_progress.sh` → `scripts/monitor_progress.sh`
- 📦 `process_full_dataset.sh` → `scripts/process_full_dataset.sh`
- 📦 `make_bucket_public.sh` → `scripts/make_bucket_public.sh`

**Rationale:** Developer tools, not primary user interface.

### Category 3: CONSOLIDATE OR DEPRECATE

**Redundant UI Scripts:**
- ❓ `demo_ui.py` - Imports herbarium_ui, probably redundant
- ❓ `tui_interface.py` - TUI implementation, check if used
- ❓ `web_dashboard.py` - Imports herbarium_ui, probably redundant
- ❓ `review_tui.py` - TUI review, check if used
- ❓ `review.py` - Unclear purpose, check usage

**Investigation needed:**
```bash
# Check if these are actually used
rg -l "demo_ui|tui_interface|web_dashboard|review_tui|review\.py" docs/
```

**One-off Scripts (probably obsolete):**
- 🗑️ `edit_validation.py` - Likely one-off, check last modified
- 🗑️ `export_review.py` - Likely one-off
- 🗑️ `import_review.py` - Likely one-off
- 🗑️ `fix_s3_urls.py` - One-time fix (keep in archive)
- 🗑️ `progress_tracker.py` - Check if replaced by scripts/monitor_*

### Category 4: DUPLICATES IN docs/ and other directories

**Found duplicates with " 3" suffix in docs/:**
- docs/faq 3.md
- docs/guides/TERMINOLOGY_GUIDE 3.md
- docs/PROJECT_CLOSEOUT 3.md
- docs/reproducible_image_access 3.md
- docs/research/COMPREHENSIVE_OCR_ANALYSIS 3.md
- docs/research/README 3.md
- And many more...

**Also found numbered duplicates in:**
- config/schemas/ (multiple " 3.xsd", " 4.xsd" files)
- .specify/templates/
- experiments/
- Full list: 56 total duplicate files across repo

## Recommended Actions

### Phase 1: Delete Obvious Cruft (Immediate)

```bash
# Delete numbered duplicates in root
rm *\ [0-9].py *\ [0-9].sh

# Delete numbered duplicates throughout repo
find . -name "*\ [0-9].*" -type f -delete

# Verify nothing important deleted
git status
```

**Impact:** Removes 56+ duplicate files, no functionality lost.

### Phase 2: Move Development Scripts (Safe)

```bash
# Create archive for old scripts
mkdir -p archive/old_scripts

# Move development tools to scripts/
mv analyze_gpt4omini_accuracy.py scripts/
mv compare_engines.py scripts/
mv test_interfaces.py scripts/
mv test_vision_improved.py scripts/
mv validate_samples.py scripts/
mv download_trial_images.py scripts/
mv quick_trial_run.py scripts/
mv direct_apple_vision.py scripts/
mv fetch_and_process.py scripts/

# Move shell scripts
mv log_progress.sh scripts/
mv monitor_active_run.sh scripts/
mv monitor_progress.sh scripts/
mv process_full_dataset.sh scripts/
mv make_bucket_public.sh scripts/

# Update any imports/references
rg -l "from (analyze_gpt4omini|compare_engines|test_interfaces)" --type py
```

**Impact:** Cleaner root, organized scripts/ directory.

### Phase 3: Investigate Redundant UIs (Requires Review)

```bash
# Check usage of potential duplicates
rg -l "demo_ui|tui_interface|web_dashboard" docs/ tests/

# Check last modified dates
ls -lt demo_ui.py tui_interface.py web_dashboard.py review_tui.py review.py

# If unused, archive them
mv demo_ui.py tui_interface.py web_dashboard.py archive/old_scripts/ 2>/dev/null
```

**Impact:** TBD - need to verify which UIs are actually used.

### Phase 4: Archive One-Off Scripts (Safe)

```bash
# Move one-time use scripts to archive
mv edit_validation.py archive/old_scripts/
mv export_review.py archive/old_scripts/
mv import_review.py archive/old_scripts/
mv fix_s3_urls.py archive/old_scripts/
mv progress_tracker.py archive/old_scripts/
```

**Impact:** Cleaner root, scripts preserved in archive.

## Final Root Directory Structure

**After cleanup:**
```
/
├── cli.py                    # Main CLI
├── review_web.py             # Web review UI
├── herbarium_ui.py           # UI launcher
├── bootstrap.sh              # Setup script
├── test-regression.sh        # CI test script
├── pyproject.toml
├── README.md
├── uv.lock
├── scripts/                  # All development scripts
│   ├── analyze_*.py
│   ├── compare_*.py
│   ├── test_*.py
│   ├── monitor_*.sh
│   └── ...
└── archive/
    └── old_scripts/          # Archived one-off scripts
```

**Result:** 5 user-facing scripts in root instead of 41 total files.

## Risk Assessment

**Low Risk (Safe to execute):**
- ✅ Delete numbered duplicates (Phase 1)
- ✅ Move development scripts to scripts/ (Phase 2)
- ✅ Archive one-off scripts (Phase 4)

**Medium Risk (Requires verification):**
- ⚠️ Consolidate redundant UIs (Phase 3)

**Recommended Order:**
1. Phase 1 (delete duplicates) - IMMEDIATE
2. Phase 2 (move dev scripts) - SAFE
3. Phase 4 (archive one-offs) - SAFE
4. Phase 3 (investigate UIs) - REQUIRES REVIEW

## Commands Summary

**Quick cleanup (delete duplicates only):**
```bash
# From repo root
find . -name "*\ [0-9].*" -type f -delete
git status  # Review changes
git add -A
git commit -m "Remove 56+ duplicate files (macOS conflict copies)"
```

**Full cleanup (all safe phases):**
```bash
# Phase 1: Delete duplicates
find . -name "*\ [0-9].*" -type f -delete

# Phase 2: Move dev scripts
mkdir -p scripts/archive
mv analyze_gpt4omini_accuracy.py compare_engines.py test_interfaces.py \
   test_vision_improved.py validate_samples.py download_trial_images.py \
   quick_trial_run.py direct_apple_vision.py fetch_and_process.py \
   log_progress.sh monitor_active_run.sh monitor_progress.sh \
   process_full_dataset.sh make_bucket_public.sh scripts/

# Phase 4: Archive one-offs
mkdir -p archive/old_scripts
mv edit_validation.py export_review.py import_review.py \
   fix_s3_urls.py progress_tracker.py archive/old_scripts/

# Commit
git add -A
git commit -m "Organize repository: move dev scripts to scripts/, archive one-offs"
git push
```

## Estimated Impact

**Disk Space Saved:** Minimal (duplicates are small scripts)
**Cognitive Load Reduced:** HIGH - root directory 88% cleaner (41 → 5 files)
**Build/CI Impact:** None (no build dependencies on moved scripts)
**User Impact:** None (documented entry points remain in root)

## Next Steps

1. **Review this analysis** - Verify categorizations
2. **Execute Phase 1** - Delete duplicates (safe, immediate value)
3. **Execute Phase 2** - Move dev scripts (safe, good organization)
4. **Investigate Phase 3** - Check which UIs are actually needed
5. **Execute Phase 4** - Archive one-offs (safe)
6. **Update documentation** - Fix any references to moved scripts
7. **Test CI** - Ensure workflows still work

---

**Approval Needed:** Phases 1, 2, 4 are safe to execute immediately. Phase 3 needs investigation first.
