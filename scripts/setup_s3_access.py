#!/usr/bin/env python3
"""Setup S3 access for reproducible herbarium image referencing.

This script helps configure S3 access for the herbarium digitization toolkit,
enabling reproducible image references for testing, documentation, and development.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        print("tomli not installed. Install with: pip install tomli")
        sys.exit(1)


def check_aws_credentials() -> bool:
    """Check if AWS credentials are properly configured."""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        return credentials is not None
    except NoCredentialsError:
        return False


def list_s3_buckets() -> List[str]:
    """List available S3 buckets."""
    try:
        s3_client = boto3.client("s3")
        response = s3_client.list_buckets()
        return [bucket["Name"] for bucket in response["Buckets"]]
    except ClientError as e:
        print(f"Error listing buckets: {e}")
        return []


def explore_bucket_contents(bucket_name: str, prefix: str = "", max_keys: int = 100) -> List[Dict]:
    """Explore contents of an S3 bucket with optional prefix filter."""
    try:
        s3_client = boto3.client("s3")
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=max_keys)

        objects = []
        if "Contents" in response:
            for obj in response["Contents"]:
                objects.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                        "etag": obj["ETag"].strip('"'),
                    }
                )

        return objects
    except ClientError as e:
        print(f"Error exploring bucket {bucket_name}: {e}")
        return []


def generate_public_urls(bucket_name: str, keys: List[str], region: str = "us-east-1") -> List[str]:
    """Generate public HTTPS URLs for S3 objects."""
    urls = []
    for key in keys:
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
        urls.append(url)
    return urls


def categorize_images(objects: List[Dict]) -> Dict[str, List[str]]:
    """Categorize images based on filename patterns (basic heuristic)."""
    categories = {
        "readable_specimens": [],
        "minimal_text_specimens": [],
        "unlabeled_specimens": [],
        "poor_quality_specimens": [],
        "multilingual_specimens": [],
    }

    # Basic categorization heuristics - can be refined based on actual naming patterns
    for obj in objects:
        key = obj["key"].lower()

        # Skip non-image files
        if not any(key.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]):
            continue

        # Simple heuristics - these would need refinement based on actual data
        if "clear" in key or "readable" in key or "good" in key:
            categories["readable_specimens"].append(obj["key"])
        elif "minimal" in key or "basic" in key:
            categories["minimal_text_specimens"].append(obj["key"])
        elif "unlabeled" in key or "specimen" in key:
            categories["unlabeled_specimens"].append(obj["key"])
        elif "poor" in key or "damaged" in key or "blurry" in key:
            categories["poor_quality_specimens"].append(obj["key"])
        elif any(lang in key for lang in ["french", "german", "spanish", "latin"]):
            categories["multilingual_specimens"].append(obj["key"])
        else:
            # Default to readable specimens for uncategorized images
            categories["readable_specimens"].append(obj["key"])

    return categories


def update_image_sources_config(
    bucket_name: str, region: str, categories: Dict[str, List[str]]
) -> None:
    """Update the image sources configuration with discovered S3 content."""
    config_path = Path("config/image_sources.toml")

    if not config_path.exists():
        print(f"Configuration file {config_path} not found")
        return

    # Read existing config
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Generate URLs for each category (taking first 10 items as examples)
    updated_config = []

    # Update sources section
    updated_config.append("[sources]")
    updated_config.append(f'primary_bucket = "{bucket_name}"')
    updated_config.append(f'public_base_url = "https://{bucket_name}.s3.{region}.amazonaws.com"')
    updated_config.append(f'region = "{region}"')
    updated_config.append("")

    # Update test images section
    updated_config.append("[test_images]")
    for category, keys in categories.items():
        if keys:
            updated_config.append(f'# {category.replace("_", " ").title()}')
            updated_config.append(f"{category} = [")
            for key in keys[:5]:  # Take first 5 as examples
                url = f'    "https://{bucket_name}.s3.{region}.amazonaws.com/{key}",'
                updated_config.append(url)
            if len(keys) > 5:
                updated_config.append(f"    # ... and {len(keys) - 5} more images")
            updated_config.append("]")
            updated_config.append("")

    # Add public access section
    updated_config.append("[public_access]")
    updated_config.append("enable_public_urls = true")
    updated_config.append(f'region = "{region}"')
    updated_config.append("")

    # Write back the updated config
    config_text = "\n".join(updated_config)

    # Read the rest of the original config (metadata, quality categories, etc.)
    with open(config_path, "r") as f:
        original_lines = f.readlines()

    # Find where to insert the new config (after the existing sources/test_images)
    insert_point = 0
    for i, line in enumerate(original_lines):
        if line.strip().startswith("[sample_collections]"):
            insert_point = i
            break

    # Combine new config with the rest
    if insert_point > 0:
        remaining_config = "".join(original_lines[insert_point:])
        config_text += "\n" + remaining_config

    with open(config_path, "w") as f:
        f.write(config_text)

    print(f"Updated {config_path} with S3 bucket configuration")


def main():
    parser = argparse.ArgumentParser(description="Setup S3 access for herbarium images")
    parser.add_argument("--bucket", help="S3 bucket name (if known)")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--prefix", default="", help="S3 key prefix to explore")
    parser.add_argument("--max-keys", type=int, default=100, help="Maximum keys to explore")
    parser.add_argument("--list-buckets", action="store_true", help="List available buckets")
    parser.add_argument("--explore", action="store_true", help="Explore bucket contents")
    parser.add_argument("--update-config", action="store_true", help="Update image sources config")

    args = parser.parse_args()

    # Check AWS credentials
    if not check_aws_credentials():
        print("AWS credentials not configured. Please set up credentials using:")
        print("  aws configure")
        print("  or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return 1

    print("✅ AWS credentials found")

    # List buckets if requested
    if args.list_buckets:
        print("\n📦 Available S3 buckets:")
        buckets = list_s3_buckets()
        for bucket in buckets:
            print(f"  - {bucket}")
        return 0

    # Determine bucket name
    bucket_name = args.bucket
    if not bucket_name:
        print("Please specify --bucket name or use --list-buckets to see available buckets")
        return 1

    print(f"\n🔍 Exploring bucket: {bucket_name}")

    # Explore bucket contents
    if args.explore or args.update_config:
        objects = explore_bucket_contents(bucket_name, args.prefix, args.max_keys)

        if not objects:
            print("No objects found in bucket")
            return 1

        print(f"Found {len(objects)} objects")

        # Show first few objects
        print("\n📋 Sample objects:")
        for obj in objects[:10]:
            print(f"  {obj['key']} ({obj['size']} bytes)")

        if args.update_config:
            print("\n🔧 Categorizing images...")
            categories = categorize_images(objects)

            for category, keys in categories.items():
                if keys:
                    print(f"  {category}: {len(keys)} images")

            print("\n📝 Updating configuration...")
            update_image_sources_config(bucket_name, args.region, categories)

            print("✅ Configuration updated successfully!")
            print("\nNext steps:")
            print("1. Review config/image_sources.toml")
            print("2. Test image access with the updated URLs")
            print("3. Commit the configuration changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
