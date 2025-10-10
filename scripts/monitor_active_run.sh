#!/bin/bash
# Monitor active processing run

RUN_DIR="full_dataset_processing/run_20250930_181456"
PID=96490

echo "=== AAFC Processing Monitor ==="
echo "Run: $RUN_DIR"
echo "PID: $PID"
echo ""

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Process RUNNING ($(ps -p $PID -o etime= | tr -d ' '))"
else
    echo "❌ Process STOPPED"
fi

echo ""
echo "=== Output Directory ==>"
ls -lh "$RUN_DIR/" 2>/dev/null || echo "Directory not found"

echo ""
echo "=== Latest Log (last 20 lines) ==="
tail -20 "$RUN_DIR/processing.log" 2>/dev/null || echo "No log yet"

echo ""
echo "=== Database Status ==="
if [ -f "$RUN_DIR/app.db" ]; then
    SIZE=$(du -h "$RUN_DIR/app.db" | awk '{print $1}')
    COUNT=$(sqlite3 "$RUN_DIR/app.db" "SELECT COUNT(*) FROM specimens;" 2>/dev/null || echo "0")
    echo "Database: $SIZE, Specimens: $COUNT"
else
    echo "Database not yet created"
fi

echo ""
echo "=== System Load ==="
uptime
