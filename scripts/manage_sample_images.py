#!/usr/bin/env python3
"""Manage reliable sample images for consistent testing and validation.

This script provides versioned sets of sample images for:
- OCR engine validation
- Regression testing
- Documentation examples
- Reproducible research
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict
import requests
import tomllib
from urllib.parse import urlparse

def load_image_config() -> Dict:
    """Load image sources configuration."""
    config_path = Path(__file__).parent.parent / "config" / "image_sources.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"Image sources config not found: {config_path}")

    with open(config_path, 'rb') as f:
        return tomllib.load(f)

def validate_image_url(url: str) -> bool:
    """Check if image URL is accessible."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_image(url: str, output_path: Path) -> bool:
    """Download image from URL to local path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        return True
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False

def create_test_bundle(collection_name: str, output_dir: Path, config: Dict) -> Dict:
    """Create a test bundle with specified collection."""

    if collection_name not in config.get('sample_collections', {}):
        raise ValueError(f"Unknown collection: {collection_name}")

    collection = config['sample_collections'][collection_name]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_info = {
        'collection': collection_name,
        'description': collection['description'],
        'created_at': '2025-09-25',  # Current date
        'images': [],
        'categories': {}
    }

    # Get images from each category based on distribution
    categories = collection['categories']
    distribution = collection['distribution']

    total_downloaded = 0

    for i, category in enumerate(categories):
        target_count = distribution[i] if i < len(distribution) else 0
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)

        # Get URLs for this category
        if category == 'readable':
            urls = config['test_images'].get('readable_specimens', [])
        elif category == 'minimal':
            urls = config['test_images'].get('minimal_text_specimens', [])
        elif category == 'unlabeled':
            urls = config['test_images'].get('unlabeled_specimens', [])
        elif category == 'poor':
            urls = config['test_images'].get('poor_quality_specimens', [])
        elif category == 'multilingual':
            urls = config['test_images'].get('multilingual_specimens', [])
        else:
            urls = []

        downloaded_in_category = 0
        bundle_info['categories'][category] = []

        print(f"📁 Processing {category} category (target: {target_count} images)")

        for url in urls[:target_count]:  # Limit to target count
            if not url or url.startswith('#'):  # Skip comments/empty
                continue

            # Generate filename from URL
            parsed = urlparse(url)
            filename = Path(parsed.path).name or f"{category}_{downloaded_in_category:03d}.jpg"

            output_path = category_dir / filename

            print(f"  📥 Downloading {filename}...")
            if download_image(url, output_path):
                bundle_info['images'].append({
                    'filename': str(output_path.relative_to(output_dir)),
                    'category': category,
                    'source_url': url,
                    'size_bytes': output_path.stat().st_size
                })
                bundle_info['categories'][category].append(filename)
                downloaded_in_category += 1
                total_downloaded += 1
            else:
                print(f"  ❌ Failed to download {filename}")

    # Save bundle metadata
    manifest_path = output_dir / "bundle_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(bundle_info, f, indent=2)

    print(f"\n✅ Created {collection_name} bundle with {total_downloaded} images")
    print(f"📄 Bundle manifest: {manifest_path}")

    return bundle_info

def validate_sample_urls(config: Dict) -> Dict:
    """Validate all sample image URLs are accessible."""

    results = {
        'accessible': [],
        'broken': [],
        'total_checked': 0
    }

    # Check all URL categories
    url_categories = config.get('test_images', {})

    for category, urls in url_categories.items():
        if not isinstance(urls, list):
            continue

        print(f"\n🔍 Checking {category} URLs...")

        for url in urls:
            if not url or url.startswith('#'):
                continue

            results['total_checked'] += 1
            print(f"  Testing {url}...", end=' ')

            if validate_image_url(url):
                print("✅")
                results['accessible'].append(url)
            else:
                print("❌")
                results['broken'].append(url)

    return results

def list_available_collections(config: Dict):
    """List all available sample collections."""

    print("📋 Available Sample Collections:")
    print("=" * 40)

    collections = config.get('sample_collections', {})

    for name, info in collections.items():
        print(f"\n🗂️  {name}")
        print(f"   Description: {info['description']}")
        print(f"   Total images: {info['count']}")
        print(f"   Categories: {', '.join(info['categories'])}")
        if 'distribution' in info:
            print(f"   Distribution: {info['distribution']}")

def main():
    parser = argparse.ArgumentParser(
        description="Manage reliable sample images for herbarium OCR testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available collections
  python manage_sample_images.py list

  # Create demo bundle for quick testing
  python manage_sample_images.py create-bundle demo --output ./test_images/demo

  # Create validation bundle for comprehensive testing
  python manage_sample_images.py create-bundle validation --output ./test_images/validation

  # Validate all URLs are accessible
  python manage_sample_images.py validate-urls
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List collections
    list_parser = subparsers.add_parser('list', help='List available sample collections')

    # Create bundle
    create_parser = subparsers.add_parser('create-bundle', help='Create test image bundle')
    create_parser.add_argument('collection', help='Collection name (demo, validation, benchmark)')
    create_parser.add_argument('--output', type=Path, required=True, help='Output directory')

    # Validate URLs
    validate_parser = subparsers.add_parser('validate-urls', help='Validate all sample URLs')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        config = load_image_config()

        if args.command == 'list':
            list_available_collections(config)

        elif args.command == 'create-bundle':
            bundle_info = create_test_bundle(args.collection, args.output, config)
            print("\n🎯 Bundle ready for testing:")
            print(f"   Path: {args.output}")
            print(f"   Images: {len(bundle_info['images'])}")
            print(f"   Categories: {list(bundle_info['categories'].keys())}")

        elif args.command == 'validate-urls':
            print("🔗 Validating sample image URLs...")
            results = validate_sample_urls(config)

            print("\n📊 Validation Results:")
            print(f"   Total URLs checked: {results['total_checked']}")
            print(f"   ✅ Accessible: {len(results['accessible'])}")
            print(f"   ❌ Broken: {len(results['broken'])}")

            if results['broken']:
                print("\n⚠️  Broken URLs:")
                for url in results['broken']:
                    print(f"     {url}")
                return 1
            else:
                print("\n🎉 All URLs are accessible!")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())