# Multi-stage Dockerfile for AAFC Herbarium DWC Extraction
# Optimized for production deployment with OCR engines

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Install system dependencies for OCR engines
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR engine
    tesseract-ocr \
    tesseract-ocr-eng \
    # Image processing libraries (libgl1 replaced libgl1-mesa-glx in Debian 12+)
    libgl1 \
    libglib2.0-0 \
    # Build tools (needed for some Python packages)
    gcc \
    g++ \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Python dependencies
FROM base as dependencies

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies
# --no-dev excludes dev dependencies (tests, docs, linting)
RUN uv sync --frozen --no-dev

# Stage 3: Application runtime
FROM dependencies as runtime

# Copy application code
COPY cli.py ./
COPY config/ ./config/
COPY dwc/ ./dwc/
COPY engines/ ./engines/
COPY io_utils/ ./io_utils/
COPY preprocess/ ./preprocess/
COPY qc/ ./qc/
COPY src/ ./src/

# Create directories for data persistence
RUN mkdir -p /data/input /data/output /data/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Activate virtual environment created by uv
    PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv" \
    # Default to production mode
    ENV=production

# Health check - verify CLI is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python cli.py --version || exit 1

# Default command - show help
CMD ["python", "cli.py", "--help"]

# Stage 4: Development image (includes dev tools)
FROM dependencies as development

# Install dev dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Install pre-commit hooks
RUN pip install --no-cache-dir pre-commit && \
    git init && \
    pre-commit install || true

# Development uses interactive shell by default
CMD ["/bin/bash"]
