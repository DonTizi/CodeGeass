# Production Setup

This guide covers setting up CodeGeass for 24/7 production use with automatic task scheduling.

## Overview

CodeGeass can run as a systemd user service that:

- Starts automatically when your machine boots
- Runs the scheduler every 5 minutes
- Executes due tasks automatically
- Logs all activity to the system journal

## Prerequisites

- CodeGeass installed (`pip install codegeass`)
- A CodeGeass project initialized with tasks
- Linux with systemd (most modern distributions)
- User lingering enabled (for services to run without login)

## Quick Install

```bash
# Navigate to your CodeGeass project
cd /path/to/your/project

# Run the installer
./service/install.sh

# Or specify a different working directory
./service/install.sh /path/to/another/project
```

The installer will:

1. Copy service files to `~/.config/systemd/user/`
2. Configure the working directory
3. Enable lingering for your user
4. Start the timer

## Manual Installation

If you prefer to install manually:

### 1. Copy Service Files

```bash
# Create systemd user directory
mkdir -p ~/.config/systemd/user

# Copy files (adjust paths as needed)
cp service/codegeass-scheduler.service ~/.config/systemd/user/
cp service/codegeass-scheduler.timer ~/.config/systemd/user/
```

### 2. Configure Working Directory

Edit the service file to set your project path:

```bash
# Edit the service file
nano ~/.config/systemd/user/codegeass-scheduler.service

# Replace WORKING_DIR_PLACEHOLDER with your project path
# For example: /home/user/my-project
```

### 3. Enable and Start

```bash
# Reload systemd
systemctl --user daemon-reload

# Enable lingering (allows services to run without login)
loginctl enable-linger $USER

# Enable and start the timer
systemctl --user enable codegeass-scheduler.timer
systemctl --user start codegeass-scheduler.timer
```

## Service Management

### Check Status

```bash
# Timer status (shows next run time)
systemctl --user status codegeass-scheduler.timer

# Service status (shows last run result)
systemctl --user status codegeass-scheduler.service
```

### View Logs

```bash
# Follow logs in real-time
journalctl --user -u codegeass-scheduler -f

# View recent logs
journalctl --user -u codegeass-scheduler --since "1 hour ago"

# View all logs
journalctl --user -u codegeass-scheduler
```

### Manual Execution

```bash
# Run the scheduler immediately
systemctl --user start codegeass-scheduler.service

# This is equivalent to:
codegeass scheduler run
```

### Stop and Disable

```bash
# Stop the timer
systemctl --user stop codegeass-scheduler.timer

# Disable on boot
systemctl --user disable codegeass-scheduler.timer
```

## Uninstallation

```bash
# Run the uninstaller
./service/uninstall.sh
```

Or manually:

```bash
# Stop and disable
systemctl --user stop codegeass-scheduler.timer
systemctl --user disable codegeass-scheduler.timer

# Remove files
rm ~/.config/systemd/user/codegeass-scheduler.service
rm ~/.config/systemd/user/codegeass-scheduler.timer

# Reload
systemctl --user daemon-reload
```

## Configuration

### Timer Interval

The default interval is 5 minutes. To change it, edit the timer file:

```ini
# ~/.config/systemd/user/codegeass-scheduler.timer
[Timer]
# Run every minute
OnCalendar=*:*

# Run every 10 minutes
OnCalendar=*:0/10

# Run every hour
OnCalendar=*:00
```

After editing, reload:

```bash
systemctl --user daemon-reload
systemctl --user restart codegeass-scheduler.timer
```

### Environment Variables

The service automatically sets:

- `ANTHROPIC_API_KEY=""` - Ensures Claude uses subscription, not API credits
- `HOME` - Your home directory
- `PATH` - Standard system paths

To add custom environment variables, edit the service file:

```ini
[Service]
Environment="MY_VAR=value"
```

### Security Hardening

The service runs with security hardening:

- `NoNewPrivileges=yes` - Prevents privilege escalation
- `ProtectSystem=strict` - Read-only filesystem except allowed paths
- `ProtectHome=read-only` - Home directory is read-only except allowed paths

If you need to write to additional directories, add them to `ReadWritePaths`:

```ini
[Service]
ReadWritePaths=%h/.codegeass %h/.claude /path/to/project/data
```

## Multiple Projects

To run schedulers for multiple projects, create separate service instances:

```bash
# Copy with a different name
cp ~/.config/systemd/user/codegeass-scheduler.service \
   ~/.config/systemd/user/codegeass-project2.service

# Edit the new service with different WorkingDirectory
nano ~/.config/systemd/user/codegeass-project2.service

# Create matching timer
cp ~/.config/systemd/user/codegeass-scheduler.timer \
   ~/.config/systemd/user/codegeass-project2.timer

# Edit timer to reference correct service
# Unit=codegeass-project2.service

# Enable and start
systemctl --user daemon-reload
systemctl --user enable codegeass-project2.timer
systemctl --user start codegeass-project2.timer
```

## Troubleshooting

### Service Won't Start

```bash
# Check for errors
journalctl --user -u codegeass-scheduler -n 50

# Common issues:
# - codegeass not in PATH: Use full path in ExecStart
# - Working directory doesn't exist: Check WorkingDirectory
# - Missing config: Ensure config/schedules.yaml exists
```

### Timer Not Running

```bash
# Check timer status
systemctl --user list-timers

# Verify lingering is enabled
loginctl show-user $USER | grep Linger

# If Linger=no, enable it:
loginctl enable-linger $USER
```

### Permission Issues

```bash
# Check if service can access required directories
# The service runs with restricted permissions by default

# If you see permission errors, check ReadWritePaths in the service file
```

### Service Runs But Tasks Don't Execute

```bash
# Check if tasks are due
codegeass scheduler upcoming

# Run manually to see output
codegeass scheduler run

# Check task configuration
codegeass task list
```

## Monitoring

### With Notifications

Configure notifications to receive alerts when tasks complete or fail:

```bash
# Add Telegram notifications
codegeass notification add --provider telegram --token $BOT_TOKEN --chat-id $CHAT_ID

# Test notifications
codegeass notification test my-notification
```

### With System Monitoring

The service logs to the system journal, which can be integrated with monitoring tools:

```bash
# Export logs to a file
journalctl --user -u codegeass-scheduler --since "1 day ago" > scheduler.log

# Send alerts on errors (example with grep)
journalctl --user -u codegeass-scheduler -f | grep -i error
```

## Next Steps

- [Notifications Setup](setup-notifications.md) - Get alerts for task execution
- [CRON Automation](cron-setup.md) - Alternative to systemd using CRON
- [Task Creation](create-task.md) - Create and schedule tasks
