# Documentation Architecture: Single Source of Truth

## The Problem: Documentation Drift

When documentation lives in multiple places, you get:
- **Duplication**: Same content in README.md and docs/index.md
- **Sync Issues**: Updates in code don't reflect in docs
- **Maintenance Burden**: Two places to update everything

## Our Solution: Single Source of Truth

### 1. Root Files Are Canonical

These files live **only** in the repository root:
- `README.md` - GitHub landing page
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contribution guide
- `LICENSE` - Legal terms

### 2. Docs Site Includes Root Files

We use **symlinks** or **pymdownx.snippets** to include root files in the docs site:

```yaml
# mkdocs.yml
markdown_extensions:
  - pymdownx.snippets:
      base_path: ['.', 'docs']  # Search root and docs/
      check_paths: true
```

### 3. Include Syntax

In any docs file, include content from root:

```markdown
<!-- Include entire file -->
--8<-- "CHANGELOG.md"

<!-- Include specific lines -->
--8<-- "README.md:10:50"

<!-- Include code from source -->
--8<-- "src/provenance/specimen_index.py:15:30"
```

### 4. Symlink for Navigation

For files that need to appear in nav (like CHANGELOG):

```bash
cd docs/
ln -s ../CHANGELOG.md changelog.md
ln -s ../CONTRIBUTING.md contributing.md
```

Then reference in `mkdocs.yml`:
```yaml
nav:
  - Changelog: changelog.md
  - Contributing: contributing.md
```

## Benefits

✅ **Single Source**: Edit once, appears everywhere
✅ **Always Synced**: Docs automatically reflect latest code
✅ **No Duplication**: One canonical version of each file
✅ **Code Examples**: Include actual source code, not copy-paste

## Examples in This Project

### Including Code Snippets

Instead of copying code into docs:
```markdown
<!-- BAD: Duplicated code -->
\`\`\`python
from src.provenance.specimen_index import SpecimenIndex
\`\`\`

<!-- GOOD: Include from source -->
--8<-- "src/provenance/specimen_index.py:15:25"
```

### Including Root Files

Instead of duplicating README content:
```markdown
<!-- BAD: Copy-paste from README -->
# Project Overview
AAFC Herbarium digitization...

<!-- GOOD: Include from root -->
--8<-- "README.md:1:50"
```

## Validation

The docs validation workflow checks:
1. All snippet includes resolve correctly
2. No broken symlinks
3. No duplicate content warnings

Run locally:
```bash
uv run mkdocs build --strict  # Catches broken includes
```

## Migration Guide

To consolidate duplicate docs:

1. **Identify duplicates**: Compare docs/index.md and README.md
2. **Choose canonical source**: Usually root for GitHub visibility
3. **Replace with includes**: Use --8<-- syntax
4. **Test build**: Run `mkdocs build --strict`
5. **Remove duplicates**: Delete old files

---

**Pattern**: [Documentation Quality Gates](decisions/001-documentation-quality-gates.md)
**Status**: Implemented with pymdownx.snippets plugin
