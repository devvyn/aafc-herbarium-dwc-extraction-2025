# 📸 Reproducible Image Access for Herbarium Digitization

This guide explains how to set up and use reproducible image references for testing, documentation, and development of the herbarium digitization toolkit.

## 🎯 Overview

The toolkit provides a comprehensive system for managing test images that enables:

- **Reproducible testing** across different environments
- **Consistent documentation** with standard example images
- **Quality stratification** for realistic testing scenarios
- **Public accessibility** for team collaboration and community use

## 🔧 Setup Process

### Step 1: Configure AWS Access

You have several options for AWS access:

#### Option A: Use Existing API Key
If you have an AWS API key from another repository:

1. Copy your AWS credentials:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1  # or your preferred region
   ```

2. Or create a credentials file:
   ```bash
   mkdir -p ~/.aws
   cat > ~/.aws/credentials << EOF
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   EOF
   ```

#### Option B: Create New Claude-Specific Key
For dedicated access, create a new IAM user with S3 read permissions:

1. AWS Console → IAM → Users → Create User
2. Attach policy: `AmazonS3ReadOnlyAccess`
3. Create access key for programmatic access
4. Use credentials as in Option A

### Step 2: Discover Your S3 Bucket

Use the setup script to find and explore your bucket:

```bash
# Install required dependency
pip install boto3

# List available buckets
python scripts/setup_s3_access.py --list-buckets

# Explore a specific bucket
python scripts/setup_s3_access.py --bucket your-herbarium-bucket --explore

# Update configuration with discovered images
python scripts/setup_s3_access.py --bucket your-herbarium-bucket --update-config
```

### Step 3: Verify Configuration

After setup, verify your configuration works:

```bash
# List available image categories
python scripts/manage_test_images.py list-categories

# Validate that URLs are accessible
python scripts/manage_test_images.py validate-urls

# List available sample collections
python scripts/manage_test_images.py list-collections
```

## 📊 Image Quality Stratification

The system organizes images into quality categories for realistic testing:

### 🟢 Readable Specimens (40% of test set)
- **Characteristics**: Clear, legible labels with good lighting
- **Expected Accuracy**: >95% with GPT processing
- **Use Case**: Demonstrating best-case performance

### 🟡 Minimal Text Specimens (25% of test set)
- **Characteristics**: Some readable text, acceptable quality
- **Expected Accuracy**: ~85% with hybrid triage
- **Use Case**: Testing OCR fallback scenarios

### 🟠 Unlabeled Specimens (20% of test set)
- **Characteristics**: No visible text labels, specimen only
- **Expected Accuracy**: ~30% (limited to specimen analysis)
- **Use Case**: Testing edge cases and failure modes

### 🔴 Poor Quality Specimens (15% of test set)
- **Characteristics**: Blurry, damaged, or difficult to process
- **Expected Accuracy**: ~15% (requires manual review)
- **Use Case**: Testing robustness and error handling

### 🌍 Multilingual Specimens (Variable)
- **Characteristics**: Labels in various languages
- **Expected Accuracy**: ~80% with multilingual OCR
- **Use Case**: Testing language detection and processing

## 🎯 Usage Examples

### Create Test Bundles for Development

```bash
# Create a small demo bundle (10 images)
python scripts/manage_test_images.py create-bundle demo \
  --output ./test_images/demo \
  --download

# Create comprehensive validation set (100 images)
python scripts/manage_test_images.py create-bundle validation \
  --output ./test_images/validation \
  --download

# Create performance benchmark set (1000 images)
python scripts/manage_test_images.py create-bundle benchmark \
  --output ./test_images/benchmark
  # Note: --download omitted for large sets to use URLs directly
```

### Generate Documentation URLs

```bash
# Get 3 URLs per category for documentation
python scripts/manage_test_images.py generate-doc-urls --count 3
```

Output example:
```
readable_specimens:
  https://your-bucket.s3.us-east-1.amazonaws.com/clear_specimen_001.jpg
  https://your-bucket.s3.us-east-1.amazonaws.com/readable_label_002.jpg
  https://your-bucket.s3.us-east-1.amazonaws.com/good_quality_003.jpg
