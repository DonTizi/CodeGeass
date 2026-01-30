#!/bin/bash
set -e

# CodeGeass Uninstaller

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo -e "${YELLOW}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              CodeGeass Uninstaller                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Darwin*) OS="macos" ;;
    Linux*)  OS="linux" ;;
esac

# Stop and remove scheduler service
if [ "$OS" = "macos" ]; then
    PLIST_FILE="$HOME/Library/LaunchAgents/com.codegeass.scheduler.plist"
    if [ -f "$PLIST_FILE" ]; then
        log_info "Stopping launchd service..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        rm -f "$PLIST_FILE"
        log_success "launchd service removed"
    fi
elif [ "$OS" = "linux" ]; then
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    if [ -f "$SYSTEMD_DIR/codegeass-scheduler.timer" ]; then
        log_info "Stopping systemd service..."
        systemctl --user stop codegeass-scheduler.timer 2>/dev/null || true
        systemctl --user disable codegeass-scheduler.timer 2>/dev/null || true
        rm -f "$SYSTEMD_DIR/codegeass-scheduler.timer"
        rm -f "$SYSTEMD_DIR/codegeass-scheduler.service"
        systemctl --user daemon-reload
        log_success "systemd service removed"
    fi
fi

# Uninstall Python package
log_info "Uninstalling CodeGeass package..."
pip3 uninstall -y codegeass 2>/dev/null || true
log_success "Package uninstalled"

# Ask about data
echo ""
read -p "Remove configuration and data (~/.codegeass)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.codegeass"
    log_success "Configuration removed"
else
    log_info "Configuration kept at ~/.codegeass"
fi

echo ""
echo -e "${GREEN}CodeGeass uninstalled.${NC}"
