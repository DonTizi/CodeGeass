<p align="center">
  <img src="https://raw.githubusercontent.com/DonTizi/CodeGeass/main/public/logo.png" alt="CodeGeass Logo" width="200" />
</p>

# CodeGeass

[![PyPI version](https://badge.fury.io/py/codegeass.svg)](https://pypi.org/project/codegeass/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Claude Code Scheduler Framework** - Orchestrate automated Claude Code sessions with templates, prompts and skills, executed via CRON with your Pro/Max subscription.

## Features

- **Scheduled Tasks**: Define tasks with CRON expressions for automated execution
- **Multi-Provider Support**: Use Claude Code, OpenAI Codex, or other AI coding assistants
- **Multi-Project Support**: Manage multiple projects from a single installation with shared skills
- **Skills Integration**: Use Claude Code skills (`.claude/skills/`) for consistent, reusable prompts
- **Multiple Strategies**: Headless, autonomous, or skill-based execution
- **Session Management**: Track execution history with detailed logs
- **CLI Interface**: Full-featured command line tool for task management
- **Web Dashboard**: React + FastAPI dashboard for monitoring and management
- **Notifications**: Telegram, Discord, and Microsoft Teams notifications with plan approval support
- **24/7 Service**: Automatic scheduler for macOS (launchd) and Linux (systemd)

## Installation

### Using pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs CLI tools in isolated environments. This is the recommended method:

```bash
# Install pipx if you don't have it
# macOS
brew install pipx && pipx ensurepath

# Linux
python3 -m pip install --user pipx && pipx ensurepath

# Then install CodeGeass + start the 24/7 scheduler
pipx install codegeass
codegeass setup
```

### Using pip (in a virtual environment)

If you prefer using pip, we recommend a virtual environment:

```bash
# Create and activate a virtual environment
python3 -m venv ~/.codegeass-venv
source ~/.codegeass-venv/bin/activate

# Install CodeGeass
pip install codegeass

# Add to PATH (add this to your ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.codegeass-venv/bin:$PATH"

# Setup with 24/7 scheduler
codegeass setup
```

### With notification support

```bash
pipx install "codegeass[notifications]"
```

### From Source

```bash
git clone https://github.com/DonTizi/CodeGeass.git
cd CodeGeass
pip install -e .
```

### Verify Installation

```bash
codegeass --version
```

## Quick Start

### 1. Full Setup (One Command)

```bash
codegeass setup
```

This will:
- Detect your OS (macOS/Linux)
- Install the 24/7 background scheduler
- Show you the next steps

### 2. Initialize a Project

```bash
cd /path/to/your/project
codegeass init
```

### 3. Create a Task

```bash
# Using a skill
codegeass task create \
  --name daily-review \
  --skill code-review \
  --schedule "0 9 * * 1-5" \
  --working-dir /path/to/project

# Using a direct prompt
codegeass task create \
  --name check-tests \
  --prompt "Run the test suite and report any failures" \
  --schedule "0 3 * * *" \
  --working-dir /path/to/project
```

### 4. Manage Tasks

```bash
codegeass task list              # List all tasks
codegeass task show daily-review # Show task details
codegeass task run daily-review  # Run manually
```

### 5. Monitor

```bash
codegeass logs list              # View execution logs
codegeass scheduler upcoming     # See upcoming runs
codegeass dashboard              # Open web dashboard
```

## Scheduler Management

```bash
# Check scheduler status
# macOS
launchctl list | grep codegeass

# Linux
systemctl --user status codegeass-scheduler.timer

# Uninstall scheduler
codegeass uninstall-scheduler
```

## CLI Commands

### Tasks

```bash
codegeass task list              # List all tasks
codegeass task show <name>       # Show task details
codegeass task create [opts]     # Create new task
codegeass task run <name>        # Run task manually
codegeass task stop <name>       # Stop running task
codegeass task enable <name>     # Enable task
codegeass task disable <name>    # Disable task
codegeass task delete <name>     # Delete task
```

### Skills

```bash
codegeass skill list             # List available skills
codegeass skill show <name>      # Show skill details
codegeass skill validate <name>  # Validate skill format
codegeass skill render <name>    # Preview rendered skill
```

### Scheduler

```bash
codegeass scheduler status       # Show scheduler status
codegeass scheduler run          # Run due tasks
codegeass scheduler run --force  # Run all enabled tasks
codegeass scheduler upcoming     # Show upcoming tasks
```

### Logs

```bash
codegeass logs list              # List recent logs
codegeass logs show <task>       # Show logs for task
codegeass logs tail <task>       # Tail recent logs
codegeass logs stats             # Show statistics
```

### Projects

```bash
codegeass project list           # List registered projects
codegeass project add <path>     # Register a project
codegeass project show <name>    # Show project details
codegeass project set-default <name>  # Set default project
codegeass project init [path]    # Initialize project structure
codegeass project remove <name>  # Unregister a project
codegeass project enable <name>  # Enable a project
codegeass project disable <name> # Disable a project
codegeass project update <name>  # Update project settings
```

### Notifications

```bash
codegeass notification list              # List notification channels
codegeass notification add               # Add a channel (interactive)
codegeass notification show <id>         # Show channel details
codegeass notification test <id>         # Test a channel
codegeass notification remove <id>       # Remove a channel
codegeass notification enable <id>       # Enable a channel
codegeass notification disable <id>      # Disable a channel
codegeass notification providers         # List available providers
```

### Providers

```bash
codegeass provider list          # List available code execution providers
codegeass provider info <name>   # Show provider details
codegeass provider check         # Check provider availability
```

## Notifications

Send notifications to chat platforms (Telegram, Discord, Microsoft Teams) when tasks start, complete, or fail.

### Setup

1. **Add a notification channel**:

```bash
# Add Telegram channel (interactive prompts for bot token and chat ID)
codegeass notification add --provider telegram --name "My Alerts"

# Add Discord channel (interactive prompt for webhook URL)
codegeass notification add --provider discord --name "DevOps Channel"

# Add Microsoft Teams channel (interactive prompt for webhook URL)
codegeass notification add --provider teams --name "Dev Team"
```

2. **Test the channel**:

```bash
codegeass notification test <channel-id>
```

3. **Create tasks with notifications**:

```bash
codegeass task create \
  --name daily-backup \
  --prompt "Run backup script" \
  --schedule "0 2 * * *" \
  --notify <channel-id> \
  --notify-on start \
  --notify-on complete \
  --notify-on failure
```

### Supported Providers

| Provider | Requirements | Features |
|----------|--------------|----------|
| **Telegram** | Bot token from @BotFather, Chat ID | Message editing, inline buttons, HTML formatting |
| **Discord** | Webhook URL | Markdown formatting, embeds |
| **Microsoft Teams** | Power Automate Workflows webhook URL | Adaptive Cards, Dashboard-based approvals |

### Configuration

Channels are stored in `config/notifications.yaml` (non-sensitive config).
Credentials are stored in `~/.codegeass/credentials.yaml` (secrets, not in repo).

### Message Editing

For Telegram, notifications are edited in-place rather than sending multiple messages:
- Task start: Shows "Running..."
- Task complete: Updates same message with result and duration

## Skills

Skills are Claude Code prompt templates stored in `.claude/skills/`. They follow the [Agent Skills](https://agentskills.io) open standard.

### Included Skills

- **review**: Comprehensive code review for PRs or recent changes (correctness, security, performance, maintainability, tests)
- **security-scan**: Deep security analysis with secrets detection, dependency vulnerabilities, and CWE references
- **code-review**: Automated code review with security, performance, and maintainability focus
- **security-audit**: Deep security analysis for OWASP vulnerabilities and secrets
- **test-runner**: Execute and analyze test suites
- **dependency-check**: Analyze dependencies for updates and vulnerabilities
- **refactor**: Automated code refactoring into clean, single-responsibility modules following SOLID principles

### Shared Skills

Place skills in `~/.codegeass/skills/` to make them available across all registered projects. Project-specific skills in `.claude/skills/` take priority over shared skills with the same name.

### Skill Format

```yaml
---
name: my-skill
description: What the skill does
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# Skill Instructions

Instructions for $ARGUMENTS.

## Dynamic Context
- Status: !`git status`
```

## Configuration

### config/schedules.yaml

```yaml
tasks:
  - name: daily-code-review
    skill: code-review
    schedule: "0 9 * * 1-5"
    working_dir: /home/user/projects/myapp

  - name: weekly-security-audit
    skill: security-audit
    schedule: "0 2 * * 0"
    working_dir: /home/user/projects/myapp
    autonomous: true
```

### config/settings.yaml

```yaml
claude:
  default_model: sonnet
  default_timeout: 300
  unset_api_key: true

scheduler:
  check_interval: 60
  max_concurrent: 1
```

## Subscription Usage

**Important**: CodeGeass is designed to use your Claude Pro/Max subscription, NOT API credits.

The scheduler automatically unsets `ANTHROPIC_API_KEY` to ensure your subscription is used.

## Architecture

```
codegeass/
├── src/codegeass/
│   ├── core/           # Domain entities and value objects
│   │   └── entities/   # Modular entity classes (Task, Skill, Project, etc.)
│   ├── storage/        # Persistence layer (YAML, JSON)
│   │   └── project_repository.py  # Multi-project registry
│   ├── factory/        # Task and skill registries
│   │   └── skill_resolver.py  # Project + shared skills with priority
│   ├── providers/      # Universal code execution providers
│   │   ├── claude/     # Claude Code adapter
│   │   └── codex/      # OpenAI Codex adapter
│   ├── execution/      # Execution layer
│   │   ├── strategies/ # Execution strategies (headless, autonomous, skill, plan)
│   │   ├── tracker/    # Execution tracking and crash recovery
│   │   └── plan_service/  # Plan mode approval workflow
│   ├── scheduling/     # CRON parsing and job scheduling
│   ├── notifications/  # Chat notifications (Telegram, Discord, Teams)
│   │   └── callbacks/  # Interactive callback handling
│   └── cli/            # Click CLI commands
│       └── commands/   # Modular command groups (task/, project/, etc.)
├── dashboard/          # Web dashboard (React + FastAPI)
├── config/             # Configuration files
├── data/               # Runtime data (logs, sessions)
├── scripts/            # CRON runner script
└── .claude/skills/     # Claude Code skills

~/.codegeass/           # Global user configuration
├── projects.yaml       # Project registry
├── credentials.yaml    # Secrets
└── skills/             # Shared skills (all projects)
```

## Web Dashboard

A React + FastAPI dashboard for managing tasks and viewing logs.

```bash
codegeass dashboard
```

Then open http://localhost:8001

Or run manually:

```bash
cd dashboard
./setup.sh    # First-time setup
./run.sh      # Run frontend (5173) + backend (8001)
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/codegeass

# Linting
ruff check src/codegeass

# Build package
python -m build
```

## Documentation

- **Live docs**: https://dontizi.github.io/codegeass/
- **Build locally**: `pip install -e ".[docs]" && mkdocs serve`

## Uninstalling

### Complete Uninstall

Remove everything (scheduler, config, logs, tasks):

```bash
codegeass uninstall --all
pipx uninstall codegeass
```

### Partial Uninstall

Remove scheduler only (keep your tasks and config):

```bash
codegeass uninstall-scheduler
pipx uninstall codegeass
```

### Uninstall Options

```bash
codegeass uninstall --all              # Remove everything
codegeass uninstall --all -y           # Skip confirmation
codegeass uninstall --all --keep-global   # Keep ~/.codegeass/
codegeass uninstall --all --keep-project  # Keep config/ and data/
```

## Troubleshooting

### Permission denied on macOS with pipx

```bash
mkdir -p ~/.local/bin && chmod 755 ~/.local/bin
pipx install codegeass
```

### Command not found after install

```bash
# Restart your terminal, or run:
source ~/.bashrc  # or ~/.zshrc
```

### Scheduler not running

```bash
# Check logs
# macOS
cat /tmp/codegeass-scheduler.log

# Linux
journalctl --user -u codegeass-scheduler -f
```

## Release Process

Releases are automated via GitHub Actions when a tag is pushed:

```bash
# Use the release skill
/release 0.2.0

# Or manually: update version, commit, tag, push
```

The workflow will:
1. Build and test the package
2. Publish to PyPI (via OIDC trusted publishing)
3. Create a GitHub release with assets
4. Deploy versioned documentation

## License

MIT
