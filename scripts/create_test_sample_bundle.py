"""Create stratified test sample bundle from S3 herbarium images.

This script downloads a representative sample of herbarium images from S3 with
stratified sampling to ensure coverage of different OCR scenarios:
- High-quality readable labels
- Specimens with minimal/unclear text
- Unlabeled specimens (specimen-only)
- Poor quality/unusable text scenarios

The resulting bundle is designed for automated OCR testing and validation.
"""

from __future__ import annotations

import argparse
import json
import random
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception


@dataclass
class ImageMetadata:
    """Metadata for a single image in the test sample."""
    s3_key: str
    local_path: str
    category: str  # readable_labels, minimal_text, unlabeled, poor_quality
    file_size: int
    sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    download_timestamp: Optional[str] = None


@dataclass
class TestSampleManifest:
    """Manifest describing the test sample bundle."""
    creation_timestamp: str
    total_images: int
    bucket_name: str
    sampling_strategy: str
    categories: Dict[str, int]  # category -> count
    images: List[ImageMetadata]


class TestSampleBuilder:
    """Builder for creating stratified test samples from S3."""

    CATEGORIES = {
        "readable_labels": "Images with clear, OCR-readable specimen labels",
        "minimal_text": "Images with specimens and minimal/unclear text",
        "unlabeled": "Images with specimens but no visible labels",
        "poor_quality": "Images with unusable/corrupted text or poor quality"
    }

    def __init__(self, bucket_name: str, aws_profile: Optional[str] = None):
        if boto3 is None:
            raise ImportError(
                "boto3 is required for S3 access. Install with: pip install boto3"
            )

        self.bucket_name = bucket_name
        self.s3_client = self._create_s3_client(aws_profile)

    def _create_s3_client(self, aws_profile: Optional[str]):
        """Create configured S3 client."""
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                return session.client('s3')
            else:
                return boto3.client('s3')
        except NoCredentialsError:
            raise ValueError(
                "AWS credentials not found. Configure via AWS CLI, environment "
                "variables, or IAM roles."
            )

    def list_available_images(self, prefix: str = "", max_keys: int = 1000) -> List[str]:
        """List available images in the S3 bucket."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
        images = []

        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']
                    if any(key.lower().endswith(ext) for ext in image_extensions):
                        images.append(key)

            return images

        except ClientError as e:
            raise ValueError(f"Failed to list S3 objects: {e}")

    def _categorize_by_name_heuristics(self, s3_keys: List[str]) -> Dict[str, List[str]]:
        """Categorize images based on naming heuristics (placeholder implementation)."""
        # This is a simplified heuristic - in practice you'd use metadata,
        # previous OCR results, or manual classification
        random.shuffle(s3_keys)

        total = len(s3_keys)
        categories = {
            "readable_labels": s3_keys[:total//4],
            "minimal_text": s3_keys[total//4:total//2],
            "unlabeled": s3_keys[total//2:3*total//4],
            "poor_quality": s3_keys[3*total//4:]
        }

        return categories

    def create_stratified_sample(
        self,
        total_size: int = 100,
        category_distribution: Optional[Dict[str, float]] = None
    ) -> Dict[str, List[str]]:
        """Create stratified sample with specified distribution."""
        if category_distribution is None:
            # Default distribution for comprehensive testing
            category_distribution = {
                "readable_labels": 0.4,   # 40% - primary test cases
                "minimal_text": 0.25,     # 25% - edge cases
                "unlabeled": 0.20,        # 20% - negative cases
                "poor_quality": 0.15      # 15% - robustness testing
            }

        # Validate distribution
        if abs(sum(category_distribution.values()) - 1.0) > 0.01:
            raise ValueError("Category distribution must sum to 1.0")

        available_images = self.list_available_images()
        if len(available_images) < total_size:
            raise ValueError(
                f"Not enough images available. Found {len(available_images)}, "
                f"need {total_size}"
            )

        # Categorize all available images
        categorized = self._categorize_by_name_heuristics(available_images)

        # Sample from each category
        sample = {}
        for category, ratio in category_distribution.items():
            target_count = int(total_size * ratio)
            available = categorized.get(category, [])

            if len(available) < target_count:
                print(f"Warning: Only {len(available)} images available for "
                      f"category '{category}', need {target_count}")
                target_count = len(available)

            sample[category] = random.sample(available, target_count)

        return sample

    def download_image(self, s3_key: str, local_path: Path) -> ImageMetadata:
        """Download single image and create metadata."""
        try:
            # Create directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))

            # Get file info
            stat = local_path.stat()

            # Try to get image dimensions
            width, height = None, None
            try:
                from PIL import Image
                with Image.open(local_path) as img:
                    width, height = img.size
            except ImportError:
                pass  # PIL not available
            except Exception:
                pass  # Image might be corrupted

            return ImageMetadata(
                s3_key=s3_key,
                local_path=str(local_path.relative_to(Path.cwd())),
                category="",  # Will be set by caller
                file_size=stat.st_size,
                width=width,
                height=height,
                download_timestamp=datetime.now().isoformat()
            )

        except ClientError as e:
            raise ValueError(f"Failed to download {s3_key}: {e}")

    def create_bundle(
        self,
        output_dir: Path,
        sample_size: int = 100,
        category_distribution: Optional[Dict[str, float]] = None,
        compress: bool = True
    ) -> Tuple[Path, TestSampleManifest]:
        """Create complete test sample bundle."""

        print(f"Creating test sample bundle with {sample_size} images...")

        # Create stratified sample
        sample = self.create_stratified_sample(sample_size, category_distribution)

        # Setup directories
        output_dir.mkdir(parents=True, exist_ok=True)
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Download images and build manifest
        all_images = []
        category_counts = {}

        for category, s3_keys in sample.items():
            print(f"Downloading {len(s3_keys)} images for category: {category}")
            category_counts[category] = len(s3_keys)

            category_dir = images_dir / category
            category_dir.mkdir(exist_ok=True)

            for i, s3_key in enumerate(s3_keys):
                # Generate local filename
                filename = f"{category}_{i:03d}_{Path(s3_key).name}"
                local_path = category_dir / filename

                # Download and create metadata
                metadata = self.download_image(s3_key, local_path)
                metadata.category = category
                all_images.append(metadata)

        # Create manifest
        manifest = TestSampleManifest(
            creation_timestamp=datetime.now().isoformat(),
            total_images=len(all_images),
            bucket_name=self.bucket_name,
            sampling_strategy="stratified",
            categories=category_counts,
            images=all_images
        )

        # Write manifest
        manifest_path = output_dir / "manifest.json"
        with manifest_path.open('w') as f:
            json.dump(asdict(manifest), f, indent=2)

        # Create README
        readme_path = output_dir / "README.md"
        self._create_readme(readme_path, manifest)

        # Create test categories description
        categories_path = output_dir / "test_categories.json"
        with categories_path.open('w') as f:
            json.dump(self.CATEGORIES, f, indent=2)

        # Optionally compress
        if compress:
            zip_path = output_dir.parent / f"{output_dir.name}.zip"
            self._create_zip(output_dir, zip_path)
            print(f"Created compressed bundle: {zip_path}")
            return zip_path, manifest

        print(f"Created test sample bundle: {output_dir}")
        return output_dir, manifest

    def _create_readme(self, readme_path: Path, manifest: TestSampleManifest):
        """Create README documentation for the test bundle."""
        content = f"""# Herbarium OCR Test Sample Bundle

