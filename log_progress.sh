#!/bin/bash
# Log progress to file every 5 minutes

LOG_FILE="/Users/devvynmurphy/Documents/GitHub/aafc-herbarium-dwc-extraction-2025/progress.log"

while true; do
    count=$(ls /tmp/imgcache/*.jpg 2>/dev/null | wc -l | tr -d ' ')
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Images fetched: $count / 2885" >> "$LOG_FILE"
    sleep 300  # 5 minutes
done
