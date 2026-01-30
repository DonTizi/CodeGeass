#!/bin/bash
set -e

# CodeGeass Universal Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/DonTizi/CodeGeass/main/install.sh | bash

VERSION="latest"
CODEGEASS_DIR="$HOME/.codegeass"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║              CodeGeass Installer                          ║"
    echo "║         Claude Code Scheduler Framework                   ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

detect_arch() {
    case "$(uname -m)" in
        x86_64)  echo "amd64" ;;
        arm64)   echo "arm64" ;;
        aarch64) echo "arm64" ;;
        *)       echo "unknown" ;;
    esac
}

check_python() {
    if find_python; then
        PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        log_success "Python $PYTHON_VERSION found ($PYTHON_BIN)"
        return 0
    else
        log_warn "Python 3.10+ not found"
        return 1
    fi
}

install_python() {
    log_info "Installing Python 3.12..."
    OS=$(detect_os)

    if [ "$OS" = "macos" ]; then
        if command -v brew &> /dev/null; then
            brew install python@3.12
            # Find the Homebrew Python path
            if [ -f "/opt/homebrew/opt/python@3.12/bin/python3.12" ]; then
                PYTHON_BIN="/opt/homebrew/opt/python@3.12/bin/python3.12"
                PIP_BIN="/opt/homebrew/opt/python@3.12/bin/pip3.12"
            elif [ -f "/usr/local/opt/python@3.12/bin/python3.12" ]; then
                PYTHON_BIN="/usr/local/opt/python@3.12/bin/python3.12"
                PIP_BIN="/usr/local/opt/python@3.12/bin/pip3.12"
            fi
            export PYTHON_BIN PIP_BIN
            log_success "Python 3.12 installed via Homebrew"
            log_info "Using: $PYTHON_BIN"
            return 0
        else
            log_error "Homebrew not found. Install it first: https://brew.sh"
            return 1
        fi
    elif [ "$OS" = "linux" ]; then
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3.12 python3.12-venv python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3.12
        else
            log_error "Please install Python 3.10+ manually"
            return 1
        fi
        PYTHON_BIN="python3.12"
        PIP_BIN="pip3.12"
        export PYTHON_BIN PIP_BIN
        log_success "Python installed"
        return 0
    fi
    return 1
}

find_python() {
    # Try to find a suitable Python 3.10+
    for py in python3.12 python3.11 python3.10 python3; do
        if command -v $py &> /dev/null; then
            version=$($py -c 'import sys; print(f"{sys.version_info.minor}")')
            if [ "$version" -ge 10 ]; then
                PYTHON_BIN=$py
                # Find corresponding pip
                pip_name=$(echo $py | sed 's/python/pip/')
                if command -v $pip_name &> /dev/null; then
                    PIP_BIN=$pip_name
                else
                    PIP_BIN="$py -m pip"
                fi
                export PYTHON_BIN PIP_BIN
                return 0
            fi
        fi
    done

    # Check Homebrew paths on macOS
    for path in /opt/homebrew/opt/python@3.12/bin /usr/local/opt/python@3.12/bin; do
        if [ -f "$path/python3.12" ]; then
            PYTHON_BIN="$path/python3.12"
            PIP_BIN="$path/pip3.12"
            export PYTHON_BIN PIP_BIN
            return 0
        fi
    done

    return 1
}

check_claude() {
    if command -v claude &> /dev/null; then
        log_success "Claude CLI found: $(claude --version 2>/dev/null || echo 'installed')"
        return 0
    else
        log_warn "Claude CLI not found"
        return 1
    fi
}

install_claude_cli() {
    log_info "Installing Claude CLI..."

    OS=$(detect_os)

    if [ "$OS" = "macos" ]; then
        if command -v brew &> /dev/null; then
            brew install claude 2>/dev/null || {
                log_info "Trying npm install..."
                npm install -g @anthropic-ai/claude-code
            }
        elif command -v npm &> /dev/null; then
            npm install -g @anthropic-ai/claude-code
        else
            log_error "Please install Claude CLI manually: https://claude.ai/code"
            return 1
        fi
    elif [ "$OS" = "linux" ]; then
        if command -v npm &> /dev/null; then
            npm install -g @anthropic-ai/claude-code
        else
            log_error "Please install npm first, then run: npm install -g @anthropic-ai/claude-code"
            return 1
        fi
    fi

    if command -v claude &> /dev/null; then
        log_success "Claude CLI installed"
        return 0
    else
        log_error "Claude CLI installation failed"
        return 1
    fi
}