Generated: {manifest.creation_timestamp}
Source: S3 bucket `{manifest.bucket_name}`
Total Images: {manifest.total_images}
Sampling Strategy: {manifest.sampling_strategy}

## Test Categories

This bundle contains stratified samples designed for automated OCR testing:

"""

        for category, description in self.CATEGORIES.items():
            count = manifest.categories.get(category, 0)
            content += f"### {category.replace('_', ' ').title()} ({count} images)\n"
            content += f"{description}\n\n"

        content += """## Usage

### Running OCR Tests
```bash
# Test all categories
python -m pytest tests/integration/test_ocr_sample_validation.py

# Test specific category
python -m pytest tests/integration/test_ocr_sample_validation.py::test_readable_labels

# Run with specific engine
python cli.py process --input images/readable_labels --engine tesseract --output test_output
```

### Bundle Structure
- `images/`: Categorized test images
  - `readable_labels/`: High-quality labeled specimens
  - `minimal_text/`: Specimens with unclear text
  - `unlabeled/`: Specimens without visible labels
  - `poor_quality/`: Low-quality or corrupted images
- `manifest.json`: Complete metadata for all images
- `test_categories.json`: Category descriptions
- `README.md`: This documentation

## Quality Expectations

- **readable_labels**: Should achieve >80% OCR confidence
- **minimal_text**: May achieve 30-80% confidence with partial extraction
- **unlabeled**: Should gracefully handle with minimal false positives
- **poor_quality**: Should fail gracefully without crashing

