#!/bin/bash

# Full AAFC Herbarium Dataset Processing Script
# Authors: Devin Murphy (AAFC) & Claude (Anthropic AI)
# Target: 2,886 specimens in ~3.3 hours

echo "=== AAFC Herbarium Full Dataset Processing ==="
echo "Target: 2,886 specimens"
echo "Estimated time: 3.3 hours"
echo "Started: $(date)"
echo ""

# Create output directory with timestamp
OUTPUT_DIR="full_dataset_processing/run_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Test S3 access first
echo "Testing S3 bucket access..."
if curl -s -I "https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/images/00/0e/000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84.jpg" | grep -q "200 OK"; then
    echo "✅ S3 bucket accessible"
else
    echo "❌ S3 bucket not accessible - check permissions"
    exit 1
fi

echo ""
echo "Starting full dataset processing..."
echo "This will take approximately 3.3 hours"
echo ""

# Process with Apple Vision (bypassing LLM to avoid API key issues)
python cli.py process \
    --input "s3://devvyn.aafc-srdc.herbarium/images/" \
    --output "$OUTPUT_DIR" \
    --engine vision \
    --batch-size 100

PROCESS_EXIT_CODE=$?

if [ $PROCESS_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Processing completed successfully!"
    echo "Completed: $(date)"
    echo ""

    # Generate summary statistics
    python -c "
import sqlite3
import os

db_path = '$OUTPUT_DIR/app.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count total specimens
    cursor.execute('SELECT COUNT(*) FROM specimens')
    total_count = cursor.fetchone()[0]

    # Count processing status
    cursor.execute('SELECT status, COUNT(*) FROM processing_state GROUP BY status')
    status_counts = cursor.fetchall()

    print(f'=== PROCESSING SUMMARY ===')
    print(f'Total specimens: {total_count:,}')
    print()
    print('Processing status:')
    for status, count in status_counts:
        print(f'  {status}: {count:,} specimens')

    # Count extracted fields
    cursor.execute('SELECT COUNT(*) FROM final_values')
    field_count = cursor.fetchone()[0]
    print(f'')
    print(f'Total fields extracted: {field_count:,}')

    conn.close()
else:
    print('Database not found - check processing output')
"

    echo ""
    echo "Results available in: $OUTPUT_DIR"
    echo "Next step: Generate Darwin Core CSV for stakeholders"

else
    echo ""
    echo "❌ Processing failed with exit code: $PROCESS_EXIT_CODE"
    echo "Check logs in: $OUTPUT_DIR"
fi
