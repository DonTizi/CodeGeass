# Installation

This guide covers installing CodeGeass and its dependencies.

## Requirements

- **Python 3.11+** - CodeGeass requires Python 3.11 or later
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

### From PyPI (Recommended)

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

## Directory Structure

After installation, CodeGeass uses these directories:

```
~/.codegeass/              # Global user config
└── credentials.yaml       # API keys, secrets (gitignored)

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
