# Contract: CommandExecutor

**Component**: Test execution engine
**Phase**: 1 (Design)
**Date**: 2025-10-02
**Updated**: 2025-10-04

## Purpose
Execute slash commands in isolated test environment and capture results for validation.

## ⚠️ Known Limitation

**Slash commands cannot be executed via subprocess**

Claude Code slash commands (`/specify`, `/plan`, `/tasks`, `/implement`) are agent-level
commands executed via the SlashCommand tool. They are NOT shell executables and cannot
be invoked programmatically via subprocess.run().

**Current Status**: Implementation attempts subprocess execution but slash command tests
are skipped. Manual validation required (see `tests/slash_commands/MANUAL_VALIDATION.md`).

**Future Enhancement**: Implement Claude Code CLI wrapper to enable programmatic execution.

## Public Interface

### `execute_command(command: TestCommand) -> ValidationResult`
Execute a single slash command and return validation result.

**Input**:
- `command`: TestCommand object with name, parameters, expected behavior

**Output**:
- `ValidationResult` object with status, exit code, timing, artifacts

**Preconditions**:
- Test environment isolated (branch/directory)
- Command infrastructure available (`.specify/scripts/`)
- Sufficient permissions to create test artifacts

**Postconditions**:
- Command executed exactly once
- All output captured (stdout, stderr)
- Artifacts recorded if created
- Test environment cleaned up

**Error Handling**:
- Timeout after 60 seconds → FAIL with timeout error
- Missing command script → FAIL with file not found
- Permission denied → FAIL with permission error
- Any exception → FAIL with exception details in stderr

### `create_test_environment() -> str`
Create isolated test environment (branch or directory).

**Output**:
- Path/identifier of test environment

**Postconditions**:
- Environment exists and is writable
- Environment isolated from production
- Environment can be safely deleted

### `cleanup_test_environment(env_id: str) -> None`
Remove test environment after validation complete.

**Input**:
- `env_id`: Environment identifier from create_test_environment()

**Postconditions**:
- Test artifacts removed
- Branches deleted if applicable
- No residual test data

## Implementation Constraints

- MUST use subprocess for command execution (not direct function calls)
- MUST capture both stdout and stderr separately
- MUST record execution time with precision to 0.01 seconds
- MUST verify exit code = 0 for PASS status
- MUST check artifact existence after command completes

## Dependencies

- Python subprocess module
- Git for branch management (if branch isolation used)
- File system access for temporary directories

## Testing Strategy

- **Unit tests**: Mock subprocess, verify result parsing
- **Integration tests**: Execute actual commands in test environment
- **Error tests**: Verify timeout, permission, not-found handling

---

**Contract Status**: Defined
**Implementer**: TBD (Phase 2)
