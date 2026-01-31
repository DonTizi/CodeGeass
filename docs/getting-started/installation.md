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

### Using pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs Python CLI tools in isolated environments. This is the recommended method because it:

- Keeps CodeGeass isolated from your system Python
- Avoids dependency conflicts
- Makes the `codegeass` command globally available

```bash
# Install pipx first

# macOS
brew install pipx
pipx ensurepath

# Linux (Debian/Ubuntu)
sudo apt install pipx
pipx ensurepath

# Linux (other) or if apt doesn't have pipx
python3 -m pip install --user pipx
pipx ensurepath

# Restart your terminal, then install CodeGeass
pipx install codegeass
```

### Using pip (in a virtual environment)

If you prefer pip, we strongly recommend using a virtual environment:

```bash
# Create a dedicated virtual environment
python3 -m venv ~/.codegeass-venv

# Activate it
source ~/.codegeass-venv/bin/activate

# Install CodeGeass
pip install codegeass

# Add to your PATH permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.codegeass-venv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

!!! warning "Avoid `pip install` without a virtual environment"
    On modern systems (macOS, Ubuntu 23+), installing packages system-wide with pip is restricted. Always use pipx or a virtual environment.

### From Source

For development or to get the latest changes:

```bash
git clone https://github.com/dontizi/codegeass.git
cd codegeass
pip install -e .
```

### With Optional Dependencies

```bash
# With notification support (Telegram, Discord, Teams)
pipx install "codegeass[notifications]"

# If using pip in a venv:
pip install "codegeass[notifications]"

# With development tools
pip install "codegeass[dev]"

# With documentation tools
pip install "codegeass[docs]"

# Everything
pip install "codegeass[notifications,dev,docs]"
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
  dashboard     Start the web dashboard
  execution     Manage task executions
  init          Initialize project structure
  logs          View execution logs
  notification  Manage notifications
  project       Manage projects
  provider      Manage code providers
  scheduler     Scheduler operations
  setup         Install 24/7 scheduler
  skill         Manage skills
  task          Manage scheduled tasks
  uninstall-scheduler  Remove the scheduler
```

## Setup the 24/7 Scheduler

After installing CodeGeass, run the setup command to install the background scheduler:

```bash
codegeass setup
```

This will:

1. Detect your operating system
2. Install the appropriate scheduler:
   - **macOS**: launchd service (`~/Library/LaunchAgents/com.codegeass.scheduler.plist`)
   - **Linux**: systemd user timer (`~/.config/systemd/user/codegeass-scheduler.timer`)
3. Start the scheduler immediately

The scheduler runs every minute and executes any due tasks automatically.

### Setup Command Behavior

#### First time setup

```
CodeGeass Setup

Detected OS: Darwin
CodeGeass path: /Users/you/.local/bin/codegeass

Installing 24/7 scheduler...
Using launchd (macOS native)
✓ Scheduler installed (launchd)

╭─ Setup Complete ─────────────────────────╮
│ ✓ CodeGeass is ready!                    │
│                                          │
│ 24/7 Scheduler: Running (launchd)        │
│ Check status: launchctl list | grep ...  │
│ Uninstall: codegeass uninstall-scheduler │
╰──────────────────────────────────────────╯
```

#### Running setup again (already installed)

If the scheduler is already installed, setup will detect it and skip reinstallation:

```
CodeGeass Setup

Detected OS: Darwin
CodeGeass path: /Users/you/.local/bin/codegeass

✓ Scheduler already installed (launchd (running))
Use --force to reinstall
```

#### Force reinstall

Use `--force` to reinstall the scheduler (useful after upgrading CodeGeass):

```bash
codegeass setup --force
```

```
Reinstalling scheduler (was: launchd (running))...
Using launchd (macOS native)
✓ Scheduler reinstalled (launchd)
```

### Verify Scheduler is Running

```bash
# macOS
launchctl list | grep codegeass

# Linux
systemctl --user status codegeass-scheduler.timer
```

### View Scheduler Logs

```bash
# macOS
cat /tmp/codegeass-scheduler.log
cat /tmp/codegeass-scheduler.err

# Linux
journalctl --user -u codegeass-scheduler -f
```

## Updating CodeGeass

### With pipx

```bash
pipx upgrade codegeass

# Reinstall the scheduler to use the new version
codegeass setup --force
```

### With pip (in venv)

```bash
source ~/.codegeass-venv/bin/activate
pip install --upgrade codegeass

