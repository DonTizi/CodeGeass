# CRON Automation Setup

This guide explains how to set up CRON for automatic task execution.

## Overview

CodeGeass uses system CRON to check for due tasks every minute:

```
┌─────────────────────────────────────────────────────────┐
│                    System CRON                          │
│  * * * * * codegeass scheduler run-due                  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Every minute
                           v
┌─────────────────────────────────────────────────────────┐
│                   CodeGeass Scheduler                   │
│  - Loads tasks from config/schedules.yaml               │
│  - Checks which tasks are due now                       │
│  - Executes due tasks                                   │
│  - Logs results                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Setup

```bash
# Install the CRON job
codegeass cron install

# Verify installation
codegeass cron status
```

That's it! Tasks will now run automatically according to their schedules.

## Manual Setup

If automatic installation doesn't work, set up CRON manually:

### Step 1: Find Python Path

```bash
which python
# or
which python3
```

### Step 2: Find CodeGeass Path

```bash
which codegeass
```

### Step 3: Edit Crontab

```bash
crontab -e
```

Add this line (adjust paths):

```cron
* * * * * /path/to/python -m codegeass scheduler run-due >> /tmp/codegeass-cron.log 2>&1
```

### Step 4: Verify

```bash
# Check crontab
crontab -l | grep codegeass

# Watch the log
tail -f /tmp/codegeass-cron.log
```

## Environment Variables

CRON runs with minimal environment. Important considerations:

### Claude Pro/Max Usage

CodeGeass deliberately **unsets** `ANTHROPIC_API_KEY` in CRON to use your subscription:

```python
# This happens automatically in CRON context
os.environ.pop('ANTHROPIC_API_KEY', None)
```

### Custom Environment

If you need specific environment variables, add them to crontab:

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
CODEGEASS_LOG_LEVEL=INFO

* * * * * /path/to/python -m codegeass scheduler run-due
```

## Logging

### CRON Output

Redirect CRON output to a log file:

```cron
* * * * * /path/to/codegeass scheduler run-due >> /var/log/codegeass-cron.log 2>&1
```

### Task Logs

Task execution logs are always stored in `data/logs/`:

```bash
# View recent executions
codegeass logs list

# Tail logs
codegeass logs tail
```

## Verification

### Check CRON is Running

```bash
# View status
codegeass cron status

# Check system CRON logs
grep codegeass /var/log/syslog
# or
journalctl -u cron | grep codegeass
```

### Check Tasks are Being Picked Up

```bash
# View upcoming runs
codegeass scheduler upcoming

# Manually trigger run-due
codegeass scheduler run-due --dry-run
```

### Test a Specific Task

```bash
# Run task manually
codegeass task run my-task

# Check it completed
codegeass logs list --limit 1
```

## Troubleshooting

### Tasks Not Running

**Check CRON is installed:**
```bash
codegeass cron status
crontab -l | grep codegeass
```

**Check task is enabled:**
```bash
codegeass task show my-task
# Look for: enabled: true
```

**Check schedule:**
```bash
codegeass scheduler upcoming
```

**Run manually:**
```bash
codegeass scheduler run-due
```

### Permission Issues

**Ensure directories are writable:**
```bash
ls -la data/
ls -la data/logs/
ls -la data/sessions/
```

**Create if missing:**
```bash
mkdir -p data/logs data/sessions
```

### Path Issues

**CRON can't find codegeass:**
```bash
# Use absolute path in crontab
which codegeass
# Result: /home/user/.local/bin/codegeass

# Update crontab with full path
* * * * * /home/user/.local/bin/codegeass scheduler run-due
```

### Claude CLI Issues

**Claude not found:**
```bash
# Check Claude is installed
claude --version

# Add to PATH in crontab
PATH=/usr/local/bin:/home/user/.local/bin:$PATH
* * * * * codegeass scheduler run-due
```

## Advanced Configuration

### Run Every 5 Minutes

If you don't need minute-level precision:

```cron
*/5 * * * * codegeass scheduler run-due
```

### Multiple Projects

For multiple projects with different configs:

```cron
* * * * * cd /home/user/project1 && codegeass scheduler run-due
* * * * * cd /home/user/project2 && codegeass scheduler run-due
```

### Systemd Alternative

For systemd-based systems, you can use a timer instead of CRON:

```ini
# ~/.config/systemd/user/codegeass.service
[Unit]
Description=CodeGeass Scheduler

[Service]
Type=oneshot
WorkingDirectory=/home/user/myproject
ExecStart=/usr/bin/python -m codegeass scheduler run-due
```

```ini
# ~/.config/systemd/user/codegeass.timer
[Unit]
Description=Run CodeGeass every minute

[Timer]
OnCalendar=*:*:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now codegeass.timer
```

## Maintenance

### Uninstall CRON Job

```bash
codegeass cron uninstall
```

### Disable Temporarily

```bash
# Comment out in crontab
crontab -e
# Add # at beginning of line

# Or disable all tasks
codegeass task list | while read id; do codegeass task disable $id; done
```

### Clean Old Logs

```bash
# View log stats
codegeass logs stats

# Manual cleanup (keep last 30 days)
find data/logs -name "*.jsonl" -mtime +30 -delete
find data/sessions -name "*.json" -mtime +30 -delete
```

## Next Steps

- [Creating Tasks](create-task.md) - Create tasks to schedule
- [Scheduling](../concepts/scheduling.md) - CRON expressions
- [Notifications](setup-notifications.md) - Get alerts when tasks run
