# Docker Deployment Guide

Containerized deployment for the AAFC Herbarium DWC Extraction toolkit.

## Quick Start

### Build the Image

```bash
docker build --target runtime -t herbarium-dwc:latest .
```

**Build time:** ~2-3 minutes (first build)
**Image size:** ~1.8GB (includes Tesseract OCR + Python dependencies)

### Run Processing

```bash
# Process specimen images
docker run --rm \
  -v $(pwd)/data/input:/data/input:ro \
  -v $(pwd)/data/output:/data/output \
  herbarium-dwc:latest \
  python cli.py process --input /data/input --output /data/output
```

### Using Docker Compose

```bash
# Copy environment template
cp .env.docker.example .env
# Edit .env with your API keys (if using cloud OCR)

# Start processing service
docker compose up herbarium

# Start review web interface
docker compose --profile review up review-web
# Access at http://localhost:5000

# Start development environment
docker compose --profile dev up -d herbarium-dev
docker compose exec herbarium-dev bash
```

## Image Variants

### Production Runtime (`runtime` stage - default)
```bash
docker build --target runtime -t herbarium-dwc:latest .
```
- **Size:** ~1.8GB
- **Includes:** Tesseract OCR, Python app, production dependencies
- **Use for:** Production processing, batch jobs, cloud deployment

### Development (`development` stage)
```bash
docker build --target development -t herbarium-dwc:dev .
```
- **Size:** ~2.1GB
- **Includes:** Runtime + dev tools (pytest, ruff, pre-commit)
- **Use for:** Local development, testing, debugging

## OCR Engine Support

### Tesseract (Built-in)
✅ Available in all images (FREE, no API keys required)

```bash
docker run --rm herbarium-dwc:latest tesseract --version
# Output: tesseract 5.5.0
```

### Cloud APIs (Requires API Keys)
Configure via `.env` file:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

Mount `.env` at runtime:
```bash
docker run --rm --env-file .env \
  -v $(pwd)/data:/data \
  herbarium-dwc:latest \
  python cli.py process --input /data/input --engine gpt-4o-mini
```

## Volume Mounts

### Required Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data/input` | `/data/input` | Specimen images (read-only recommended) |
| `./data/output` | `/data/output` | Extraction results (read-write) |

### Optional Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data/cache` | `/data/cache` | OCR cache for faster re-processing |
| `./config` | `/app/config` | Custom configuration overrides |

### Example

```bash
docker run --rm \
  -v $(pwd)/specimens:/data/input:ro \
  -v $(pwd)/results:/data/output \
  -v $(pwd)/cache:/data/cache \
  --env-file .env \
  herbarium-dwc:latest \
  python cli.py process \
    --input /data/input \
    --output /data/output \
    --engine tesseract
```

## Services

### 1. Processing Service

```bash
docker compose up herbarium
```

Runs batch processing on `/data/input`.

**Configuration (via .env):**
```bash
OCR_ENGINE=tesseract  # or gpt-4o-mini, azure-vision
BATCH_SIZE=10
WORKERS=4
LOG_LEVEL=INFO
```

### 2. Review Web Interface

```bash
docker compose --profile review up review-web
```

**Access:** http://localhost:5000
**Purpose:** Quality review and validation

### 3. Batch Monitor

```bash
docker compose --profile monitor up monitor
```

**Access:** http://localhost:5002
**Purpose:** Real-time processing status

### 4. Development Shell

```bash
docker compose --profile dev up -d herbarium-dev
docker compose exec herbarium-dev bash
```

**Features:**
- Live code mounting (changes reflected immediately)
- Full dev toolchain (pytest, ruff, pre-commit)
- Persistent Python cache

## Multi-Stage Build Architecture

```
┌─────────────────────────────────────────┐
│ Stage 1: base                           │
│ - Python 3.11-slim (Debian)             │
│ - Tesseract OCR 5.5.0                   │
│ - System libraries (libgl1, gcc, g++)   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Stage 2: dependencies                   │
│ - uv package manager                    │
│ - Python dependencies (91 packages)     │
│ - Virtual environment (.venv)           │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐  ┌───────▼────────┐
│ runtime    │  │ development    │
│ (1.8GB)    │  │ (2.1GB)        │
│ Production │  │ Dev + Testing  │
└────────────┘  └────────────────┘
```

