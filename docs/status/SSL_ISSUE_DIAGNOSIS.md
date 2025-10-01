# SSL Issue Diagnosis and Solutions

## Problem Analysis

The SSL certificate error you encountered is caused by three issues:

### 1. SSL Certificate Hostname Mismatch
```
certificate verify failed: Hostname mismatch, certificate is not valid for 'devvyn.aafc-srdc.herbarium.s3.us-east-1.amazonaws.com'
```

**Issue**: Custom subdomains like `devvyn.aafc-srdc.herbarium.s3.us-east-1.amazonaws.com` don't have valid SSL certificates.

### 2. Wrong AWS Region
- **Config shows**: `us-east-1`
- **Actual bucket region**: `ca-central-1` (confirmed by HTTP 301 redirect)

### 3. Private S3 Bucket
- **Current status**: 403 Forbidden (bucket exists but not publicly accessible)
- **Required**: Public read access for anonymous downloads

## Solutions (Choose One)

### Option A: Make Bucket Public and Fix URLs

1. **Make bucket publicly readable**:
   ```bash
   # Set bucket policy for public read access
   aws s3api put-bucket-policy --bucket devvyn.aafc-srdc.herbarium --policy '{
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::devvyn.aafc-srdc.herbarium/*"
       }
     ]
   }'
   ```

2. **Use correct URL format**:
   ```
   OLD: https://devvyn.aafc-srdc.herbarium.s3.us-east-1.amazonaws.com/images/...
   NEW: https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/images/...
   ```

### Option B: Use AWS CLI with Credentials

```bash
# Download images using AWS CLI (bypasses SSL/public access issues)
aws s3 cp s3://devvyn.aafc-srdc.herbarium/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg trial_images/specimen_001.jpg

# Then process normally
python cli.py process --input trial_images/ --output trial_results/ --engine vision
```

### Option C: Skip S3 Downloads (Recommended)

Since you mentioned the bucket is available, use it directly:

```bash
# If you have local access to the 2,800 images, process directly:
python cli.py process --input /path/to/your/images/ --output production_results/ --engine vision
```

## Immediate Fix for Testing

Create a working test script that bypasses S3:

```python
# Create some test images manually for immediate testing
mkdir trial_images
# Copy any local images you have
cp /path/to/any/herbarium/images/*.jpg trial_images/

# Or create a minimal test
echo "Testing with local files only" > trial_images/test.txt
```

## Recommended Action

**For immediate testing**: Use Option C - bypass S3 and use local images
**For production**: Fix the bucket permissions (Option A) for future reproducibility

The core OCR processing works perfectly - this is just a configuration issue with the sample image distribution system.