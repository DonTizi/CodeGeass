# Scheduling

CodeGeass uses CRON expressions to schedule tasks. This guide explains CRON syntax and scheduling options.

## CRON Basics

A CRON expression has five fields:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

## Common Patterns

| Expression | Description |
|------------|-------------|
| `0 9 * * *` | Every day at 9:00 AM |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `*/15 * * * *` | Every 15 minutes |
| `0 */2 * * *` | Every 2 hours |
| `0 9 1 * *` | First day of each month at 9:00 AM |
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `30 8 * * 1-5` | Weekdays at 8:30 AM |

## Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` = every minute |
| `,` | List | `0 9,17 * * *` = 9 AM and 5 PM |
| `-` | Range | `0 9 * * 1-5` = Mon-Fri |
| `/` | Step | `*/15 * * * *` = every 15 min |

## Examples

### Development Tasks

```bash
# Run tests every hour during work hours
codegeass task create \
  --name hourly-tests \
  --schedule "0 9-17 * * 1-5" \
  --prompt "Run the test suite and report failures"

# Daily code quality check at 6 AM
codegeass task create \
  --name quality-check \
  --schedule "0 6 * * *" \
  --prompt "Run linting and type checking, report issues"
```

### Reporting Tasks

```bash
# Weekly summary every Monday at 10 AM
codegeass task create \
  --name weekly-summary \
  --schedule "0 10 * * 1" \
  --prompt "Generate a weekly summary of project activity"

# Monthly report on the 1st at 9 AM
codegeass task create \
  --name monthly-report \
  --schedule "0 9 1 * *" \
  --prompt "Generate a monthly project status report"
```

### Maintenance Tasks

```bash
# Nightly dependency check at 2 AM
codegeass task create \
  --name dep-check \
  --schedule "0 2 * * *" \
  --prompt "Check for outdated dependencies and security issues"

# Sunday night cleanup at 11 PM
codegeass task create \
  --name cleanup \
  --schedule "0 23 * * 0" \
  --prompt "Clean up temporary files and old branches"
```

## Viewing Schedules

```bash
# See upcoming runs for all tasks
codegeass scheduler upcoming

# See next run for a specific task
codegeass task show my-task
```

## Installing the Scheduler

The scheduler runs as a CRON job that checks for due tasks:

```bash
# Install the CRON job
codegeass cron install

# Check status
codegeass scheduler status

# View the CRON entry
crontab -l | grep codegeass
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    System CRON                          │
│                                                         │
│  * * * * * /path/to/codegeass scheduler run-due         │
└─────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────┐
│                   CodeGeass Scheduler                   │
│                                                         │
│  1. Load tasks from config/schedules.yaml               │
│  2. Check which tasks are due                           │
│  3. Execute due tasks                                   │
│  4. Log results                                         │
└─────────────────────────────────────────────────────────┘
```

## Time Zones

CRON uses system time. To check your system timezone:

```bash
timedatectl show --property=Timezone
```

!!! tip "UTC for Servers"
    For servers, consider using UTC to avoid daylight saving time issues.

## Best Practices

1. **Stagger schedules** - Don't run all tasks at the same time
2. **Use work hours** - Schedule interactive tasks during your active hours
3. **Consider timezones** - Be aware of when tasks will actually run
4. **Test manually** - Always test with `codegeass task run` before scheduling
5. **Monitor executions** - Check `codegeass logs list` regularly

## Troubleshooting

### Task Not Running

```bash
# Check if scheduler is installed
codegeass scheduler status

# Check if task is enabled
codegeass task show my-task

# Check CRON logs
grep codegeass /var/log/syslog
```

### Wrong Time

```bash
# Check system time
date

# Check timezone
timedatectl

# Verify CRON expression
codegeass scheduler upcoming
```

## Related

- [Tasks](tasks.md) - Creating and managing tasks
- [CLI Reference](../cli/scheduler.md) - Scheduler commands
- [CRON Setup Guide](../guides/cron-setup.md) - Detailed setup instructions
