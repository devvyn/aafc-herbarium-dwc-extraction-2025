# Testing Standards and Methodology

## Overview

This document establishes testing standards to prevent regressions like the SQLAlchemy compatibility issue that occurred in the web review interface.

## Root Cause Analysis

The SQLAlchemy compatibility bug occurred because:

1. **Interface Mismatch**: `review_web.py` used raw `sqlite3.Connection` but `fetch_candidates()` expected SQLAlchemy `Session`
2. **Missing Integration Tests**: No tests validated the web interface with actual database connections
3. **Untested Code Paths**: Database abstraction layer had gaps in test coverage
4. **Type Safety Gap**: No static type checking to catch interface mismatches early

## Testing Methodology

### 1. Unit Tests

**Requirements:**
- Test all public functions with multiple input scenarios
- Test error conditions and edge cases
- Mock external dependencies
- Achieve >90% code coverage

**Database Layer Testing:**
- Test both SQLAlchemy and raw sqlite3 interfaces when both exist
- Verify data consistency between different access methods
- Test database schema migrations and initialization

**Example:**
```python
def test_sqlalchemy_and_sqlite3_equivalence(tmp_path: Path) -> None:
    """Test that SQLAlchemy and sqlite3 functions return equivalent results."""
    # Setup data with SQLAlchemy
    session = init_db(db_path)
    insert_candidate(session, "run1", "test.jpg", candidate)
    
    # Compare results from both interfaces
    sqlalchemy_results = fetch_candidates(session, "test.jpg")
    sqlite3_results = fetch_candidates_sqlite(conn, "test.jpg")
    
    assert_equivalent_results(sqlalchemy_results, sqlite3_results)
```

### 2. Integration Tests

**Requirements:**
- Test complete workflows end-to-end
- Use real databases (not mocks)
- Test interface boundaries between components
- Validate HTTP endpoints and web interfaces

**Web Interface Testing:**
- Test server startup and shutdown
- Validate HTTP responses and content
- Test database integration with web handlers
- Verify error handling and edge cases

**Example:**
```python
def test_web_review_database_compatibility():
    """Test that review_web.py can handle sqlite3 connections."""
    create_test_database(db_path)
    
    with sqlite3.connect(db_path) as conn:
        candidates = fetch_candidates_sqlite(conn, "test.jpg")
        
    assert len(candidates) > 0
```

### 3. Regression Tests

**Requirements:**
- Add specific tests for each bug discovered
- Include the exact error scenario that caused the issue
- Document the root cause in test docstrings
- Ensure tests fail when the bug is reintroduced

**SQLAlchemy Compatibility:**
```python
def test_fetch_candidates_sqlite_compatibility(tmp_path: Path) -> None:
    """Regression test for SQLAlchemy compatibility issues in web review.
    
    Bug: review_web.py used sqlite3.Connection but fetch_candidates() 
    expected SQLAlchemy Session, causing TypeError in production.
    """
    # Test the exact scenario that failed
```

### 4. Type Safety

**Requirements:**
- Use type hints for all function signatures
- Run mypy in CI pipeline
- Declare interface contracts explicitly
- Use protocols for duck-typed interfaces

**Example:**
```python
from typing import Protocol

class DatabaseConnection(Protocol):
    def execute(self, query: str) -> Any: ...

def fetch_candidates_generic(conn: DatabaseConnection, image: str) -> List[Candidate]:
    """Works with both SQLAlchemy sessions and sqlite3 connections."""
```

## CI/CD Integration

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: uv run python -m pytest tests/unit/
        language: system
        pass_filenames: false
        
      - id: mypy
        name: Type checking
        entry: uv run mypy src/
        language: system
        pass_filenames: false
```

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
          
      - name: Run unit tests
        run: uv run python -m pytest tests/unit/ -v --cov=src/
        
      - name: Run integration tests
        run: uv run python -m pytest tests/integration/ -v
        
      - name: Type checking
        run: uv run mypy src/
        
      - name: Lint code
        run: uv run ruff check src/
```

### Test Commands

Add to project root for easy testing:

```bash
# Run all tests
uv run python -m pytest

# Run unit tests only  
uv run python -m pytest tests/unit/

# Run integration tests
uv run python -m pytest tests/integration/

# Run with coverage
uv run python -m pytest --cov=src/ --cov-report=html

# Run specific regression test
uv run python -m pytest -k "sqlite_compatibility"

# Type checking
uv run mypy src/

# Lint and format
uv run ruff check src/
uv run ruff format src/
```

## Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_candidates.py   # Database layer
│   ├── test_web_handlers.py # HTTP handlers
│   └── test_ocr_engines.py  # OCR functionality
├── integration/             # End-to-end tests
│   ├── test_web_review.py   # Full web interface
│   ├── test_cli_process.py  # CLI workflows
│   └── test_batch_processing.py
├── regression/              # Specific bug tests
│   ├── test_sqlalchemy_compatibility.py
│   └── test_s3_auth_issues.py
└── conftest.py             # Shared fixtures
```

## Database Testing Standards

### 1. Test Database Isolation
- Use temporary databases for each test
- Clean up database connections properly
- Avoid shared database state between tests

### 2. Multiple Interface Testing
When a component can be accessed via multiple interfaces (SQLAlchemy + sqlite3):
- Test both interfaces independently
- Test interface equivalence
- Document which interface is used where

### 3. Schema Migration Testing
- Test database creation from scratch
- Test migration from older schema versions
- Validate data integrity after migrations

## Monitoring and Alerting

### Test Metrics to Track
- Test coverage percentage
- Test execution time
- Test flakiness rate
- Regression test coverage

### When Tests Should Fail CI
- Any unit test failure
- Integration test failures on main branch
- Type checking errors
- Coverage below threshold (90%)
- Lint violations

## Best Practices

### 1. Test Naming
- Use descriptive names that explain the scenario
- Include "test_" prefix for pytest discovery
- Use "regression_" prefix for bug-specific tests

### 2. Test Documentation
- Include docstrings explaining the test purpose
- Document root cause for regression tests
- Link to relevant issues/PRs when applicable

### 3. Test Maintenance
- Review and update tests when functionality changes
- Remove obsolete tests that no longer apply
- Refactor duplicated test code into fixtures

### 4. Performance Testing
- Include performance benchmarks for critical paths
- Test with realistic data volumes
- Monitor test execution time trends

## Implementation Checklist

- [x] Add regression tests for SQLAlchemy compatibility
- [x] Create integration tests for web review interface
- [x] Add equivalence tests for dual interfaces
- [ ] Set up mypy type checking
- [ ] Configure pre-commit hooks
- [ ] Add GitHub Actions workflow
- [ ] Implement test coverage reporting
- [ ] Add performance benchmarks
- [ ] Document test commands in README