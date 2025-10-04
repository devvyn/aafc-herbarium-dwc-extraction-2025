# Storage Abstraction Architecture

**Version**: 1.0
**Status**: Implemented
**Last Updated**: 2025-10-04

## Overview

The storage abstraction layer decouples the core extraction pipeline from storage implementation details, enabling the software to work with images from multiple sources:

- **Local filesystem** - Traditional directory-based storage
- **AWS S3** - Cloud object storage
- **MinIO** - Self-hosted S3-compatible storage
- **HTTP/HTTPS** - Remote image fetching (planned)

### Key Benefits

1. **Storage Independence**: Core extraction logic doesn't know or care where images come from
2. **Transparent Caching**: Remote images automatically cached locally via decorator pattern
3. **Configuration-Driven**: Storage backend selected via TOML config, no code changes needed
4. **Performance**: Direct filesystem access when available, efficient streaming when not
5. **Future-Proof**: Easy to add new backends (Azure Blob, Google Cloud Storage, etc.)

## Architecture Pattern

The implementation follows the **Strategy Pattern** with **Decorator Pattern** for caching:

```
┌─────────────────────────────────────────┐
│        Core Extraction Logic            │
│  (operates on ImageLocator interface)   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       CachingImageLocator               │
│    (optional transparent caching)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         ImageLocator Backend             │
│  ┌────────────┬─────────────┬──────────┐ │
│  │   Local    │     S3      │  MinIO   │ │
│  └────────────┴─────────────┴──────────┘ │
└──────────────────────────────────────────┘
```

## Components

### ImageLocator Protocol (`src/io_utils/locator.py`)

Core interface defining storage operations:

```python
class ImageLocator(Protocol):
    def exists(self, identifier: str) -> bool:
        """Check if image exists"""

    def get_image(self, identifier: str) -> bytes:
        """Fetch image data"""

    def get_metadata(self, identifier: str) -> ImageMetadata:
        """Get image metadata (size, type, etc.)"""

    def list_images(self, prefix: Optional[str] = None) -> Iterator[str]:
        """List available images"""

    def get_local_path(self, identifier: str) -> Optional[Path]:
        """Get local path if available (optimization)"""
```

### Backend Implementations

#### LocalFilesystemLocator (`src/io_utils/locators/local.py`)

Simplest backend for traditional directory-based storage:

```python
locator = LocalFilesystemLocator(Path("/data/herbarium-images"))
image_data = locator.get_image("specimen_001.jpg")
# Reads from /data/herbarium-images/specimen_001.jpg
```

**Features**:
- Direct filesystem access (no caching needed)
- Recursive directory traversal
- Standard image extension filtering
- Fast metadata access via filesystem stats

#### S3ImageLocator (`src/io_utils/locators/s3.py`)

AWS S3 and S3-compatible storage backend:

```python
locator = S3ImageLocator(
    bucket="my-herbarium-bucket",
    prefix="specimens/batch1/",
    region="us-east-1"
)
image_data = locator.get_image("IMG_001.jpg")
# Fetches s3://my-herbarium-bucket/specimens/batch1/IMG_001.jpg
```

**Features**:
- Boto3-based S3 access
- Optional AWS credentials (uses default chain if omitted)
- Paginated listing for large buckets
- Works with MinIO via custom endpoint configuration

### CachingImageLocator Decorator (`src/io_utils/caching.py`)

Transparent pass-through caching wrapper:

```python
# Wrap any backend with caching
backend = S3ImageLocator(bucket="my-bucket")
cached = CachingImageLocator(
    backend,
    cache_dir=Path("/tmp/image-cache"),
    max_cache_size_mb=2000  # Optional size limit
)

# First access: cache miss, fetches from S3, saves to cache
data = cached.get_image("specimen_001.jpg")

# Second access: cache hit, returns from local filesystem (fast!)
data = cached.get_image("specimen_001.jpg")
```

**Features**:
- SHA256-based cache keys (handles special chars, long names)
- LRU eviction when cache size limit exceeded
- Cache statistics (`get_cache_stats()`)
- Manual cache management (`clear_cache()`)
- Transparent to caller - same ImageLocator interface

### Factory Function (`src/io_utils/locator_factory.py`)

Configuration-driven instantiation:

```python
from src.io_utils.locator_factory import create_image_locator

config = load_config(config_path)
locator = create_image_locator(config)
# Returns appropriate backend based on config
```

## Configuration

### Example: Local Filesystem (Default)

```toml
# No [storage] section needed - uses --input directory
```

### Example: S3 with Caching

```toml
[storage]
backend = "s3"
cache_enabled = true
cache_dir = "/tmp/herbarium-cache"
cache_max_size_mb = 2000

[storage.s3]
bucket = "my-herbarium-bucket"
prefix = "specimens/"
region = "us-east-1"
# AWS credentials optional (uses default chain)
```

### Example: MinIO

```toml
[storage]
backend = "minio"
cache_enabled = true
cache_dir = "/tmp/cache"

[storage.minio]
endpoint = "http://localhost:9000"
bucket = "herbarium"
access_key = "minioadmin"
secret_key = "minioadmin"
```

## Migration Guide

### Phase 1: Core Abstractions (Completed ✅)

- ✅ ImageLocator protocol defined
- ✅ LocalFilesystemLocator implemented
- ✅ S3ImageLocator implemented
- ✅ CachingImageLocator decorator implemented
- ✅ Factory function for config-based creation
- ✅ Configuration support in default TOML
- ✅ Comprehensive tests (18 passing)
- ✅ Example configs for S3 with caching

### Phase 2: CLI Integration (Future)

**Current State**: CLI works perfectly with local filesystem via existing `--input` directory.

**Future Enhancement**: Optionally use ImageLocator when `[storage]` configured:

