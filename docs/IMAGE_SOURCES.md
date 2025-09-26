# Image Source Configuration

## Overview

The herbarium OCR system now supports configurable image sources, allowing you to seamlessly switch between S3 buckets and local filesystem storage using SHA256 hashes as the key. This makes it straightforward to work with images regardless of where they're stored.

## Key Concepts

### SHA256-Based Organization

Images are organized using their SHA256 hash in a hierarchical directory structure:
- **S3**: `s3://bucket/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg`
- **Local**: `./images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg`

The first 2 characters (`00`) and next 2 characters (`0e`) of the hash form the directory structure, with the full hash as the filename.

### Interchangeable Sources

The same image can be accessed from different sources using its SHA256 hash:

```python
from io_utils.image_source import ImageSourceConfig

# S3 source
s3_source = ImageSourceConfig.from_config({
    'type': 's3',
    'bucket': 'devvyn.aafc-srdc.herbarium',
    'region': 'ca-central-1'
})

# Local source  
local_source = ImageSourceConfig.from_config({
    'type': 'local',
    'base_path': './image_cache'
})

# Both access the same image via hash
hash_value = "000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84"
s3_path = s3_source.get_image_path(hash_value)
local_path = local_source.get_image_path(hash_value)
```

## Configuration Types

### S3 Source

Access images directly from an S3 bucket:

```toml
[source]
type = "s3"
bucket = "devvyn.aafc-srdc.herbarium"
region = "ca-central-1"
prefix = "images"  # Optional, defaults to "images"
```

### Local Source

Access images from local filesystem:

```toml
[source]
type = "local"
base_path = "./local_images"
```

### Multi-Source

Try multiple sources in priority order (local cache first, S3 fallback):

```toml
[source]
type = "multi"

[[source.sources]]
type = "local"
base_path = "./image_cache"

[[source.sources]]
type = "s3"  
bucket = "devvyn.aafc-srdc.herbarium"
region = "ca-central-1"
prefix = "images"
```

## Usage Examples

### Basic Usage

```python
from io_utils.image_source import ImageSourceConfig, DEFAULT_S3_CONFIG
from pathlib import Path

# Use default S3 configuration
source = ImageSourceConfig.from_config(DEFAULT_S3_CONFIG)

# Check if image exists
hash_value = "000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84"
if source.exists(hash_value):
    print("Image exists!")

# Get image URL/path
image_path = source.get_image_path(hash_value)
print(f"Image available at: {image_path}")

# Download to local file
local_path = Path("./downloaded_image.jpg")
success = source.download_image(hash_value, local_path)
if success:
    print(f"Downloaded to {local_path}")
```

### Development Workflow

Create a local cache to avoid repeated S3 downloads:

```python
# Development configuration with local-first approach
dev_config = {
    'type': 'multi',
    'sources': [
        {'type': 'local', 'base_path': './dev_cache'},
        {'type': 's3', 'bucket': 'devvyn.aafc-srdc.herbarium', 'region': 'ca-central-1'}
    ]
}

source = ImageSourceConfig.from_config(dev_config)

# First call downloads from S3 to local cache
# Subsequent calls use local cache
for hash_value in image_hashes:
    local_path = Path(f"./processing/{hash_value}.jpg")
    source.download_image(hash_value, local_path)
```

### Production Setup

Use local cache with S3 backup:

```python
production_config = {
    'type': 'multi',
    'sources': [
        {'type': 'local', 'base_path': '/opt/herbarium/images'},
        {'type': 's3', 'bucket': 'devvyn.aafc-srdc.herbarium', 'region': 'ca-central-1'}
    ]
}
```

## Integration with Existing Tools

### Quick Trial Run

The `quick_trial_run.py` script now uses the configurable image source system:

```bash
# Uses default S3 configuration
python quick_trial_run.py

# To use a different configuration, modify the script or create a custom version
```

### Custom Processing Scripts

