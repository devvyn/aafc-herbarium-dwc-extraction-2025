#!/usr/bin/env python3
"""Fix S3 URLs in image_sources.toml configuration."""

import re
from pathlib import Path

def fix_s3_urls(content):
    """Convert old S3 URLs to correct format."""
    # Pattern: https://devvyn.aafc-srdc.herbarium.s3.us-east-1.amazonaws.com/path
    # Replace: https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/path

    old_pattern = r'https://devvyn\.aafc-srdc\.herbarium\.s3\.us-east-1\.amazonaws\.com/'
    new_base = 'https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/'

    fixed_content = re.sub(old_pattern, new_base, content)

    return fixed_content

def main():
    config_path = Path('config/image_sources.toml')

    print("🔧 Fixing S3 URLs in image_sources.toml...")

    # Read current content
    with open(config_path, 'r') as f:
        content = f.read()

    # Count URLs to fix
    old_pattern = r'https://devvyn\.aafc-srdc\.herbarium\.s3\.us-east-1\.amazonaws\.com/'
    old_urls = len(re.findall(old_pattern, content))

    if old_urls == 0:
        print("✅ No URLs to fix - configuration already correct")
        return

    print(f"📝 Found {old_urls} URLs to fix")

    # Fix URLs
    fixed_content = fix_s3_urls(content)

    # Verify fix
    new_urls = len(re.findall(old_pattern, fixed_content))
    fixed_urls = old_urls - new_urls

    # Write back
    with open(config_path, 'w') as f:
        f.write(fixed_content)

    print(f"✅ Fixed {fixed_urls} URLs")
    print("🔗 URLs now use format: https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/...")

    # Test one URL
    print("\n🧪 Testing URL access...")
    import requests
    test_url = "https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg"

    try:
        response = requests.head(test_url, timeout=10)
        if response.status_code == 200:
            print("✅ URL format fixed - images are accessible!")
        elif response.status_code == 403:
            print("⚠️ URLs fixed but bucket is private (403 Forbidden)")
            print("   Need to make bucket public for downloads to work")
        else:
            print(f"❓ URL test returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ URL test failed: {e}")

if __name__ == "__main__":
    main()