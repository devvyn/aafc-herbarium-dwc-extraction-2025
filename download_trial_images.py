#!/usr/bin/env python3
"""Download trial images using AWS CLI since we have credentials."""

import subprocess
import sys
from pathlib import Path
import time

def download_with_aws_cli(s3_paths, output_dir):
    """Download images using AWS CLI."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for i, s3_path in enumerate(s3_paths):
        try:
            filename = f"specimen_{i+1:03d}.jpg"
            filepath = output_dir / filename

            print(f"📥 Downloading image {i+1}/{len(s3_paths)}...")

            result = subprocess.run([
                'aws', 's3', 'cp', s3_path, str(filepath)
            ], capture_output=True, text=True, check=True)

            downloaded.append(str(filepath))
            print(f"✅ Downloaded: {filename}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download {s3_path}: {e.stderr}")

    return downloaded

def main():
    # S3 paths to download
    s3_paths = [
        "s3://devvyn.aafc-srdc.herbarium/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg",
        "s3://devvyn.aafc-srdc.herbarium/images/00/21/002143863d4b7c143fbf210738ff3f6a01a0f0d421e93e2762e3ee3e4c5c3fdd.jpg",
        "s3://devvynmurphy.aafc-srdc.herbarium/images/00/2e/002e8642edeadc9390dc630b8bd0a0a656e6b2bf76894943df0032b4b3916ee4.jpg",
        "s3://devvyn.aafc-srdc.herbarium/images/00/32/0032c4e7a00e97fcaafa518ceaea0d91919131e12c77c727ad8fb90ef1d30267.jpg",
        "s3://devvyn.aafc-srdc.herbarium/images/00/42/0042a8ea8490719b559ed7ada1b424adfaffd3ef88cc4f99432d63d8c4984ebe.jpg"
    ]

    print("🚀 Downloading trial images using AWS CLI...")

    # Download images
    images_dir = Path("trial_images")
    downloaded = download_with_aws_cli(s3_paths, images_dir)

    if not downloaded:
        print("❌ No images downloaded")
        return 1

    print(f"\n✅ Downloaded {len(downloaded)} images to {images_dir}/")

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

        # Check results
        if (results_dir / "app.db").exists():
            print("\n🎉 SUCCESS! Trial data ready for review:")
            print(f"📊 Database: {results_dir}/app.db")
            print(f"🌐 Launch review: python review_web.py --db {results_dir}/candidates.db --images {images_dir}/")

            return 0
        else:
            print("⚠️ Processing completed but no database found")
            return 1

    except subprocess.CalledProcessError as e:
        processing_time = time.time() - start_time
        print(f"❌ Processing failed after {processing_time:.1f}s")
        print(f"Error: {e.stderr}")
        return 1

if __name__ == "__main__":
    sys.exit(main())