# Reinstall the scheduler to use the new version
codegeass setup --force
```

### To a specific version

```bash
pipx install codegeass==0.3.0 --force

# or with pip
pip install codegeass==0.3.0
```

## Uninstalling CodeGeass

### Quick Uninstall (Everything)

Remove CodeGeass completely with one command:

```bash
codegeass uninstall --all
```

Output:
```
CodeGeass Uninstall

This will remove:
  - Scheduler service (launchd (running))
  - Global config (/Users/you/.codegeass)
  - Project config (/path/to/project/config)
  - Project data (/path/to/project/data)

Are you sure you want to continue? [y/N]: y

✓ Scheduler service removed
✓ Global config removed (/Users/you/.codegeass)
✓ Project config removed (/path/to/project/config)
✓ Project data removed (/path/to/project/data)

╭─ Uninstall Complete ─────────────────────╮
│ CodeGeass uninstalled successfully!      │
│                                          │
│ To remove the Python package:            │
│ pipx uninstall codegeass                 │
╰──────────────────────────────────────────╯
```

Then remove the package:

```bash
pipx uninstall codegeass
```

### Uninstall Options

| Command | What it removes |
|---------|-----------------|
| `codegeass uninstall` | Scheduler only |
| `codegeass uninstall --all` | Everything (scheduler + config + data) |
| `codegeass uninstall --all --keep-global` | Everything except ~/.codegeass/ |
| `codegeass uninstall --all --keep-project` | Everything except config/ and data/ |
| `codegeass uninstall --all -y` | Everything, skip confirmation |

### What Gets Removed

| Flag | Scheduler | Global Config | Project Config | Project Data |
|------|-----------|---------------|----------------|--------------|
| (none) | ✓ | - | - | - |
| `--all` | ✓ | ✓ | ✓ | ✓ |
| `--all --keep-global` | ✓ | - | ✓ | ✓ |
| `--all --keep-project` | ✓ | ✓ | - | - |

**Locations:**

- **Scheduler**: `~/Library/LaunchAgents/com.codegeass.scheduler.plist` (macOS) or `~/.config/systemd/user/codegeass-scheduler.*` (Linux)
- **Global config**: `~/.codegeass/` (credentials, shared skills, project registry)
- **Project config**: `./config/` (tasks, settings, notifications)
- **Project data**: `./data/` (logs, sessions)

### Partial Uninstall

#### Remove scheduler only

```bash
codegeass uninstall-scheduler
```

This keeps all your tasks, logs, and configuration intact.

#### Remove package only (keep data)

```bash
# First remove scheduler
codegeass uninstall-scheduler

# Then uninstall package
pipx uninstall codegeass
```

Your config and data remain for future reinstallation.

### Manual Cleanup

If you already uninstalled the package and need to clean up:

**Remove scheduler manually:**

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.codegeass.scheduler.plist
rm ~/Library/LaunchAgents/com.codegeass.scheduler.plist

# Linux
systemctl --user disable --now codegeass-scheduler.timer
rm ~/.config/systemd/user/codegeass-scheduler.timer
rm ~/.config/systemd/user/codegeass-scheduler.service
systemctl --user daemon-reload
```

**Remove data manually:**

```bash
# Global config
rm -rf ~/.codegeass

# Project config (in each project directory)
rm -rf config/ data/
```

## Troubleshooting

### Permission denied on macOS

If you get a permission error when installing with pipx:

```bash
mkdir -p ~/.local/bin
chmod 755 ~/.local/bin
pipx install codegeass
```

### Command not found after install

Restart your terminal or run:

```bash
source ~/.bashrc  # or ~/.zshrc on macOS
```

### externally-managed-environment error

This error means your system Python is protected. Use pipx instead:

```bash
# macOS
brew install pipx && pipx ensurepath

# Then restart terminal and install
pipx install codegeass
```

### Scheduler won't start

Check the logs:

```bash
# macOS
cat /tmp/codegeass-scheduler.log
cat /tmp/codegeass-scheduler.err

# Linux
journalctl --user -u codegeass-scheduler -f
```

Common issues:

- **codegeass not found**: The scheduler can't find the codegeass command. Reinstall with `codegeass setup --force`
- **Permission denied**: Check file permissions in your project directory
- **No tasks**: The scheduler runs but there are no due tasks. Check `codegeass scheduler upcoming`

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
