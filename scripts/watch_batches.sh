#!/bin/bash
#
# Quick-start batch monitoring using watch command
# Opens two terminal windows monitoring current batch experiments
#

cd "$(dirname "$0")/.."

echo "🔍 Starting batch monitors..."
echo ""
echo "Opening terminal windows for:"
echo "  - Few-Shot v2: batch_68e588743e2c8190a7d6e429c1ac3cc4"
echo "  - CoT v2: batch_68e5888230288190a6702f4b50998888"
echo ""

# Check if watch is available
if ! command -v watch &> /dev/null; then
    echo "❌ 'watch' command not found. Install with: brew install watch"
    exit 1
fi

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Open two terminal windows with watch commands
osascript <<EOF
tell application "Terminal"
    do script "cd '$PWD' && watch -n 30 'export OPENAI_API_KEY=\"$OPENAI_API_KEY\" && uv run python scripts/monitor_batch.py --batch-id batch_68e588743e2c8190a7d6e429c1ac3cc4 --no-poll'"
    do script "cd '$PWD' && watch -n 30 'export OPENAI_API_KEY=\"$OPENAI_API_KEY\" && uv run python scripts/monitor_batch.py --batch-id batch_68e5888230288190a6702f4b50998888 --no-poll'"
end tell
EOF

echo "✅ Monitoring windows opened"
echo "   Updates every 30 seconds"
echo "   Press Ctrl+C in each window to stop"
