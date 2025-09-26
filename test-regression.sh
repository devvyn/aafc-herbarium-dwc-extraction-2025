#!/bin/bash
# Regression test runner for database compatibility issues
# Run this script before committing changes to prevent SQLAlchemy compatibility issues

set -e

echo "🧪 Running Database Compatibility Regression Tests"
echo "=================================================="

echo "📊 Testing SQLAlchemy <-> sqlite3 compatibility..."
uv run python -m pytest \
  tests/unit/test_candidates.py::test_fetch_candidates_sqlite_compatibility \
  tests/unit/test_candidates.py::test_sqlalchemy_and_sqlite3_equivalence \
  -v

echo ""
echo "🌐 Testing web review database integration..."
uv run python -m pytest \
  tests/integration/test_web_review.py::test_web_review_database_compatibility \
  -v

echo ""
echo "🔍 Running all candidates module tests..."
uv run python -m pytest tests/unit/test_candidates.py -v

echo ""
echo "✅ All regression tests passed!"
echo ""
echo "🔧 Optional: Run full integration tests (slower):"
echo "   uv run python -m pytest tests/integration/test_web_review.py -v"
echo ""
echo "📝 Optional: Type checking (if mypy is available):"
echo "   uv run mypy io_utils/candidates.py review_web.py --ignore-missing-imports"
