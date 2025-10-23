# Environment Snapshots for Reproducibility

**Pattern:** Extract Docker wisdom (declarative environments) without the baggage (daemon, containers)

## Overview

Environment snapshots capture the complete execution context for reproducibility tracking. Every extraction run now automatically saves:

- Python version and executable path
- Platform information (OS, architecture)
- Git commit and dirty state
- All installed dependencies with versions
- Exact command that was executed
- Timestamp

**No Docker daemon required.** Simple JSON file with full reproducibility.

## Usage

### Automatic Capture

Environment snapshots are automatically captured by extraction scripts:

```bash
python scripts/extract_openrouter.py \
    --input /tmp/imgcache \
    --output my_extraction_run \
    --model qwen-vl-72b-free
```

**Output:** `my_extraction_run/environment.json`

### Manual Capture

Use the utility function directly:

```python
from src.utils.environment import save_environment_snapshot
from pathlib import Path

# Capture current environment
snapshot_path = save_environment_snapshot(
    output_dir=Path("output"),
    run_id="my_run_001",
    command="python cli.py process ..."
)
```

### Load and Compare

```python
from src.utils.environment import load_environment_snapshot, compare_environments

# Load snapshots
env1 = load_environment_snapshot(Path("run1/environment.json"))
env2 = load_environment_snapshot(Path("run2/environment.json"))

# Compare
differences = compare_environments(env1, env2)

# Check if environments are identical
if not differences:
    print("Environments are identical - fully reproducible!")
else:
    print(f"Found {len(differences)} differences:")
    for key, diff in differences.items():
        print(f"  {key}: {diff}")
```

## Snapshot Format

```json
{
  "run_id": "openrouter_run_20251010_115131",
  "timestamp": "2025-10-10T20:19:25.943256+00:00",
  "python": {
    "version": "3.13.5 (main, Jun 11 2025, ...)",
    "version_info": {
      "major": 3,
      "minor": 13,
      "micro": 5
    },
    "executable": "/usr/local/bin/python3"
  },
  "platform": {
    "system": "Darwin",
    "release": "26.0.1",
    "version": "Darwin Kernel Version 26.0.1...",
    "machine": "arm64",
    "platform": "macOS-26.0.1-arm64-arm-64bit-Mach-O"
  },
  "git": {
    "commit": "a62bc43673f4d8e2b1a5c9d7e3f0a1b2c4d5e6f7",
    "branch": "main",
    "dirty": true
  },
  "dependencies": {
    "openai": "1.45.0",
    "pillow": "10.4.0",
    "requests": "2.32.3",
    ...
  },
  "command": "uv run python scripts/extract_openrouter.py --input /tmp/imgcache ..."
}
```

## Benefits

### 1. Full Reproducibility
Every extraction run documents its exact environment - no guessing what versions were used.

### 2. Debugging Failed Runs
When extraction fails, environment snapshot shows if it's a dependency issue, Python version mismatch, or code change (dirty git state).

### 3. Scientific Integrity
Publications can reference exact environment: "Extraction performed with Python 3.13.5, commit a62bc43, dependencies as specified in environment.json"

### 4. Cross-Platform Comparison
Compare environments across different machines/platforms to identify platform-specific issues.

### 5. Dependency Tracking
Track when dependency updates affect extraction quality or performance.

## Wisdom Extracted from Docker

**What we took:**
- Declarative environment specification
- Version pinning for dependencies
- Execution context reproducibility
- Layer-based thinking (git + platform + packages)

**What we left behind:**
- Docker daemon
- Container orchestration
- Image building complexity
- Registry infrastructure
- Volume mounting
- Network configuration

**Result:** Reproducibility without operational overhead.

## Use Cases

### Quality Assurance
```bash
# Compare successful vs failed run environments
python -c "
from src.utils.environment import load_environment_snapshot, compare_environments
from pathlib import Path

good_run = load_environment_snapshot(Path('successful_run/environment.json'))
bad_run = load_environment_snapshot(Path('failed_run/environment.json'))

diffs = compare_environments(good_run, bad_run)
if diffs:
    print('Environment differences found:')
    for key, diff in diffs.items():
        print(f'  {key}: {diff}')
"
```

### Stakeholder Reporting
```bash
# Extract key info for reports
python -c "
import json
from pathlib import Path

env = json.loads(Path('extraction_run/environment.json').read_text())
print(f'Extraction Environment Report')
print(f'=' * 50)
print(f'Run ID: {env[\"run_id\"]}')
print(f'Python: {env[\"python\"][\"version\"][:40]}')
print(f'Platform: {env[\"platform\"][\"platform\"]}')
print(f'Git commit: {env[\"git\"][\"commit\"][:8]}')
print(f'Timestamp: {env[\"timestamp\"]}')
print(f'Command: {env[\"command\"]}')
"
```

### Dependency Auditing
```bash
# List all dependencies for security audit
python -c "
import json
from pathlib import Path

env = json.loads(Path('extraction_run/environment.json').read_text())
print('Installed packages:')
for pkg, version in sorted(env['dependencies'].items()):
    print(f'  {pkg}=={version}')
"
```

## Integration with Existing Patterns

### Git Provenance
Environment snapshots extend git provenance with full dependency context:
- Git commit: Code version
- Git dirty flag: Uncommitted changes
- Dependencies: Library versions
- Platform: Execution environment

### Event Architecture
Future integration: Emit environment snapshot as initial event in extraction event log.

### Content Addressing
Environment snapshots are content-addressable via their JSON representation - hash the file for version tracking.

## FAQ

**Q: Why not use Docker?**
A: Docker adds operational complexity (daemon, images, volumes) for scientific workflows. We extract the wisdom (declarative environments) without the baggage (infrastructure).

**Q: Can I recreate the exact environment from a snapshot?**
A: Yes! Use the dependency list to install exact versions:
```bash
# Extract requirements
jq -r '.dependencies | to_entries | .[] | "\(.key)==\(.value)"' environment.json > requirements.txt

# Install exact versions
pip install -r requirements.txt
```

**Q: What if git commit differs?**
A: Snapshot shows the exact commit used. Check out that commit to recreate code state:
```bash
git checkout $(jq -r '.git.commit' environment.json)
```

**Q: How much disk space do snapshots use?**
A: Typically 10-20KB per snapshot (JSON text). Negligible compared to extraction results.

**Q: Does this slow down extraction?**
A: No. Snapshot capture takes <1 second at startup, one-time cost per run.

## Related Patterns

- **Git Provenance:** Code version tracking (read-only git metadata)
- **Content DAG:** Hash-based content addressing
- **Event Architecture:** Streaming execution events
- **Wisdom Extraction Philosophy:** Extract essential innovation, leave complexity

## Future Enhancements

### Planned
- Environment snapshot comparison in web dashboard
- Automatic environment validation (warn if different from baseline)
- Environment diff visualization

### Possible
- Containerized environment recreation (optional, for users who want Docker)
- Environment snapshot as event in event bus
- Historical environment tracking across all runs

## References

- Implementation: `src/utils/environment.py`
- Wisdom Extraction Philosophy: Desktop/archive/2025-10-research-reports/20251009130206-0600-wisdom-extraction-philosophy.md
- Pattern Analysis: Desktop/20251010140747-CST-wisdom-extraction-applicability.md

## Tags

`reproducibility` `docker-wisdom` `environment` `dependencies` `provenance` `scientific-integrity`
