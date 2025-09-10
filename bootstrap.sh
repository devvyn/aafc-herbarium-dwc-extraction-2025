#!/usr/bin/env bash
set -euo pipefail

# Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# Install base and development dependencies using uv
uv sync --dev

# Copy environment example if no .env exists
if [ ! -f .env ]; then
  cp .env.example .env
fi

# Run linting and tests to verify setup
uv run ruff check . --fix
uv run pytest -q
