# Installation

This guide covers installing CodeGeass and its dependencies.

## Requirements

- **Python 3.10+** - CodeGeass requires Python 3.10 or later
- **Claude Code** - The Claude CLI tool must be installed and authenticated
- **Git** - Required for version control features

## Install Claude Code

First, ensure Claude Code is installed:

```bash
# Check if Claude Code is installed
claude --version

# If not installed, follow instructions at:
# https://claude.ai/code
```

## Install CodeGeass

### One-Line Installer (Recommended)

The fastest way to get started with CodeGeass is using the automated installer:

```bash
curl -fsSL https://raw.githubusercontent.com/DonTizi/CodeGeass/main/install.sh | bash
```

This installer will:

- Check for Python 3.10+ (auto-installs on macOS via Homebrew if needed)
- Install CodeGeass in a dedicated virtual environment at `~/.codegeass/venv`
- Verify or prompt for Claude CLI installation
- Set up the 24/7 scheduler service (launchd on macOS, systemd on Linux)
- Configure all necessary directories

The installer handles both fresh installations and updates automatically.

### From PyPI

```bash
pip install codegeass
```

### From Source

```bash
git clone https://github.com/dontizi/codegeass.git
cd codegeass
pip install -e .
```

### With Optional Dependencies

```bash
# With notification support (Telegram, Discord)
pip install codegeass[notifications]

# With development tools
pip install codegeass[dev]

# With documentation tools
pip install codegeass[docs]

# Everything
pip install codegeass[notifications,dev,docs]
```

## Verify Installation

```bash
# Check version
codegeass --version

# View available commands
codegeass --help
```

Expected output:

```
Usage: codegeass [OPTIONS] COMMAND [ARGS]...

  CodeGeass - Claude Code Scheduler Framework

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  approval      Manage plan mode approvals
  cron          CRON job management
  execution     Manage task executions
  logs          View execution logs
  notification  Manage notifications
  scheduler     Scheduler operations
  skill         Manage skills
  task          Manage scheduled tasks
```

## Updating CodeGeass

If you installed via the one-line installer, simply run it again:

```bash
curl -fsSL https://raw.githubusercontent.com/DonTizi/CodeGeass/main/install.sh | bash
```

If you installed manually via pip:

```bash
pip install --upgrade codegeass
```

To update to a specific version:

```bash
pip install codegeass==0.2.0
```

## Uninstalling CodeGeass

To completely remove CodeGeass:

```bash
curl -fsSL https://raw.githubusercontent.com/DonTizi/CodeGeass/main/uninstall.sh | bash
```

This will:

- Remove the virtual environment at `~/.codegeass/venv`
- Uninstall the scheduler service (launchd/systemd)
- Optionally remove configuration files (you'll be prompted)

## Installing the Scheduler Service

For production use, you can install CodeGeass as a systemd service that runs automatically:

```bash
# Navigate to your CodeGeass project
cd /path/to/your/project

# Run the installer
./service/install.sh
```

This will:

1. Install a systemd user service and timer
2. Configure it to run every 5 minutes
3. Enable it to start on boot

See [Production Setup](../guides/production-setup.md) for detailed instructions.

## Directory Structure

After installation, CodeGeass uses these directories:

```
~/.codegeass/              # Global user config
├── projects.yaml          # Project registry
├── credentials.yaml       # API keys, secrets (gitignored)
└── skills/                # Shared skills (available to all projects)

./config/                  # Project config (in your repo)
├── schedules.yaml         # Task definitions
├── settings.yaml          # Project settings
└── notifications.yaml     # Notification channels

./data/                    # Runtime data (gitignored)
├── logs/                  # Execution logs (JSONL)
└── sessions/              # Claude session data
```

## Next Steps

- [Quick Start](quickstart.md) - Create your first task
- [Configuration](configuration.md) - Configure CodeGeass for your project
- [Production Setup](../guides/production-setup.md) - Run CodeGeass 24/7
