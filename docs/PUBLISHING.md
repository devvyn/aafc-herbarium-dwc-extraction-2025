# Publishing Dataset Releases

This document explains how to publish the dataset to GitHub Releases and S3 for public access.

## Quick Reference

**GitHub Pages**: https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/
**Repository**: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025

## Data Files Location

```
docs/data/
├── occurrence.csv     (606 KB  - Darwin Core CSV)
├── dwc-archive.zip    (168 KB  - GBIF-ready archive)
└── raw.jsonl          (2.5 MB  - with confidence scores)
```

## Publishing Workflow

### 1. GitHub Pages (Automatic)

GitHub Pages automatically serves files from `docs/` directory:

```
https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/
https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/occurrence.csv
https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/dwc-archive.zip
https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/raw.jsonl
```

**To enable** (one-time setup):
1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`, Folder: `/docs`
4. Save

**To update**: Just commit changes to `docs/` and push to main branch.

### 2. GitHub Releases (Manual)

Create versioned releases for major dataset updates:

```bash
# 1. Tag the release
git tag -a v1.0-vision-baseline -m "v1.0 Vision Baseline Dataset - 2,702 specimens"
git push origin v1.0-vision-baseline

# 2. Create release via GitHub UI or gh CLI
gh release create v1.0-vision-baseline \
  --title "v1.0 Vision Baseline Dataset" \
  --notes "Preview/Beta release - 2,702 AAFC herbarium specimens extracted via Apple Vision + GPT-4o-mini. See full documentation at https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/" \
  docs/data/occurrence.csv \
  docs/data/dwc-archive.zip \
  docs/data/raw.jsonl

# 3. Mark as pre-release
gh release edit v1.0-vision-baseline --prerelease
```

**Release URLs** will be:
```
https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/occurrence.csv
https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/dwc-archive.zip
https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/raw.jsonl
```

### 3. S3 Public Bucket (Optional)

For high-bandwidth distribution and direct file access without GitHub rate limits.

#### Setup (One-time)

```bash
# Create public S3 bucket
aws s3 mb s3://aafc-herbarium-data --region us-east-1

# Enable public access
aws s3api put-public-access-block \
  --bucket aafc-herbarium-data \
  --public-access-block-configuration \
    BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

# Set bucket policy (allow public read)
cat > /tmp/bucket-policy.json <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::aafc-herbarium-data/*"
    }
  ]
}
POLICY

aws s3api put-bucket-policy \
  --bucket aafc-herbarium-data \
  --policy file:///tmp/bucket-policy.json
```

#### Upload Data

```bash
# Upload with versioning
aws s3 cp docs/data/occurrence.csv \
  s3://aafc-herbarium-data/v1.0/occurrence.csv \
  --content-type text/csv \
  --metadata version=1.0,status=preview,date=2025-10-31

aws s3 cp docs/data/dwc-archive.zip \
  s3://aafc-herbarium-data/v1.0/dwc-archive.zip \
  --content-type application/zip

aws s3 cp docs/data/raw.jsonl \
  s3://aafc-herbarium-data/v1.0/raw.jsonl \
  --content-type application/x-ndjson

# Verify public access
curl -I https://aafc-herbarium-data.s3.amazonaws.com/v1.0/occurrence.csv
```

**S3 URLs**:
```
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/occurrence.csv
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/dwc-archive.zip
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/raw.jsonl
```

#### Cost Estimate

- **Storage**: ~3 MB × $0.023/GB/month = **$0.00007/month**
- **Transfer**: 100 downloads/month × 3 MB × $0.09/GB = **$0.027/month**
- **Total**: **~$0.03/month** (negligible)

### 4. Update Documentation

After publishing, update these files with correct URLs:

1. **docs/index.md** - Landing page download links
2. **README.md** - Main download section
3. **CHANGELOG.md** - Release notes
4. **docs/CITATION.cff** - Citation file (if using DOI)

## Versioning Strategy

### Version Numbers

- **v1.0-vision-baseline**: Initial OCR extraction (current)
- **v1.1-reviewed**: After manual verification
- **v2.0-spatial-zones**: With location-aware extraction
- **v2.1-ensemble**: With multi-model voting

### Release Naming

```
v{MAJOR}.{MINOR}-{CODENAME}

Examples:
- v1.0-vision-baseline
- v1.1-reviewed-500
- v2.0-full-extraction
```

## Quality Levels

Mark releases with appropriate labels:

- 🧪 **Preview/Beta**: Unverified OCR data
- ⚠️ **Review Required**: Partial verification
- ✅ **Verified**: Manually checked
- 🏆 **Production**: Publication-ready

## Metadata Standards

### Manifest (manifest.json)

Every release should include:

```json
{
  "version": "1.0.0",
  "release_date": "2025-10-31",
  "record_count": 2702,
  "institution": "AAFC-SRDC",
  "extraction_method": "vision-api",
  "quality_level": "preview",
  "license": "CC0-1.0",
  "citation": "Murphy, D. (2025). AAFC Herbarium Dataset v1.0. DOI: pending"
}
```

### EML (Ecological Metadata Language)

Darwin Core Archives include `eml.xml` with:
- Dataset title, description, abstract
- Creator/contact information
- Geographic coverage
- Taxonomic coverage (if known)
- Data quality notes

## Automated Publishing

### GitHub Actions (Future)

```yaml
# .github/workflows/publish-dataset.yml
name: Publish Dataset

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            docs/data/occurrence.csv
            docs/data/dwc-archive.zip
            docs/data/raw.jsonl
          prerelease: ${{ contains(github.ref, 'preview') }}
      - name: Upload to S3
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: aws s3 sync docs/data/ s3://aafc-herbarium-data/${GITHUB_REF_NAME}/
```

## Monitoring Access

### GitHub Traffic

Check repository Insights → Traffic for:
- Clone statistics
- Visitor stats
- Popular content

### S3 Access Logs (if enabled)

```bash
# Enable logging
aws s3api put-bucket-logging \
  --bucket aafc-herbarium-data \
  --bucket-logging-status '{"LoggingEnabled":{"TargetBucket":"aafc-logs","TargetPrefix":"herbarium-access/"}}'

# Analyze logs
aws s3 ls s3://aafc-logs/herbarium-access/ --recursive
```

## Troubleshooting

### GitHub Pages not updating

1. Check Settings → Pages is enabled
2. Verify `docs/` folder exists in main branch
3. Wait 2-3 minutes for rebuild
4. Check Actions tab for Pages deployment status

### S3 Access Denied

```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket aafc-herbarium-data

# Test public access
curl -I https://aafc-herbarium-data.s3.amazonaws.com/v1.0/occurrence.csv
```

### Release URLs 404

- Verify tag exists: `git tag -l`
- Check release created: `gh release list`
- Confirm files attached: `gh release view v1.0-vision-baseline`

---

**Last updated**: 2025-10-31