```python
from io_utils.image_source import ImageSourceConfig
from quick_trial_run import download_images_with_source

# Custom configuration
custom_config = {
    'type': 'local',
    'base_path': '/shared/herbarium_images'
}

source = ImageSourceConfig.from_config(custom_config)

# Use with existing download function
urls = ["https://s3.../images/00/0e/000e426d...84.jpg"]
download_images_with_source(urls, "./output", source)
```

## Configuration Files

### Example Configurations

See `config/image_source_examples.toml` for complete examples:

- **s3_only**: Direct S3 access
- **local_only**: Local filesystem only  
- **local_first**: Local cache with S3 fallback
- **development**: Multi-tier development setup
- **production**: Production-ready configuration
- **testing**: Test environment setup

### Loading from File

```python
import toml
from io_utils.image_source import ImageSourceConfig

# Load configuration from file
config = toml.load("config/image_source_examples.toml")
source = ImageSourceConfig.from_config(config['development'])
```

## Performance Considerations

### Local Cache Benefits

- **Speed**: Local access is significantly faster than S3 downloads
- **Cost**: Reduces S3 API calls and data transfer costs
- **Reliability**: Works offline once images are cached

### Multi-Source Strategy

- **Development**: Local first, S3 fallback for missing images
- **Production**: Local cache with S3 backup
- **Testing**: Local test images to avoid external dependencies

### Cache Management

```python
# Check cache size
import os
from pathlib import Path

cache_path = Path("./image_cache")
if cache_path.exists():
    total_size = sum(f.stat().st_size for f in cache_path.rglob("*.jpg"))
    print(f"Cache size: {total_size / (1024*1024):.1f} MB")

# Clear cache if needed
import shutil
shutil.rmtree(cache_path, ignore_errors=True)
```

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS CLI is configured for S3 access
   ```bash
   aws configure
   # or set environment variables:
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

2. **Permission Denied**: Check filesystem permissions for local paths
   ```bash
   mkdir -p ./image_cache
   chmod 755 ./image_cache
   ```

3. **Hash Extraction**: Verify URL format for SHA256 extraction
   ```python
   # Valid format:
   "https://s3.ca-central-1.amazonaws.com/.../000e426d...84.jpg"
   ```

### Testing Configuration

Use the test script to verify your configuration:

```bash
python test_image_source.py
```

This tests:
- SHA256 extraction from URLs
- S3 source functionality  
- Local source functionality
- Multi-source fallback behavior

## API Reference

### ImageSource Classes

- `S3ImageSource`: S3 bucket access
- `LocalImageSource`: Local filesystem access  
- `MultiImageSource`: Multiple sources with fallback
- `ImageSourceConfig`: Configuration factory

### Key Methods

- `get_image_path(sha256_hash)`: Get path/URL for image
- `download_image(sha256_hash, local_path)`: Download to local file
- `exists(sha256_hash)`: Check if image exists
- `ImageSourceConfig.from_config(config_dict)`: Create from configuration

### Utility Functions

- `calculate_sha256(file_path)`: Calculate hash of local file
- `extract_sha256_from_url(url)`: Extract hash from S3 URL

## Migration Guide

### From Direct S3 URLs

Old approach:
```python
# Direct URL handling
url = "https://s3.../images/00/0e/000e426d...84.jpg"
subprocess.run(['aws', 's3', 'cp', s3_path, local_path])
```

New approach:
```python
# Hash-based access
from quick_trial_run import extract_sha256_from_url
from io_utils.image_source import ImageSourceConfig, DEFAULT_S3_CONFIG

hash_value = extract_sha256_from_url(url)
source = ImageSourceConfig.from_config(DEFAULT_S3_CONFIG)
source.download_image(hash_value, local_path)
```

### Benefits of Migration

1. **Flexibility**: Easy switching between S3 and local storage
2. **Performance**: Automatic caching and fallback
3. **Testing**: Use local test images without S3 dependency
4. **Development**: Local-first workflow with S3 backup
5. **Consistency**: Unified interface regardless of storage backend