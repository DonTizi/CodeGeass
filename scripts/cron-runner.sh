#!/bin/bash
# CodeGeass CRON Runner
# This script is called by cron to execute due tasks
#
# CRITICAL: This script UNSETS ANTHROPIC_API_KEY to use your
# Claude Pro/Max subscription instead of API credits.

set -e

# CRITICAL: Use subscription, not API
unset ANTHROPIC_API_KEY

# Project paths
PROJECT_DIR="/home/dontizi/Projects/codegeass"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/data/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Timestamp for log
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log file for cron output
CRON_LOG="$LOG_DIR/cron.log"

echo "[$TIMESTAMP] CodeGeass scheduler starting..." >> "$CRON_LOG"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "[$TIMESTAMP] ERROR: Virtual environment not found at $VENV_DIR" >> "$CRON_LOG"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run scheduler (use absolute path to ensure correct Python in cron environment)
"$VENV_DIR/bin/python" -m codegeass.cli.main scheduler run >> "$CRON_LOG" 2>&1
EXIT_CODE=$?

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Scheduler completed successfully" >> "$CRON_LOG"
else
    echo "[$TIMESTAMP] Scheduler exited with code $EXIT_CODE" >> "$CRON_LOG"
fi

echo "---" >> "$CRON_LOG"
