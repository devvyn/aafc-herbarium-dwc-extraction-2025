# Scientific Provenance Pattern

**Git-based version tracking for reproducible research outputs**

## Problem Statement

Scientific data outputs must be **cryptographically traceable** to the exact code version that generated them. This enables:

- **Reproducibility**: Re-run analysis with identical code
- **Forensic analysis**: Investigate anomalies by reconstructing environment
- **Compliance**: Demonstrate methodological rigor for publication
- **Trust**: Stakeholders can verify data provenance

## Solution: Git as Metadata Provider

Use git **read-only** to capture version metadata in scientific outputs.

### Core Principle

**Git is NOT a workflow manager** → Git IS a version metadata provider

- ✅ Read git state: `rev-parse`, `status`, `describe`
- ✅ Embed in outputs: Manifests, exports, reports
- ✅ Fail gracefully: Try/except with `"unknown"` fallback
- ❌ Never modify: No programmatic `git add/commit/push`

## Implementation

### Pattern 1: Export Manifest Metadata

**Every scientific data export includes version metadata:**

```python
def create_export_manifest(
    output_path: Path,
    version: str,
    include_git_info: bool = True,
    include_system_info: bool = True
) -> dict:
    """Create manifest with full provenance metadata.

    Embeds git commit hash, branch, dirty flag, and system info
    in export manifest for complete reproducibility.
    """
    manifest = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
    }

    if include_git_info:
        try:
            # Capture commit hash (primary identifier)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                text=True
            ).strip()
            manifest["git_commit"] = commit
            manifest["git_commit_short"] = commit[:7]

            # Capture branch (context)
            try:
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    text=True
                ).strip()
                if branch != "HEAD":  # Not in detached HEAD state
                    manifest["git_branch"] = branch
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            # Flag uncommitted changes (critical for reproducibility)
            try:
                result = subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    text=True
                ).strip()
                manifest["git_dirty"] = bool(result)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Git information not available")
            manifest["git_commit"] = "unknown"

    if include_system_info:
        import platform
        import sys

        manifest["system_info"] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "hostname": platform.node(),
        }

    return manifest
```

**Example output** (`manifest.json`):

```json
{
  "export_timestamp": "2025-10-08T19:30:00Z",
  "version": "1.0.0",
  "git_commit": "a1b2c3d4e5f6789012345678901234567890abcd",
  "git_commit_short": "a1b2c3d",
  "git_branch": "main",
  "git_dirty": false,
  "system_info": {
    "platform": "macOS-14.0-arm64",
    "python_version": "3.11.5",
    "hostname": "aafc-workstation-01"
  }
}
```

### Pattern 2: Processing Run Metadata

**Capture version at processing start:**

```python
def process_specimens(input_dir: Path, output_dir: Path):
    """Process specimens with full provenance tracking."""

    # Capture git commit at start
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()
    except Exception:
        git_commit = None

    # Processing logic...
    results = []
    for specimen_image in input_dir.glob("*.jpg"):
        result = extract_darwin_core(specimen_image)
        result["processing_metadata"] = {
            "git_commit": git_commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

    # Export with manifest
    manifest = create_export_manifest(
        output_dir / "manifest.json",
        version="1.0.0",
        include_git_info=True
    )

    with open(output_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return results
```

### Pattern 3: Quality Assurance Checks

**Use git status to flag risky outputs:**

```python
def export_darwin_core_archive(data: list[dict], output_path: Path):
    """Export Darwin Core archive with provenance validation."""

    # Check for uncommitted changes
    try:
        result = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True
        ).strip()
        if result:
            logger.warning(
                "Exporting from dirty working tree! "
                "Consider committing changes for reproducibility."
            )
            logger.warning(f"Uncommitted changes:\n{result}")
    except Exception:
        pass  # Git not available, continue anyway

    # Export data...
    export_to_dwc(data, output_path)
```

## Best Practices

### 1. Fail Gracefully

**Always wrap git calls in try/except:**

```python
try:
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    git_commit = "unknown"  # Graceful degradation
```

**Why**: Git may not be available (deployed environment, Docker, etc.)

### 2. Flag Dirty State

**Always check `git status --porcelain`:**

```python
result = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
manifest["git_dirty"] = bool(result)
```

**Why**: Uncommitted changes break reproducibility. Flag them prominently.

### 3. Capture at Entry Point

**Record git commit at processing start, not export:**

```python
# ❌ Wrong: Capture at export (may have changed)
def export_results(results):
    git_commit = get_git_commit()  # Too late!

# ✅ Correct: Capture at processing start
def process_data(input_dir):
    git_commit = get_git_commit()  # Locked in
    results = do_processing(input_dir, metadata={"git_commit": git_commit})
    export_results(results)  # Uses captured metadata
```

### 4. Include System Info

**Capture environment details:**

```python
manifest["system_info"] = {
    "platform": platform.platform(),      # OS, architecture
    "python_version": sys.version,        # Python interpreter
    "hostname": platform.node(),          # Which machine
    "dependencies": get_installed_packages()  # Package versions
}
```

**Why**: Code version alone isn't enough—environment matters.

### 5. Document in README

**Make provenance visible to users:**

```markdown
## Data Provenance

All data exports include a `manifest.json` file with:

- **git_commit**: Exact code version used
- **git_dirty**: Whether uncommitted changes were present
- **timestamp**: When processing occurred
- **system_info**: Python version, OS, hostname

To reproduce an export:
\`\`\`bash
git checkout <git_commit>
python cli.py process --input data/ --output results/
\`\`\`
```

