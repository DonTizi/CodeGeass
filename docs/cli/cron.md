# cron

CRON job management for the scheduler.

## Usage

```bash
codegeass cron [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.cron
    :command: cron
    :prog_name: codegeass cron
    :depth: 1

## Examples

### Install CRON Job

```bash
# Install the scheduler CRON entry
codegeass cron install
```

This adds an entry to your crontab that runs the scheduler every minute.

### Uninstall CRON Job

```bash
# Remove the scheduler CRON entry
codegeass cron uninstall
```

### View CRON Status

```bash
# Check if CRON is installed
codegeass cron status
```

### View Current CRON Entry

```bash
# Show the crontab entry
crontab -l | grep codegeass
```

## How It Works

The CRON job runs `codegeass scheduler run-due` every minute:

```cron
* * * * * /path/to/python -m codegeass scheduler run-due
```

This:
1. Loads all tasks from `config/schedules.yaml`
2. Checks each task's schedule against the current time
3. Runs any tasks that are due
4. Logs results and sends notifications

## Environment Variables

The CRON job inherits minimal environment. To ensure proper operation:

```bash
# The install command captures the current Python path
# and includes necessary environment variables
codegeass cron install
```

## Troubleshooting

### Tasks Not Running

```bash
# Check CRON is installed
codegeass cron status

# Check system CRON logs
grep codegeass /var/log/syslog

# Manually run due tasks
codegeass scheduler run-due
```

### CRON Path Issues

If the CRON job fails to find `codegeass`:

```bash
# Reinstall with absolute paths
codegeass cron uninstall
codegeass cron install
```

### Permission Issues

CRON runs as your user. Ensure:
- The codegeass installation is accessible
- Configuration files are readable
- Log directories are writable

## Related

- [`scheduler`](scheduler.md) - View upcoming runs
- [CRON Setup Guide](../guides/cron-setup.md) - Detailed setup
