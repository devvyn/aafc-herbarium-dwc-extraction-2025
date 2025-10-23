# Pre-Commit Checklist

**Run these checks BEFORE `git commit` to prevent CI failures**

## Quick Checks (Always Run)

### 1. Lint and Format
```bash
# Auto-fix linting issues
uv run ruff check . --fix

# Auto-format code
uv run ruff format .
```

### 2. Run Tests
```bash
# Quick unit tests (< 30 seconds)
uv run python -m pytest tests/unit/ -q

# Full test suite (if time permits)
uv run python -m pytest
```

### 3. Check for Common Issues
```bash
# Trailing whitespace and file endings (pre-commit hooks will catch this)
git diff --check

# Check for large files
find . -type f -size +1M -not -path "./.git/*" -not -path "./.venv/*"
```

## Documentation Changes (If Editing Docs)

### 4. Validate Links
```bash
# Check for broken markdown links
uv run python -m pytest tests/unit/test_docs_links.py 2>/dev/null || \
  echo "⚠️  No link checker - verify manually"
```

### 5. Check Version Consistency
```bash
# Find version references in docs
rg "v[0-9]+\.[0-9]+\.[0-9]+" --type md docs/ README.md | grep -v archive

# Current version should be:
# v2.0.0 (released)
# v2.1.0 (next milestone)
```

### 6. Verify Documentation Structure
```bash
# All docs should be linked from docs/README.md
fd -e md . docs/ | while read file; do
  basename=$(basename "$file")
  if ! rg -q "$basename" docs/README.md; then
    echo "⚠️  Not linked in docs/README.md: $file"
  fi
done
```

## Code Changes (If Editing Source)

### 7. Type Checking (Optional)
```bash
# If mypy is installed
uv run mypy src/ --ignore-missing-imports 2>/dev/null || \
  echo "ℹ️  mypy not configured"
```

### 8. Import Checks
```bash
# Check for unused imports
uv run ruff check . --select F401

# Check for missing imports
uv run python -c "import sys; sys.path.insert(0, '.'); import src"
```

## Pre-Commit Hook (Automated)

The repository has pre-commit hooks that run automatically on `git commit`:
- ✅ Trim trailing whitespace
- ✅ Fix end of files
- ✅ Check YAML syntax
- ✅ Check for large files (>500KB)
- ✅ Check for merge conflicts
- ✅ Run ruff linting
- ✅ Run ruff formatting

**If hooks fail**: Fix issues and `git add` changes, then retry commit.

## One-Liner Quick Check

```bash
# Run before every commit
uv run ruff check . --fix && \
uv run ruff format . && \
uv run python -m pytest tests/unit/ -q && \
git diff --check && \
echo "✅ All checks passed! Safe to commit."
```

## Common Failure Patterns

### Ruff Linting Failures
```bash
# Fix: Auto-fix most issues
uv run ruff check . --fix

# Manual fixes may be needed for:
# - Unused variables (prefix with _)
# - Complex logic issues
# - Import ordering
```

### Test Failures
```bash
# Run specific failing test with verbose output
uv run python -m pytest tests/path/to/test.py::test_name -vv

# Check for:
# - Outdated fixtures
# - Missing test data files
# - Environment dependencies
```

### Documentation Link Failures
```bash
# Find broken links
fd -e md -x grep -H "](.*\.md)" {} \; | grep -v "http"

# Common issues:
# - Case sensitivity (use lowercase filenames)
# - Moved files (update all references)
# - Relative vs absolute paths
```

## Integration with Git Workflow

### Recommended Workflow
```bash
# 1. Make changes
vim src/my_file.py

# 2. Run quick checks
uv run ruff check . --fix && uv run pytest tests/unit/ -q

# 3. Stage changes
git add src/my_file.py

# 4. Commit (pre-commit hooks run automatically)
git commit -m "feat: add new feature"

# 5. If hooks fail, fix and amend
uv run ruff format .
git add -u
git commit --amend --no-edit

# 6. Push (CI runs full checks)
git push
```

## CI Checks (GitHub Actions)

CI runs additional checks that may not run locally:
- Full test suite on multiple Python versions
- Documentation build (MkDocs)
- Link validation across entire site
- Code coverage reporting

**Pro tip**: If CI fails, check the GitHub Actions logs and reproduce locally:
```bash
# Get CI Python version
python --version

# Run same commands as CI
uv run python -m pytest tests/
uv run mkdocs build --strict
```

## Preventing Common Mistakes

### ❌ Don't:
- Commit without running tests
- Skip `ruff check --fix` (auto-fixes most issues)
- Commit large data files (check `.gitignore`)
- Leave TODO comments without tracking issues
- Break documentation links when renaming files

### ✅ Do:
- Run quick check one-liner before every commit
- Fix all ruff warnings (not just errors)
- Update docs when changing APIs
- Test documentation examples
- Keep commits focused and atomic

## Emergency: Failed CI After Push

If CI fails after you've already pushed:

```bash
# 1. Pull any changes
git pull

# 2. Fix the issue locally
uv run ruff check . --fix
uv run pytest

# 3. Commit fix
git add -u
git commit -m "fix: resolve CI check failure"

# 4. Push fix
git push
```

## Questions?

- **Pre-commit hooks not running?** Run `pre-commit install`
- **Checks too slow?** Use `pytest -k "not slow"` for quick tests
- **Still confused?** See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Remember**: It's much faster to catch issues locally than to wait for CI to fail! 🚀
