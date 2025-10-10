#!/bin/bash
# Monitor image fetching progress

while true; do
    count=$(ls /tmp/imgcache/*.jpg 2>/dev/null | wc -l | tr -d ' ')
    timestamp=$(date '+%H:%M:%S')
    echo "$timestamp - Images fetched: $count / 2885"
    sleep 30
done