## Performance

### Build Performance
- **First build:** 2-3 minutes (pulls base image, installs packages)
- **Incremental builds:** 10-30 seconds (layer caching)
- **Build context:** ~50MB (2GB excluded via .dockerignore)

### Runtime Performance
- **Startup time:** <5 seconds
- **Processing:** Same as native (Tesseract 5.5.0)
- **Memory:** ~500MB base + OCR overhead

## Cloud Deployment

### AWS ECS/Fargate

```bash
# Build for ARM64 (AWS Graviton)
docker build --platform linux/arm64 -t herbarium-dwc:latest .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag herbarium-dwc:latest <account>.dkr.ecr.<region>.amazonaws.com/herbarium-dwc:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/herbarium-dwc:latest
```

**Task Definition:**
- **CPU:** 2 vCPU (minimum)
- **Memory:** 4GB (recommended for large batches)
- **Storage:** 20GB+ ephemeral (for image cache)

### Google Cloud Run

```bash
# Build and push
docker build -t gcr.io/<project>/herbarium-dwc:latest .
docker push gcr.io/<project>/herbarium-dwc:latest

# Deploy
gcloud run deploy herbarium-dwc \
  --image gcr.io/<project>/herbarium-dwc:latest \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600
```

## Troubleshooting

### ModuleNotFoundError

**Symptom:** `ModuleNotFoundError: No module named 'sqlalchemy'`

**Cause:** Virtual environment not activated

**Fix:** Rebuild with latest Dockerfile (includes PATH fix)

```bash
docker build --target runtime -t herbarium-dwc:latest . --no-cache
```

### Permission Denied on Volumes

**Symptom:** Cannot write to `/data/output`

**Fix:** Use named volumes or fix host permissions

```bash
# Option 1: Named volume
docker volume create herbarium-output
docker run -v herbarium-output:/data/output ...

# Option 2: Fix host permissions
chmod -R 777 ./data/output
```

### Build Fails: libgl1-mesa-glx not found

**Cause:** Old Dockerfile for outdated Debian

**Fix:** Use `libgl1` instead (already fixed in current Dockerfile)

## Security

### Secrets Management

**❌ Never include in image:**
```dockerfile
# BAD - secrets baked into image
ENV OPENAI_API_KEY=sk-...
```

**✅ Use environment files:**
```bash
# GOOD - secrets at runtime only
docker run --env-file .env ...
```

### Read-Only Mounts

Protect source images:
```bash
docker run -v $(pwd)/images:/data/input:ro ...
                                          ^^^^
                                      read-only
```

## Development Workflow

```bash
# 1. Start dev environment
docker compose --profile dev up -d herbarium-dev

# 2. Enter container
docker compose exec herbarium-dev bash

# 3. Inside container - make changes to mounted code
cd /app
vim src/extraction_monitor/api.py

# 4. Run tests
pytest tests/

# 5. Lint code
ruff check . --fix

# 6. Exit and rebuild for production
exit
docker build --target runtime -t herbarium-dwc:latest .
```

## Health Checks

Built-in health check verifies CLI accessibility:

```bash
docker inspect herbarium-dwc:latest | grep -A 5 Healthcheck
```

**Check manually:**
```bash
docker run --rm herbarium-dwc:latest python cli.py --version
```

## Next Steps

- **Production deployment:** See cloud deployment sections above
- **Custom configuration:** Mount custom `config/` directory
- **API integration:** Use FastAPI service (port 8000)
- **Batch processing:** See `scripts/batch_*.py` examples

## Related Documentation

- [Main README](README.md) - Project overview
- [API Setup Guide](API_SETUP_QUICK.md) - Cloud API configuration
- [Contributing](CONTRIBUTING.md) - Development guidelines