```python
# In cli.py process_cli()
if "storage" in cfg:
    locator = create_image_locator(cfg)
    for identifier in iter_images_from_locator(locator):
        # Process using locator.get_image(identifier)
else:
    # Legacy path: use --input directory
    for img_path in iter_images(input_dir):
        # Process using path directly
```

**Benefits of Deferred Integration**:
- No breaking changes to existing workflows
- Architecture proven via tests and examples
- CLI migration can happen gradually
- Current local filesystem usage unaffected

### Phase 3: Advanced Features (Future)

Potential enhancements:

- **HTTP/HTTPS backend** for fetching images from web servers
- **Azure Blob Storage** backend
- **Google Cloud Storage** backend
- **Parallel download** for remote backends
- **Cache warming** - pre-download images before processing
- **Cache sharing** - multiple runs share same cache
- **Compression** - compress cached images to save disk space

## Usage Examples

### Basic Local Filesystem

```python
from src.io_utils.locators.local import LocalFilesystemLocator

locator = LocalFilesystemLocator(Path("/data/images"))
for identifier in locator.list_images():
    image_data = locator.get_image(identifier)
    # Process image_data...
```

### S3 with Automatic Caching

```python
from src.io_utils.locator_factory import create_image_locator

config = {
    "storage": {
        "backend": "s3",
        "cache_enabled": True,
        "cache_dir": "/tmp/cache",
        "s3": {
            "bucket": "my-bucket",
            "prefix": "images/"
        }
    }
}

locator = create_image_locator(config)
for identifier in locator.list_images():
    # First iteration: downloads from S3, caches locally
    # Subsequent iterations: reads from cache
    image_data = locator.get_image(identifier)
```

### Direct S3 Access (No Caching)

```python
from src.io_utils.locators.s3 import S3ImageLocator

locator = S3ImageLocator(
    bucket="my-bucket",
    prefix="specimens/"
)

# Always fetches from S3 (no caching)
image_data = locator.get_image("IMG_001.jpg")
```

### Custom Cache Management

```python
from src.io_utils.caching import CachingImageLocator

locator = CachingImageLocator(backend, cache_dir)

# Check cache statistics
stats = locator.get_cache_stats()
print(f"Cached files: {stats['num_files']}")
print(f"Cache size: {stats['total_size_mb']:.2f} MB")

# Clear cache if needed
locator.clear_cache()
```

## Performance Characteristics

### LocalFilesystemLocator

- **Listing**: O(n) directory traversal, filesystem speed
- **Fetch**: Direct file read, no overhead
- **Metadata**: Filesystem stat() call, very fast

### S3ImageLocator

- **Listing**: Paginated API calls, ~100ms per 1000 keys
- **Fetch**: Network latency + transfer time (~100-500ms per image)
- **Metadata**: HEAD request, ~50-100ms

### CachingImageLocator

- **Cache Hit**: Same as LocalFilesystemLocator (filesystem speed)
- **Cache Miss**: Backend speed + cache write overhead (~10-20ms)
- **Eviction**: O(n log n) for LRU sorting when limit exceeded

## Testing

Comprehensive test suite in `tests/unit/test_locators.py`:

```bash
# Run all storage abstraction tests
uv run pytest tests/unit/test_locators.py -v

# Test specific component
uv run pytest tests/unit/test_locators.py::TestCachingImageLocator -v
```

**Test Coverage**:
- ✅ LocalFilesystemLocator (11 tests)
- ✅ CachingImageLocator (7 tests)
- ✅ All edge cases (missing files, invalid paths, cache eviction)
- ⏳ S3ImageLocator (requires AWS credentials or moto mocking)

## Design Principles

1. **Protocol over ABC**: Use `Protocol` for duck typing, not abstract base classes
2. **Decorator Pattern**: Caching is a wrapper, not baked into backends
3. **Fail Fast**: Invalid config raises ValueError at startup, not during processing
4. **Lazy Import**: Backend dependencies (boto3) only imported when needed
5. **Explicit Over Implicit**: Configuration is explicit, no magic defaults

## Troubleshooting

### "Invalid or missing configuration"

```python
ValueError: Local backend requires 'base_path' in config or input_path argument
```

**Fix**: Provide either `storage.base_path` in config or `input_path` argument to factory.

### "S3 backend requires boto3"

```python
ImportError: S3 backend requires boto3: pip install boto3
```

**Fix**: Install boto3:
```bash
uv pip install boto3
```

### "Access denied to S3 object"

```python
PermissionError: Access denied to S3 object: specimen_001.jpg
```

**Fix**: Check AWS credentials and S3 bucket permissions.

### Cache eviction too aggressive

**Symptom**: Cache constantly evicting files even with `max_cache_size_mb=2000`.

**Fix**: Increase cache size limit or check disk space:
```bash
df -h /tmp  # Check available space
```

## References

- **Design Document**: `~/Desktop/20251004160850-0600-storage-abstraction-architecture.md`
- **Issue Discussion**: Storage abstraction requirements and architecture
- **Example Config**: `config/config.s3-cached.toml`
- **Tests**: `tests/unit/test_locators.py`

## Contributing

To add a new storage backend:

1. Create backend class implementing `ImageLocator` protocol
2. Add backend to `locator_factory.py` factory function
3. Update `config/config.default.toml` with backend configuration
4. Add tests to `tests/unit/test_locators.py`
5. Update this documentation

Example stub for HTTP backend:

```python
# src/io_utils/locators/http.py
class HTTPImageLocator:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def exists(self, identifier: str) -> bool:
        # HEAD request to check existence
        ...

    def get_image(self, identifier: str) -> bytes:
        # GET request to fetch image
        ...

    # ... implement remaining methods
```
