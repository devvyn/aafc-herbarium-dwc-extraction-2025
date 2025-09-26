#!/usr/bin/env python3
"""Quick trial run for stakeholder review testing."""

from pathlib import Path
import subprocess
import time
import sys
import re
from io_utils.image_source import ImageSourceConfig, DEFAULT_S3_CONFIG

def extract_sha256_from_url(url: str) -> str:
    """Extract SHA256 hash from S3 URL."""
    # Extract from URLs like: .../images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg
    match = re.search(r'/([0-9a-f]{64})\.jpg$', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract SHA256 from URL: {url}")

def download_images_with_source(urls, output_dir, image_source=None):
    """Download images using configurable image source."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if image_source is None:
        image_source = ImageSourceConfig.from_config(DEFAULT_S3_CONFIG)

    downloaded = []
    for i, url in enumerate(urls):
        try:
            print(f"📥 Downloading image {i+1}/{len(urls)}...")
            filename = f"specimen_{i+1:03d}.jpg"
            filepath = output_dir / filename

            # Extract SHA256 from URL and use image source
            sha256_hash = extract_sha256_from_url(url)
            success = image_source.download_image(sha256_hash, filepath)

            if success:
                downloaded.append(str(filepath))
                print(f"✅ Downloaded: {filename}")
            else:
                print(f"❌ Failed to download {url}")

        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

    return downloaded

# Legacy function for backward compatibility
def download_s3_images(urls, output_dir):
    """Download images from S3 URLs (legacy interface)."""
    return download_images_with_source(urls, output_dir)

def main():
    # Get URLs from config file
    import toml

    config_path = Path("config/image_sources.toml")
    if not config_path.exists():
        print("❌ Config file not found")
        return 1

    config = toml.load(config_path)

    # Collect URLs from different categories
    urls = []
    for category in ['readable_specimens', 'minimal_specimens', 'poor_specimens']:
        if category in config.get('test_images', {}):
            urls.extend(config['test_images'][category][:5])  # 5 from each category

    print(f"🚀 Quick Trial Run - Processing {len(urls)} specimens")
    print("📁 This will create trial_images/ and trial_results/")

    # Download images
    images_dir = Path("trial_images")
    print(f"\n📥 Downloading {len(urls)} images...")
    downloaded = download_s3_images(urls, images_dir)

    if not downloaded:
        print("❌ No images downloaded")
        return 1

    print(f"✅ Downloaded {len(downloaded)} images")

    # Process with Apple Vision
    results_dir = Path("trial_results")
    print("\n🔄 Processing with Apple Vision OCR...")

    start_time = time.time()

    try:
        result = subprocess.run([
            'python', 'cli.py', 'process',
            '--input', str(images_dir),
            '--output', str(results_dir),
            '--engine', 'vision'
        ], capture_output=True, text=True, check=True)

        processing_time = time.time() - start_time
        print(f"✅ Processing completed in {processing_time:.1f}s")

    except subprocess.CalledProcessError as e:
        print(f"❌ Processing failed: {e.stderr}")
        return 1

    # Check results
    if (results_dir / "app.db").exists():
        print(f"✅ Database created: {results_dir / 'app.db'}")

        # Launch review interface
        print("\n🌐 Ready to launch review interface:")
        print(f"python review_web.py --db {results_dir}/candidates.db --images {images_dir}/")
        print("\nOr check processing with:")
        print(f"python -c \"import sqlite3; conn=sqlite3.connect('{results_dir}/app.db'); print('Specimens:', conn.execute('SELECT COUNT(*) FROM specimens').fetchone()[0])\"")

        return 0
    else:
        print("❌ No database created - check processing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
