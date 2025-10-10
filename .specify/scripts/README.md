# Specification Checkpoint Scripts

Automation scripts to streamline the specification checkpoint process and ensure consistent adoption.

## Available Scripts

### 🚀 `quick-assess.sh` - Feature Assessment
**Purpose**: Streamline the quick assessment process for new features
**Usage**:
```bash
.specify/scripts/quick-assess.sh
```
**What it does**:
- Creates assessment file from template
- Opens in your preferred editor (respects $EDITOR)
- Provides guidance on next steps based on assessment outcome

### 📋 `new-adr.sh` - Architecture Decision Records
**Purpose**: Create new ADR with proper numbering and formatting
**Usage**:
```bash
.specify/scripts/new-adr.sh "decision-title-in-kebab-case"
```
**Examples**:
```bash
.specify/scripts/new-adr.sh "database-selection-strategy"
.specify/scripts/new-adr.sh "api-authentication-approach"
```
**What it does**:
- Finds next available ADR number automatically
- Creates ADR file with proper naming convention
- Pre-fills template with title and date
- Opens in your preferred editor

### ✅ `check-commit.sh` - Commit Validation
**Purpose**: Validate commit messages follow specification guidelines
**Usage**:
```bash
.specify/scripts/check-commit.sh "your commit message"
```
**What it does**:
- Checks for appropriate specification references
- Validates commit type compliance
- Provides specific guidance for improvements
- Returns exit codes for CI/CD integration

## Integration Examples

### Git Hooks
Add to `.git/hooks/commit-msg` to automatically validate commits:
```bash
#!/bin/bash
.specify/scripts/check-commit.sh "$(cat $1)"
```

### Development Workflow
```bash
# 1. Start with assessment
.specify/scripts/quick-assess.sh

# 2. If architecture decision needed
.specify/scripts/new-adr.sh "my-decision"

# 3. Before committing
.specify/scripts/check-commit.sh "feat: implement new feature

Ref: .specify/features/001-feature/spec.md"
```

### CI/CD Integration
Add to your CI pipeline to ensure specification compliance:
```yaml
- name: Check commit messages
  run: |
    git log --format="%s%n%b" -1 | .specify/scripts/check-commit.sh
```

## Script Configuration

### Editor Selection
Scripts respect the following editor priority:
1. `$EDITOR` environment variable
2. VS Code (`code` command)
3. Vim (`vim` command)
4. Manual instruction if none available

### Customization
All scripts use consistent color coding:
- 🟢 **Green**: Success/completion messages
- 🟡 **Yellow**: Warnings/suggestions
- 🔵 **Blue**: Information/guidance
- 🔴 **Red**: Errors/validation failures

## Troubleshooting

### Script Not Executable
```bash
chmod +x .specify/scripts/*.sh
```

### Template Not Found
Ensure you're running scripts from the repository root directory.

### Editor Not Opening
Set your preferred editor:
```bash
export EDITOR=code  # VS Code
export EDITOR=vim   # Vim
export EDITOR=nano  # Nano
```

## Contributing to Scripts

When modifying scripts:
1. Maintain consistent color coding and output format
2. Include helpful error messages and guidance
3. Test on different platforms (macOS, Linux)
4. Update this README with any new functionality
5. Follow shell scripting best practices (set -e, proper quoting)

---

**Making specification checkpoints effortless through automation! 🚀**
