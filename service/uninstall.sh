#!/bin/bash
# CodeGeass Scheduler Service Uninstaller
# Removes systemd user service for automatic task scheduling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo -e "${YELLOW}CodeGeass Scheduler Service Uninstaller${NC}"
echo "========================================"
echo ""

# Check if service exists
if [ ! -f "$SYSTEMD_USER_DIR/codegeass-scheduler.timer" ] && [ ! -f "$SYSTEMD_USER_DIR/codegeass-scheduler.service" ]; then
    echo "Service not installed. Nothing to do."
    exit 0
fi

# Stop and disable timer
echo "Stopping and disabling timer..."
systemctl --user stop codegeass-scheduler.timer 2>/dev/null || true
systemctl --user disable codegeass-scheduler.timer 2>/dev/null || true

# Stop service if running
echo "Stopping service..."
systemctl --user stop codegeass-scheduler.service 2>/dev/null || true

# Remove service files
echo "Removing service files..."
rm -f "$SYSTEMD_USER_DIR/codegeass-scheduler.service"
rm -f "$SYSTEMD_USER_DIR/codegeass-scheduler.timer"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl --user daemon-reload

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "Note: User lingering was not disabled. To disable manually:"
echo "  loginctl disable-linger $USER"
