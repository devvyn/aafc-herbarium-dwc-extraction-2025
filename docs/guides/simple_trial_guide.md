# Simple Trial Run Guide

Since the S3 URLs are having SSL certificate issues, here are the easiest ways to run a trial:

## Option 1: Use Local Images (if available)

If you have any herbarium images locally (JPG, PNG files):

```bash
# Create directory and copy images
mkdir trial_images
cp /path/to/your/images/*.jpg trial_images/

# Process with Apple Vision
python cli.py process --input trial_images/ --output trial_results/ --engine vision

# Launch review interface
python review_web.py --db trial_results/candidates.db --images trial_images/
```

## Option 2: Test with Empty Database (Review Interface Only)

You can test the review interface even without processing:

```bash
# Create empty database
mkdir trial_results
touch trial_results/app.db
touch trial_results/candidates.db

# Test the web interface (will show empty state)
python review_web.py --db trial_results/candidates.db --images trial_images/
```

## Option 3: Fix S3 URLs and Use CLI

If you want to bypass the SSL issue:

```bash
# Download images directly using curl (bypasses Python SSL)
mkdir trial_images

# Example using standard S3 URLs
curl -o trial_images/specimen_001.jpg "https://s3.amazonaws.com/bucket-name/path/to/image1.jpg"
curl -o trial_images/specimen_002.jpg "https://s3.amazonaws.com/bucket-name/path/to/image2.jpg"

# Then process normally
python cli.py process --input trial_images/ --output trial_results/ --engine vision
```

## Option 4: Direct CLI Processing (Recommended)

**If you have access to your 2,800 specimens directory:**

```bash
# Process full collection directly
python cli.py process --input /path/to/2800_specimens/ --output production_results/ --engine vision

# This will:
# - Process all images with Apple Vision OCR
# - Create production_results/app.db with all data
# - Take ~4 hours for 2,800 specimens
# - Be ready for immediate curator review
```

## Testing the Review Workflow

Once you have processed data:

```bash
# Launch web interface
python review_web.py --db production_results/candidates.db --images /path/to/images/

# Open browser to: http://localhost:5000
# Features available:
# - Side-by-side image and extracted data
# - Edit Darwin Core fields
# - Approve/reject specimens
# - Export approved data
```

## Most Practical Approach

**For immediate testing tomorrow:**

1. **Skip the trial** - Go directly to full processing if you have image access
2. **Use Option 4** with your 2,800 specimens
3. **Let it run overnight** (4-hour processing)
4. **Review interface ready tomorrow morning**

This gives you real production data for curator testing rather than a small sample.