```

### Validate Image Accessibility

```bash
# Check all categories
python scripts/manage_test_images.py validate-urls

# Check specific category
python scripts/manage_test_images.py validate-urls --category readable_specimens
```

## 🔄 Integration with Processing Scripts

### Use with Hybrid Triage Processing

```bash
# Process a test bundle with the hybrid triage system
python scripts/process_with_hybrid_triage.py \
  --input ./test_images/validation \
  --output ./results/validation_test \
  --budget 5.00 \
  --openai-api-key your_key
```

### Use with OCR Validation

```bash
# Run validation tests using stratified samples
python scripts/run_ocr_validation.py \
  --engines tesseract vision_swift multilingual \
  --test-bundle ./test_images/validation \
  --config config/test_validation.toml
```

## 🌐 Public Access Configuration

### Making Images Publicly Accessible

To make images accessible to teammates and community members:

1. **S3 Bucket Policy** (if using S3):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-herbarium-bucket/*"
       }
     ]
   }
   ```

2. **CDN Setup** (optional, for better performance):
   ```toml
   # In config/image_sources.toml
   [public_access]
   enable_public_urls = true
   cdn_endpoint = "your-cdn-endpoint.cloudfront.net"
   cache_control = "public, max-age=3600"
   ```

3. **URL Templates**:
   The system supports multiple URL patterns:
   - Direct S3: `https://bucket.s3.region.amazonaws.com/key`
   - CDN: `https://cdn-endpoint/key`
   - Custom domain: `https://images.your-domain.com/key`

## 📁 File Structure

After setup, your repository will have:

```
config/
├── image_sources.toml          # Central configuration
└── test_validation.toml        # Testing parameters

scripts/
├── setup_s3_access.py          # Initial S3 configuration
└── manage_test_images.py       # Image management utilities

test_images/                    # Downloaded test bundles
├── demo/                       # Small demo set
├── validation/                 # Comprehensive validation set
└── benchmark/                  # Performance testing set
```

## 🔍 Troubleshooting

### Common Issues

**AWS credentials not found**:
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**Bucket access denied**:
- Verify IAM permissions include `s3:ListBucket` and `s3:GetObject`
- Check bucket policy allows your IAM user/role

**Images not downloading**:
```bash
# Test URL accessibility
curl -I "https://your-bucket.s3.region.amazonaws.com/test-image.jpg"
```

**Configuration not found**:
```bash
# Regenerate configuration
python scripts/setup_s3_access.py --bucket your-bucket --update-config
```

### Validation Commands

```bash
# Test AWS connection
aws s3 ls s3://your-bucket --max-items 5

# Test image accessibility
python scripts/manage_test_images.py validate-urls --category readable_specimens

# Verify bundle creation
python scripts/manage_test_images.py create-bundle demo --output ./test --download
```

## 🎉 Benefits for Team Collaboration

### For Developers
- **Consistent test data** across development environments
- **Reproducible benchmarks** for performance comparisons
- **Automated testing** with realistic image diversity

### For Documentation
- **Standard example images** for tutorials and guides
- **Quality category examples** for accuracy demonstrations
- **Public URLs** for easy sharing in documentation

### For Scientific Users
- **Realistic test scenarios** matching real herbarium collections
- **Quality expectations** aligned with processing capabilities
- **Reproducible workflows** for institutional adoption

## 📈 Next Steps

Once your reproducible image system is configured:

1. **Run validation tests** to establish baseline performance
2. **Update documentation** with your specific image examples
3. **Share public URLs** with team members for collaboration
4. **Integrate with CI/CD** for automated testing with real images

The system provides a solid foundation for reproducible, collaborative herbarium digitization workflows! 🌿📊