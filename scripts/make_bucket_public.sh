#!/bin/bash
# Script to make S3 bucket publicly readable

echo "🔧 Making S3 bucket publicly accessible..."

BUCKET="devvyn.aafc-srdc.herbarium"

# Step 1: Remove public access blocks
echo "📝 Step 1: Remove public access blocks..."
aws s3api delete-public-access-block --bucket "$BUCKET"

if [ $? -eq 0 ]; then
    echo "✅ Public access blocks removed"
else
    echo "❌ Failed to remove public access blocks"
    echo "   This may require AWS console access or different permissions"
fi

# Step 2: Apply public read policy
echo "📝 Step 2: Apply public read policy..."

cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket "$BUCKET" --policy file:///tmp/bucket-policy.json

if [ $? -eq 0 ]; then
    echo "✅ Public read policy applied"
    echo "🧪 Testing public access..."

    # Test URL
    TEST_URL="https://s3.ca-central-1.amazonaws.com/$BUCKET/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL")

    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ SUCCESS: Bucket is now publicly accessible!"
        echo "🔗 Test URL works: $TEST_URL"
    elif [ "$HTTP_CODE" = "403" ]; then
        echo "⚠️ Still getting 403 Forbidden - may need additional configuration"
    else
        echo "❓ Got HTTP code: $HTTP_CODE"
    fi
else
    echo "❌ Failed to apply public read policy"
fi

# Cleanup
rm -f /tmp/bucket-policy.json

echo ""
echo "📋 If this script fails, you can make the bucket public via AWS Console:"
echo "   1. Go to AWS S3 Console"
echo "   2. Select bucket: $BUCKET"
echo "   3. Permissions tab → Block public access → Edit → Uncheck 'Block all public access'"
echo "   4. Permissions tab → Bucket policy → Add policy from /tmp/bucket-policy.json"
echo ""
