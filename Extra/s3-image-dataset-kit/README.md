
# S3 Image Dataset Kit (Immutable, Read-Only, Random Access)

A minimal, production-friendly toolkit for hosting ~3k read-only JPEGs in S3/S3‑compatible storage, with
content-addressed keys, a JSONL manifest, and a read‑through cache client for containers and task runners.

> Philosophy: **Don't bake images into Docker.** Put them in object storage, fetch on demand, cache locally.

## Features
- **Content-addressed uploads** (SHA256) with two-level prefix split: `images/ab/cd/<sha256>.jpg`
- **JSONL manifest** with bytes, content-type, optional width/height, optional logical IDs
- **Read-through cache client** for random access workloads
- Supports AWS S3 and S3‑compatible endpoints (MinIO, Cloudflare R2, DO Spaces, etc.)
- Clean **uv-managed** Python project; includes **Makefile** targets

## Quick Start

### 0) Requirements
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Python package/deps manager)
- An S3 or S3-compatible bucket
- (Optional) Docker, rclone

### 1) Configure environment
Copy and edit `.env.example` → `.env`.

```bash
cp .env.example .env
# edit with your bucket and creds
```

Or set environment variables directly (CI/CD, task runner).

### 2) Install deps (uv)
```bash
uv sync
```

### 3) Build manifest + upload images
Assuming your local images are under `./data/images`:

```bash
# Dry-run manifest (no uploads) – write to ./manifests/inventory-v1.jsonl
make manifest SRC_DIR=./data/images

# Upload to S3 (idempotent by hash)
make upload SRC_DIR=./data/images
```

### 4) Random fetch demo (read-through cache)
```bash
# Downloads to /tmp/imgcache by default, then prints local paths
make random-fetch N=5
```

### 5) Optional: mount as a filesystem (read-only)
```bash
# Configure rclone remote named "dataset"
rclone mount dataset:YOUR_BUCKET /mnt/dataset --read-only --vfs-cache-mode full
```

## Directory Layout
```
s3://YOUR_BUCKET/
  images/
    ab/cd/<sha256>.jpg
  manifests/
    inventory-v1.jsonl
```

### Manifest fields (JSONL per-line object)
```json
{
  "sha256": "abcdef...",
  "path": "images/ab/cd/abcdef....jpg",
  "bytes": 4283749,
  "content_type": "image/jpeg",
  "width": 4928,
  "height": 3264,
  "logical_id": "DAO-12345",
  "etag": "\"9a8b7c6d...\""
}
```

## Docker (client/demo)
You do **not** bake images into the container. This image only contains the client tool.

```bash
# Build
docker build -t dataset-client .

# Run demo (needs env for S3 + manifest access, and a cache volume)
docker run --rm -it   --env-file .env   -v /tmp/imgcache:/tmp/imgcache   dataset-client   python -m dataset_tool.scripts.random_fetch --n 3
```

## Make Targets
- `make setup` – uv sync
- `make manifest SRC_DIR=./data/images` – compute hashes, build manifest only
- `make upload SRC_DIR=./data/images` – upload images + manifest to S3
- `make validate` – validate manifest against JSON Schema
- `make random-fetch N=5` – sample random images via read-through cache

## Notes
- Width/height require Pillow; if not installed, they are omitted.
- Set `DATASET_LOGICAL_MAP` to a CSV mapping from filename → logical_id, if needed.

## Security
Use IAM roles in cloud; for local/dev, use presigned URLs or scoped access keys.
Bucket should allow `GetObject` to runner roles and restrict `PutObject` to uploader roles.

## License
MIT