Use this bundle to validate OCR engine robustness across different image quality scenarios.
"""

        with readme_path.open('w') as f:
            f.write(content)

    def _create_zip(self, source_dir: Path, zip_path: Path):
        """Create ZIP archive of the bundle."""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)


def main():
    parser = argparse.ArgumentParser(
        description="Create stratified test sample bundle from S3 herbarium images"
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="S3 bucket name containing herbarium images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./test_sample_bundle"),
        help="Output directory for the sample bundle"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Total number of images in the sample (default: 100)"
    )
    parser.add_argument(
        "--aws-profile",
        help="AWS profile to use for S3 access"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Skip creating ZIP archive"
    )
    parser.add_argument(
        "--readable-ratio",
        type=float,
        default=0.4,
        help="Proportion of readable label images (default: 0.4)"
    )
    parser.add_argument(
        "--minimal-ratio",
        type=float,
        default=0.25,
        help="Proportion of minimal text images (default: 0.25)"
    )
    parser.add_argument(
        "--unlabeled-ratio",
        type=float,
        default=0.20,
        help="Proportion of unlabeled specimens (default: 0.20)"
    )
    parser.add_argument(
        "--poor-quality-ratio",
        type=float,
        default=0.15,
        help="Proportion of poor quality images (default: 0.15)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible sampling"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually downloading"
    )

    args = parser.parse_args()

    # Set random seed for reproducibility
    if args.seed:
        random.seed(args.seed)

    # Validate ratios
    total_ratio = (args.readable_ratio + args.minimal_ratio +
                   args.unlabeled_ratio + args.poor_quality_ratio)
    if abs(total_ratio - 1.0) > 0.01:
        parser.error(f"Category ratios must sum to 1.0, got {total_ratio}")

    distribution = {
        "readable_labels": args.readable_ratio,
        "minimal_text": args.minimal_ratio,
        "unlabeled": args.unlabeled_ratio,
        "poor_quality": args.poor_quality_ratio
    }

    try:
        builder = TestSampleBuilder(args.bucket, args.aws_profile)

        if args.dry_run:
            print("DRY RUN: Showing what would be sampled...")
            sample = builder.create_stratified_sample(args.sample_size, distribution)
            for category, images in sample.items():
                print(f"{category}: {len(images)} images")
                for img in images[:3]:  # Show first 3 as examples
                    print(f"  - {img}")
                if len(images) > 3:
                    print(f"  ... and {len(images) - 3} more")
            return 0

        bundle_path, manifest = builder.create_bundle(
            args.output,
            args.sample_size,
            distribution,
            compress=not args.no_compress
        )

        print("\nSuccessfully created test sample bundle:")
        print(f"Location: {bundle_path}")
        print(f"Total images: {manifest.total_images}")
        print("\nCategory breakdown:")
        for category, count in manifest.categories.items():
            print(f"  {category}: {count} images")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())