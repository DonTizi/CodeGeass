#!/bin/bash
# CodeGeass Scheduler Service Installer
# Installs systemd user service for automatic task scheduling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Systemd user directory
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo -e "${GREEN}CodeGeass Scheduler Service Installer${NC}"
echo "======================================="
echo ""

# Find codegeass binary
CODEGEASS_BIN=$(which codegeass 2>/dev/null || true)
if [ -z "$CODEGEASS_BIN" ]; then
    echo -e "${RED}Error: codegeass command not found${NC}"
    echo "Please install CodeGeass first: pip install codegeass"
    exit 1
fi

CODEGEASS_PATH=$(dirname "$CODEGEASS_BIN")
echo "Found codegeass at: $CODEGEASS_BIN"

# Check if systemd user session is available
if ! systemctl --user status &> /dev/null; then
    echo -e "${RED}Error: systemd user session not available${NC}"
    echo "This system may not support user services."
    exit 1
fi

# Create systemd user directory if needed
mkdir -p "$SYSTEMD_USER_DIR"

# Determine working directory
if [ -n "$1" ]; then
    WORKING_DIR="$1"
else
    WORKING_DIR="$PROJECT_DIR"
fi

# Verify working directory has config
if [ ! -f "$WORKING_DIR/config/schedules.yaml" ]; then
    echo -e "${YELLOW}Warning: No config/schedules.yaml found in $WORKING_DIR${NC}"
    echo "You may need to initialize the project: codegeass project init"
fi

echo "Installing service with:"
echo "  Working directory: $WORKING_DIR"
echo "  CodeGeass binary:  $CODEGEASS_BIN"
echo ""

# Copy and configure service file
echo "Installing codegeass-scheduler.service..."
sed -e "s|WORKING_DIR_PLACEHOLDER|$WORKING_DIR|g" \
    -e "s|CODEGEASS_BIN_PLACEHOLDER|$CODEGEASS_BIN|g" \
    -e "s|CODEGEASS_PATH_PLACEHOLDER|$CODEGEASS_PATH|g" \
    "$SCRIPT_DIR/codegeass-scheduler.service" \
    > "$SYSTEMD_USER_DIR/codegeass-scheduler.service"

# Copy timer file
echo "Installing codegeass-scheduler.timer..."
cp "$SCRIPT_DIR/codegeass-scheduler.timer" "$SYSTEMD_USER_DIR/"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl --user daemon-reload

# Enable lingering (allows user services to run without login)
echo "Enabling lingering for user $USER..."
if command -v loginctl &> /dev/null; then
    loginctl enable-linger "$USER" 2>/dev/null || echo -e "${YELLOW}Note: Could not enable lingering (may require root)${NC}"
fi

# Enable and start timer
echo "Enabling and starting timer..."
systemctl --user enable codegeass-scheduler.timer
systemctl --user start codegeass-scheduler.timer

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Service status:"
systemctl --user status codegeass-scheduler.timer --no-pager || true
echo ""
echo "Useful commands:"
echo "  Check timer status:     systemctl --user status codegeass-scheduler.timer"
echo "  Check service logs:     journalctl --user -u codegeass-scheduler -f"
echo "  Run manually:           systemctl --user start codegeass-scheduler.service"
echo "  Stop timer:             systemctl --user stop codegeass-scheduler.timer"
echo "  Disable on boot:        systemctl --user disable codegeass-scheduler.timer"
echo ""
echo "The scheduler will run every 5 minutes and execute any due tasks."