install_codegeass() {
    log_info "Installing CodeGeass..."

    # Use the correct pip
    if [ -n "$PIP_BIN" ]; then
        $PIP_BIN install --user --upgrade codegeass
    else
        pip3 install --user --upgrade codegeass
    fi

    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"

        # Add to shell profile
        SHELL_PROFILE=""
        if [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_PROFILE="$HOME/.bash_profile"
        fi

        if [ -n "$SHELL_PROFILE" ]; then
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_PROFILE" 2>/dev/null; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_PROFILE"
                log_info "Added ~/.local/bin to PATH in $SHELL_PROFILE"
            fi
        fi
    fi

    if command -v codegeass &> /dev/null || [ -f "$HOME/.local/bin/codegeass" ]; then
        log_success "CodeGeass installed: $($HOME/.local/bin/codegeass --version 2>/dev/null || echo 'installed')"
        return 0
    else
        log_error "CodeGeass installation failed"
        return 1
    fi
}

setup_directories() {
    log_info "Setting up directories..."

    mkdir -p "$CODEGEASS_DIR"
    mkdir -p "$CODEGEASS_DIR/skills"
    mkdir -p "$CODEGEASS_DIR/logs"

    log_success "Created $CODEGEASS_DIR"
}

install_launchd_service() {
    log_info "Installing launchd service (macOS)..."

    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.codegeass.scheduler.plist"

    mkdir -p "$PLIST_DIR"

    # Find codegeass path
    CODEGEASS_BIN=$(which codegeass 2>/dev/null || echo "$HOME/.local/bin/codegeass")

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codegeass.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>$CODEGEASS_BIN</string>
        <string>scheduler</string>
        <string>run-due</string>
    </array>

    <key>StartInterval</key>
    <integer>300</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$CODEGEASS_DIR/logs/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>$CODEGEASS_DIR/logs/scheduler.error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.local/bin</string>
    </dict>
</dict>
</plist>
EOF

    # Load the service
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"

    log_success "launchd service installed and started"
    log_info "Service runs every 5 minutes"
    log_info "Logs: $CODEGEASS_DIR/logs/scheduler.log"
}

install_systemd_service() {
    log_info "Installing systemd service (Linux)..."

    SYSTEMD_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_DIR"

    # Find codegeass path
    CODEGEASS_BIN=$(which codegeass 2>/dev/null || echo "$HOME/.local/bin/codegeass")

    # Service file
    cat > "$SYSTEMD_DIR/codegeass-scheduler.service" << EOF
[Unit]
Description=CodeGeass Scheduler
After=network.target

[Service]
Type=oneshot
ExecStart=$CODEGEASS_BIN scheduler run-due
Environment="PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"

[Install]
WantedBy=default.target
EOF

    # Timer file (every 5 minutes)
    cat > "$SYSTEMD_DIR/codegeass-scheduler.timer" << EOF
[Unit]
Description=CodeGeass Scheduler Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Reload and enable
    systemctl --user daemon-reload
    systemctl --user enable codegeass-scheduler.timer
    systemctl --user start codegeass-scheduler.timer

    log_success "systemd timer installed and started"
    log_info "Service runs every 5 minutes"
    log_info "Check status: systemctl --user status codegeass-scheduler.timer"
}

install_scheduler_service() {
    OS=$(detect_os)

    if [ "$OS" = "macos" ]; then
        install_launchd_service
    elif [ "$OS" = "linux" ]; then
        install_systemd_service
    else
        log_warn "Unknown OS, skipping service installation"
        log_info "You can manually set up a cron job:"
        log_info "  */5 * * * * codegeass scheduler run-due"
    fi
}

print_success() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Quick start:"
    echo ""
    echo "  1. Initialize a project:"
    echo "     cd /path/to/your/project"
    echo "     codegeass init"
    echo ""
    echo "  2. Create a task:"
    echo "     codegeass task create --name daily-review \\"
    echo "       --prompt 'Review recent changes' \\"
    echo "       --schedule '0 9 * * *'"
    echo ""
    echo "  3. Check scheduler status:"
    echo "     codegeass scheduler status"
    echo ""
    echo "  4. View logs:"
    echo "     codegeass logs list"
    echo ""
    echo "Documentation: https://dontizi.github.io/codegeass/"
    echo ""

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}NOTE: Restart your terminal or run:${NC}"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi
}

main() {
    print_banner

    OS=$(detect_os)
    ARCH=$(detect_arch)
    log_info "Detected: $OS ($ARCH)"

    # Check Python
    if ! check_python; then
        read -p "Install Python 3.12? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            if ! install_python; then
                log_error "Failed to install Python. Please install Python 3.10+ manually."
                exit 1
            fi
            # Re-check after install
            if ! check_python; then
                log_error "Python still not found. Please restart your terminal and try again."
                exit 1
            fi
        else
            log_error "Python 3.10+ is required. Exiting."
            exit 1
        fi
    fi

    # Check/Install Claude CLI
    if ! check_claude; then
        read -p "Install Claude CLI? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            install_claude_cli || log_warn "Continue without Claude CLI"
        fi
    fi

    # Setup directories
    setup_directories

    # Install CodeGeass
    install_codegeass

    # Install scheduler service
    read -p "Install 24/7 scheduler service? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        install_scheduler_service
    fi

    print_success
}

# Run main (works both when executed directly and when piped)
main "$@"
