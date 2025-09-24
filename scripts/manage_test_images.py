#!/usr/bin/env python3
"""Manage test images for reproducible herbarium digitization workflows.

This script provides utilities for working with curated test images from S3,
enabling reproducible testing, documentation, and development workflows.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import urlretrieve

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        print("tomli not installed. Install with: pip install tomli")
        sys.exit(1)


class TestImageManager:
    """Manages test images for reproducible workflows."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/image_sources.toml")
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load image sources configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'rb') as f:
            return tomllib.load(f)

    def get_categories(self) -> List[str]:
        """Get available image categories."""
        test_images = self.config.get('test_images', {})
        return [key for key in test_images.keys() if isinstance(test_images[key], list)]

    def get_images_by_category(self, category: str) -> List[str]:
        """Get image URLs for a specific category."""
        test_images = self.config.get('test_images', {})
        return test_images.get(category, [])

    def get_sample_collection(self, collection_name: str) -> Dict:
        """Get configuration for a predefined sample collection."""
        collections = self.config.get('sample_collections', {})
        return collections.get(collection_name, {})

    def create_sample_bundle(self, collection_name: str, output_dir: Path, download: bool = False) -> Dict:
        """Create a sample bundle based on collection configuration."""
        collection = self.get_sample_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        categories = collection.get('categories', [])
        distribution = collection.get('distribution', [])

        if len(categories) != len(distribution):
            raise ValueError("Categories and distribution arrays must have the same length")

        bundle = {
            'collection': collection_name,
            'description': collection.get('description', ''),
            'total_count': sum(distribution),
            'categories': {},
            'files': []
        }

        output_dir.mkdir(parents=True, exist_ok=True)

        for category, count in zip(categories, distribution):
            # Map category names to config keys
            category_key = f"{category}_specimens" if not category.endswith('_specimens') else category

            available_images = self.get_images_by_category(category_key)
            if not available_images:
                print(f"Warning: No images available for category '{category_key}'")
                continue

            # Take the requested number of images (or all available if fewer)
            selected_images = available_images[:count]

            bundle['categories'][category] = {
                'count': len(selected_images),
                'images': selected_images
            }

            # Download images if requested
            if download:
                category_dir = output_dir / category
                category_dir.mkdir(exist_ok=True)

                for i, url in enumerate(selected_images):
                    try:
                        # Extract filename from URL or generate one
                        parsed = urlparse(url)
                        original_name = Path(parsed.path).name
                        if not original_name:
                            original_name = f"image_{i:03d}.jpg"

                        local_path = category_dir / original_name
                        print(f"Downloading {url} -> {local_path}")
                        urlretrieve(url, local_path)

                        bundle['files'].append({
                            'url': url,
                            'local_path': str(local_path.relative_to(output_dir)),
                            'category': category
                        })
                    except Exception as e:
                        print(f"Error downloading {url}: {e}")

        # Write bundle manifest
        manifest_path = output_dir / f"{collection_name}_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(bundle, f, indent=2)

        print(f"Created sample bundle: {output_dir}")
        print(f"Manifest: {manifest_path}")

        return bundle

    def validate_urls(self, category: Optional[str] = None) -> Dict[str, Dict]:
        """Validate that image URLs are accessible."""
        import urllib.request
        from urllib.error import URLError

        results = {}
        categories_to_check = [category] if category else self.get_categories()

        for cat in categories_to_check:
            images = self.get_images_by_category(cat)
            results[cat] = {
                'total': len(images),
                'accessible': 0,
                'errors': []
            }

            for url in images:
                try:
                    with urllib.request.urlopen(url) as response:
                        if response.status == 200:
                            results[cat]['accessible'] += 1
                        else:
                            results[cat]['errors'].append(f"{url}: HTTP {response.status}")
                except URLError as e:
                    results[cat]['errors'].append(f"{url}: {e}")

        return results

    def generate_documentation_urls(self, count_per_category: int = 3) -> Dict[str, List[str]]:
        """Generate a subset of URLs suitable for documentation examples."""
        doc_urls = {}

        for category in self.get_categories():
            images = self.get_images_by_category(category)
            doc_urls[category] = images[:count_per_category]

        return doc_urls

    def get_public_url_template(self) -> str:
        """Get the public URL template for generating new URLs."""
        public_config = self.config.get('public_access', {})
        bucket = self.config.get('sources', {}).get('primary_bucket', '')
        region = public_config.get('region', 'us-east-1')

        if not bucket:
            return ""

        return f"https://{bucket}.s3.{region}.amazonaws.com/{{}}"


def main():
    parser = argparse.ArgumentParser(description="Manage test images for herbarium digitization")
    parser.add_argument("--config", type=Path, help="Path to image sources config file")

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List categories command
    list_parser = subparsers.add_parser('list-categories', help='List available image categories')

    # List collections command
    collections_parser = subparsers.add_parser('list-collections', help='List available sample collections')

    # Create bundle command
    bundle_parser = subparsers.add_parser('create-bundle', help='Create a sample image bundle')
    bundle_parser.add_argument('collection', help='Collection name to create')
    bundle_parser.add_argument('--output', type=Path, required=True, help='Output directory for bundle')
    bundle_parser.add_argument('--download', action='store_true', help='Download images locally')

    # Validate URLs command
    validate_parser = subparsers.add_parser('validate-urls', help='Validate image URLs')
    validate_parser.add_argument('--category', help='Specific category to validate')

    # Generate docs command
    docs_parser = subparsers.add_parser('generate-doc-urls', help='Generate URLs for documentation')
    docs_parser.add_argument('--count', type=int, default=3, help='Number of URLs per category')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        manager = TestImageManager(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'python scripts/setup_s3_access.py --update-config' first")
        return 1

    if args.command == 'list-categories':
        categories = manager.get_categories()
        print("Available image categories:")
        for category in categories:
            images = manager.get_images_by_category(category)
            print(f"  {category}: {len(images)} images")

    elif args.command == 'list-collections':
        collections = manager.config.get('sample_collections', {})
        print("Available sample collections:")
        for name, config in collections.items():
            print(f"  {name}: {config.get('description', 'No description')}")
            print(f"    Count: {config.get('count', 'Unknown')}")
            print(f"    Categories: {', '.join(config.get('categories', []))}")

    elif args.command == 'create-bundle':
        try:
            bundle = manager.create_sample_bundle(args.collection, args.output, args.download)
            print(f"\n✅ Created bundle with {bundle['total_count']} images")
            for category, info in bundle['categories'].items():
                print(f"  {category}: {info['count']} images")
        except Exception as e:
            print(f"Error creating bundle: {e}")
            return 1

    elif args.command == 'validate-urls':
        print("Validating image URLs...")
        results = manager.validate_urls(args.category)

        for category, result in results.items():
            accessible = result['accessible']
            total = result['total']
            print(f"\n{category}: {accessible}/{total} accessible")

            if result['errors']:
                print("  Errors:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"    {error}")

    elif args.command == 'generate-doc-urls':
        doc_urls = manager.generate_documentation_urls(args.count)
        print("Documentation-ready URLs:")
        for category, urls in doc_urls.items():
            print(f"\n{category}:")
            for url in urls:
                print(f"  {url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())