## Real-World Example: Herbarium DwC Export

**Current implementation** in `dwc/archive.py:90-118`:

```python
if include_git_info:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        manifest["git_commit"] = commit
        manifest["git_commit_short"] = commit[:7]

        # Branch information
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
            ).strip()
            if branch != "HEAD":
                manifest["git_branch"] = branch
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Dirty flag (critical!)
        try:
            result = subprocess.check_output(
                ["git", "status", "--porcelain"], text=True
            ).strip()
            manifest["git_dirty"] = bool(result)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Git information not available")
        manifest["git_commit"] = "unknown"
```

**Result**: Every DwC export includes complete version provenance.

**Usage**:

```bash
# Export specimens
python cli.py process --input photos/ --output results/

# Check manifest
cat results/manifest.json
```

```json
{
  "version": "1.0.0",
  "git_commit": "a1b2c3d4e5f6789012345678901234567890abcd",
  "git_commit_short": "a1b2c3d",
  "git_branch": "main",
  "git_dirty": false,
  "export_timestamp": "2025-10-08T19:30:00Z",
  "specimen_count": 2885
}
```

**Reproducibility**:

```bash
# Reproduce export from manifest
git checkout a1b2c3d4e5f6789012345678901234567890abcd
python cli.py process --input photos/ --output verification/

# Outputs should be identical (byte-for-byte)
diff results/occurrence.txt verification/occurrence.txt
```

## Anti-Patterns

### ❌ Using Git for Workflow Management

**Don't:**
```python
# Bad: Programmatic git workflow
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Auto-commit"])
subprocess.run(["git", "push"])
```

**Why**: Coupling science code to git workflow is fragile and surprising.

**Exception**: CI/CD automation (GitHub Actions, etc.) is fine.

### ❌ Ignoring Git Dirty State

**Don't:**
```python
# Bad: No dirty flag
git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
manifest["git_commit"] = git_commit
# Missing: check for uncommitted changes!
```

**Why**: Uncommitted changes break reproducibility. Always flag.

### ❌ Assuming Git Is Available

**Don't:**
```python
# Bad: No error handling
git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
```

**Why**: Deployed environments, Docker, etc. may not have git.

**Fix**: Always wrap in try/except.

## Evolution: Content-Addressed DAG

For workflows with **metadata accumulation over time**, consider migrating to Content DAG pattern.

### When to Evolve

Git provenance works for:
- ✅ Single-pass processing
- ✅ Immutable exports
- ✅ Reproducible pipelines

Content DAG adds:
- ✅ **Fragment accumulation**: Metadata added over decades
- ✅ **Cross-repo provenance**: Track data across projects
- ✅ **Duplicate detection**: Same content = same hash
- ✅ **No git dependency**: Works without repository

### Migration Example

**Current (git-based)**:
```python
manifest["git_commit"] = get_git_commit()
manifest["specimen_id"] = "AAFC-12345"
```

**Enhanced (Content DAG)**:
```python
from content_dag import hash_content, create_dag_node

# Hash specimen image (identity = content)
image_hash = hash_content("specimen.jpg")

# Create DAG node linking image to metadata
metadata_hash = hash_content("metadata.json")
dag_node = create_dag_node(
    metadata_hash,
    inputs=[image_hash],
    metadata={
        "git_commit": get_git_commit(),  # Still include!
        "specimen_id": "AAFC-12345",
        "type": "darwin_core_export"
    }
)
```

**Benefits**:
- Git commit still captured (belt-and-suspenders)
- Image content cryptographically linked
- Can query: "Which metadata came from which image?"
- Fragments can accumulate over time (georeference corrections, taxonomic updates)

**See**: `/Users/devvynmurphy/devvyn-meta-project/docs/CONTENT_DAG_PATTERN.md` for full pattern.

## Standardized Metadata Schema

**Common format for all AAFC science projects:**

```json
{
  "provenance": {
    "version": "1.0.0",
    "git_commit": "a1b2c3d",
    "git_commit_short": "a1b2c3d",
    "git_branch": "main",
    "git_dirty": false,
    "content_hash": "sha256:...",  // Optional: Content DAG
    "timestamp": "2025-10-08T19:30:00Z"
  },
  "system": {
    "platform": "macOS-14.0-arm64",
    "python_version": "3.11.5",
    "hostname": "aafc-workstation-01",
    "dependencies": {
      "numpy": "1.24.0",
      "pandas": "2.0.0"
    }
  },
  "processing": {
    "input_count": 2885,
    "output_count": 2885,
    "duration_seconds": 1234.56,
    "errors": 0
  }
}
```

## References

- **Git Internals**: https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain
- **Scientific Reproducibility**: https://www.nature.com/articles/d41586-019-00089-3
- **Content DAG Pattern**: `~/devvyn-meta-project/docs/CONTENT_DAG_PATTERN.md`
- **AAFC Herbarium Implementation**: `dwc/archive.py:90-118`, `cli.py:519`

## Summary

**Three simple rules for scientific provenance:**

1. **Capture git commit** at processing start
2. **Flag dirty state** to warn about uncommitted changes
3. **Fail gracefully** if git unavailable

**Result**: Every output is cryptographically traceable to the code that created it.

**Evolution**: Consider Content DAG for metadata fragment accumulation over time.

---

**Status**: Production-tested in AAFC Herbarium project (2,885 specimens)

**Cross-project adoption**: Recommended for all scientific data pipelines
