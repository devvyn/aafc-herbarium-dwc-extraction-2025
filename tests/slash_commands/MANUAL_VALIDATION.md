# Manual Validation Guide for Slash Commands

**Purpose**: Slash commands (`/specify`, `/plan`, `/tasks`, `/implement`) are Claude Code agent commands that cannot be executed programmatically via subprocess. This guide provides manual testing procedures.

**Issue**: #216 (Post-Merge Follow-up: Documentation Reorganization)
**Feature**: 003-test-feature-for

---

## Why Manual Validation?

Slash commands are executed by the Claude Code SlashCommand tool within an agent session. They are not:
- Shell executables
- Python scripts
- Programs that can be invoked via subprocess

Therefore, automated testing via pytest requires manual execution and verification.

---

## Manual Test Suite

### Prerequisites
1. Active Claude Code agent session
2. Clean git working directory
3. Current feature branch: `003-test-feature-for`

### Test 1: `/specify` Command

**Command**:
```
/specify "Test validation feature"
```

**Expected Results**:
- ✅ Command completes without errors
- ✅ File created: `specs/003-test-feature-for/spec.md`
- ✅ spec.md contains valid markdown
- ✅ spec.md has required sections (User Scenarios, Requirements, etc.)

**Acceptance Criteria**:
- Exit status: Success (no error messages)
- File exists and is readable
- Content follows spec template format

---

### Test 2: `/plan` Command

**Command**:
```
/plan
```

**Expected Results**:
- ✅ Command completes without errors
- ✅ File created: `specs/003-test-feature-for/plan.md`
- ✅ Files created: `research.md`, `data-model.md`
- ✅ Directory created: `contracts/` with contract files

**Acceptance Criteria**:
- Exit status: Success
- All design artifacts present
- plan.md references other artifacts
- Contracts define clear interfaces

---

### Test 3: `/tasks` Command

**Command**:
```
/tasks
```

**Expected Results**:
- ✅ Command completes without errors
- ✅ File created: `specs/003-test-feature-for/tasks.md`
- ✅ Tasks are numbered and ordered by dependencies
- ✅ Parallel tasks marked with [P]

**Acceptance Criteria**:
- Exit status: Success
- tasks.md has task list format
- Dependencies clearly indicated
- Acceptance criteria defined per task

---

### Test 4: `/implement` Command

**Command**:
```
/implement
```

**Expected Results**:
- ✅ Command completes without errors
- ✅ Tasks executed in dependency order
- ✅ Implementation artifacts created
- ✅ Tests pass (if applicable)

**Acceptance Criteria**:
- Exit status: Success
- All tasks marked complete
- Code artifacts created
- No errors during execution

---

## Running the Test Suite

### Quick Validation (10-15 minutes)
Execute all four commands in sequence and verify artifacts:

```bash
# 1. Create test feature
/specify "Test validation feature"

# 2. Generate plan
/plan

# 3. Generate tasks
/tasks

# 4. Execute implementation
/implement

# 5. Verify artifacts
ls -la specs/003-test-feature-for/
```

### Full Validation (30-45 minutes)
Include detailed artifact inspection:

```bash
# After running commands above:

# Verify spec.md
cat specs/003-test-feature-for/spec.md

# Verify plan.md
cat specs/003-test-feature-for/plan.md

# Verify tasks.md
cat specs/003-test-feature-for/tasks.md

# Check contracts
ls -la specs/003-test-feature-for/contracts/

# Run automated tests (if applicable)
uv run pytest tests/slash_commands/
```

---

## Recording Results

### YAML Format
Create `test-results/manual-validation-YYYYMMDD-HHMMSS.yaml`:

```yaml
suite_name: "Slash Command Manual Validation"
execution_date: "2025-10-04T20:00:00"
environment: "manual"
total_commands: 4
passed_count: 4
failed_count: 0
results:
  - command: "/specify"
    status: "PASS"
    artifacts: ["spec.md"]
  - command: "/plan"
    status: "PASS"
    artifacts: ["plan.md", "research.md", "data-model.md", "contracts/"]
  - command: "/tasks"
    status: "PASS"
    artifacts: ["tasks.md"]
  - command: "/implement"
    status: "PASS"
    artifacts: ["implementation artifacts"]
```

### Markdown Format
Create `test-results/manual-validation-YYYYMMDD-HHMMSS.md`:

```markdown
# Slash Command Validation Report

**Date**: 2025-10-04
**Tester**: [Your Name]
**Environment**: manual

## Summary
- Total Commands: 4
- Passed: 4
- Failed: 0

## Results

### ✅ /specify - PASS
- Artifacts: spec.md
- Notes: Spec created successfully with all required sections

### ✅ /plan - PASS
- Artifacts: plan.md, research.md, data-model.md, contracts/
- Notes: All design documents generated correctly

### ✅ /tasks - PASS
- Artifacts: tasks.md
- Notes: Task list properly formatted with dependencies

### ✅ /implement - PASS
- Artifacts: [implementation files]
- Notes: Implementation completed without errors
```

---

## Troubleshooting

### Issue: Command not recognized
**Solution**: Verify you're in a Claude Code agent session. Slash commands only work with Claude Code.

### Issue: Missing artifacts
**Solution**: Check `specs/[branch-name]/` directory. Ensure you're on the correct feature branch.

### Issue: Command times out
**Solution**: Some commands (especially `/implement`) can take several minutes. Wait for completion.

### Issue: Errors during execution
**Solution**: Check error messages. Common issues:
- Missing prerequisites (run `/specify` before `/plan`)
- Invalid spec format
- Dependency conflicts

---

## Integration with Automated Tests

The automated test suite in `tests/slash_commands/test_validation.py` contains the same test cases but is currently skipped:

```bash
# Run automated tests (will skip slash command tests)
uv run pytest tests/slash_commands/ -v

# Run only the tests that can be automated
uv run pytest tests/slash_commands/test_report_generation.py
```

To enable automated testing in the future:
1. Implement Claude Code CLI wrapper
2. Update `CommandExecutor` to use wrapper
3. Remove `@pytest.mark.skip` decorators
4. Run: `pytest tests/slash_commands/ -v`

---

## Success Criteria

**Feature validation complete when**:
- ✅ All 4 slash commands execute without errors
- ✅ All expected artifacts created
- ✅ Artifacts have correct content and format
- ✅ Manual test report generated (YAML + Markdown)
- ✅ Results documented in test-results/

**Ready for**: Issue #216 completion, slash command infrastructure validated
