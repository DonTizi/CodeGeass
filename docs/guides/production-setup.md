# Production Setup

This guide covers setting up CodeGeass for 24/7 production use with automatic task scheduling.

## Quick Setup (Recommended)

The easiest way to set up the 24/7 scheduler is with the setup command:

```bash
codegeass setup
```

This automatically:

1. Detects your operating system
2. Installs the appropriate scheduler:
   - **macOS**: launchd service
   - **Linux**: systemd user timer
3. Starts the scheduler immediately

The scheduler runs every minute and executes any due tasks.

### Verify It's Running

```bash
# macOS
launchctl list | grep codegeass

# Linux
systemctl --user status codegeass-scheduler.timer
```

### Uninstall

```bash
codegeass uninstall-scheduler
```

---

## Manual Setup (Advanced)

If you prefer manual configuration or need custom settings, follow the instructions below.

### Linux (systemd)

CodeGeass can run as a systemd user service that:

- Starts automatically when your machine boots
- Runs the scheduler every minute
- Executes due tasks automatically
- Logs all activity to the system journal

#### Prerequisites

- CodeGeass installed (`pipx install codegeass`)
- A CodeGeass project initialized with tasks
- Linux with systemd (most modern distributions)
- User lingering enabled (for services to run without login)

#### Manual Installation

##### 1. Create Service Files

```bash
# Create systemd user directory
mkdir -p ~/.config/systemd/user

# Create service file
cat > ~/.config/systemd/user/codegeass-scheduler.service << 'EOF'
[Unit]
Description=CodeGeass Scheduler - Run due tasks
After=network.target

[Service]
Type=oneshot
ExecStart=/home/YOUR_USER/.local/bin/codegeass scheduler run-due
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/home/YOUR_USER/.local/bin"
Environment="ANTHROPIC_API_KEY="

[Install]
WantedBy=default.target
EOF

# Create timer file
cat > ~/.config/systemd/user/codegeass-scheduler.timer << 'EOF'
[Unit]
Description=CodeGeass Scheduler Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF
```

Replace `YOUR_USER` with your username, or use `$HOME` path.

##### 2. Enable and Start

```bash
# Reload systemd
systemctl --user daemon-reload

# Enable lingering (allows services to run without login)
loginctl enable-linger $USER

# Enable and start the timer
systemctl --user enable codegeass-scheduler.timer
systemctl --user start codegeass-scheduler.timer
```

### macOS (launchd)

#### Manual Installation

```bash
# Create LaunchAgents directory
mkdir -p ~/Library/LaunchAgents

# Create plist file
cat > ~/Library/LaunchAgents/com.codegeass.scheduler.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codegeass.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USER/.local/bin/codegeass</string>
        <string>scheduler</string>
        <string>run-due</string>
    </array>
    <key>StartInterval</key>
    <integer>60</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/codegeass-scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/codegeass-scheduler.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/Users/YOUR_USER/.local/bin</string>
    </dict>
</dict>
</plist>
EOF

# Replace YOUR_USER with your username
sed -i '' "s/YOUR_USER/$USER/g" ~/Library/LaunchAgents/com.codegeass.scheduler.plist

# Load the service
launchctl load ~/Library/LaunchAgents/com.codegeass.scheduler.plist
```

## Service Management

### Check Status

```bash
# Linux - Timer status (shows next run time)
systemctl --user status codegeass-scheduler.timer

# Linux - Service status (shows last run result)
systemctl --user status codegeass-scheduler.service

# macOS
launchctl list | grep codegeass
```

### View Logs

```bash
# Linux - Follow logs in real-time
journalctl --user -u codegeass-scheduler -f

# Linux - View recent logs
journalctl --user -u codegeass-scheduler --since "1 hour ago"

# macOS
tail -f /tmp/codegeass-scheduler.log
cat /tmp/codegeass-scheduler.err
```

### Manual Execution

```bash
# Linux - Run the scheduler immediately
systemctl --user start codegeass-scheduler.service

# This is equivalent to:
codegeass scheduler run-due
```

### Stop and Disable

```bash
# Linux
systemctl --user stop codegeass-scheduler.timer
systemctl --user disable codegeass-scheduler.timer

# macOS
launchctl unload ~/Library/LaunchAgents/com.codegeass.scheduler.plist
```

## Configuration

### Timer Interval

#### Linux (systemd)

Edit `~/.config/systemd/user/codegeass-scheduler.timer`:

```ini
[Timer]
# Run every minute (default)
OnUnitActiveSec=1min

# Run every 5 minutes
OnUnitActiveSec=5min

# Run every hour
OnUnitActiveSec=1h
```

After editing:

```bash
systemctl --user daemon-reload
systemctl --user restart codegeass-scheduler.timer
```

#### macOS (launchd)

Edit `~/Library/LaunchAgents/com.codegeass.scheduler.plist`:

```xml
<key>StartInterval</key>
<integer>60</integer>  <!-- seconds, 60 = 1 minute -->
```

After editing:

```bash
launchctl unload ~/Library/LaunchAgents/com.codegeass.scheduler.plist
launchctl load ~/Library/LaunchAgents/com.codegeass.scheduler.plist
```

### Environment Variables

The scheduler automatically unsets `ANTHROPIC_API_KEY` to ensure Claude uses your subscription, not API credits.

To add custom environment variables:

#### Linux

Edit the service file and add:

```ini
[Service]
Environment="MY_VAR=value"
```

#### macOS

Add to the plist:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>MY_VAR</key>
    <string>value</string>
</dict>
```

## Troubleshooting

### Service Won't Start

```bash
# Linux - Check for errors
journalctl --user -u codegeass-scheduler -n 50

# macOS - Check error log
cat /tmp/codegeass-scheduler.err

# Common issues:
# - codegeass not in PATH: Use full path in ExecStart/ProgramArguments
# - Working directory doesn't exist
# - Missing config: Ensure config/schedules.yaml exists
```

### Timer Not Running (Linux)

```bash
# Check timer status
systemctl --user list-timers

# Verify lingering is enabled
loginctl show-user $USER | grep Linger

# If Linger=no, enable it:
loginctl enable-linger $USER
```

### Service Runs But Tasks Don't Execute

```bash
# Check if tasks are due
codegeass scheduler upcoming

# Run manually to see output
codegeass scheduler run-due

# Check task configuration
codegeass task list
```

## Monitoring

### With Notifications

Configure notifications to receive alerts when tasks complete or fail:

```bash
# Add Telegram notifications
codegeass notification add --provider telegram --name "My Alerts"

# Test notifications
codegeass notification test my-alerts
```

### With System Monitoring

The service logs to the system journal (Linux) or files (macOS), which can be integrated with monitoring tools:

```bash
# Linux - Export logs to a file
journalctl --user -u codegeass-scheduler --since "1 day ago" > scheduler.log

# Send alerts on errors (example with grep)
journalctl --user -u codegeass-scheduler -f | grep -i error
```

## Next Steps

- [Notifications Setup](setup-notifications.md) - Get alerts for task execution
- [Task Creation](create-task.md) - Create and schedule tasks
