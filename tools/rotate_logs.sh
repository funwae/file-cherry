#!/usr/bin/env bash
# tools/rotate_logs.sh
# Rotate and clean up old log files.

set -euo pipefail

DATA_DIR="${FILECHERRY_DATA_DIR:-/data}"
LOGS_DIR="$DATA_DIR/logs"
RETENTION_DAYS="${LOG_RETENTION_DAYS:-30}"
MAX_SIZE_MB="${LOG_MAX_SIZE_MB:-512}"

if [[ ! -d "$LOGS_DIR" ]]; then
  echo "Logs directory not found: $LOGS_DIR"
  exit 1
fi

echo "Rotating logs in $LOGS_DIR..."
echo "Retention: $RETENTION_DAYS days"
echo "Max size: $MAX_SIZE_MB MB"

# Remove logs older than retention period
find "$LOGS_DIR" -name "*.log.*" -type f -mtime +$RETENTION_DAYS -delete

# Check total log size and remove oldest if needed
TOTAL_SIZE_MB=$(du -sm "$LOGS_DIR" | cut -f1)

if [[ $TOTAL_SIZE_MB -gt $MAX_SIZE_MB ]]; then
  echo "Total log size ($TOTAL_SIZE_MB MB) exceeds limit ($MAX_SIZE_MB MB)"
  echo "Removing oldest log files..."

  # Remove oldest backup files first
  find "$LOGS_DIR" -name "*.log.*" -type f -printf '%T@ %p\n' | \
    sort -n | \
    head -n -5 | \
    cut -d' ' -f2- | \
    xargs rm -f || true
fi

echo "Log rotation complete."

