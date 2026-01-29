# scheduler

Scheduler operations - view status and run due tasks.

## Usage

```bash
codegeass scheduler [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.scheduler
    :command: scheduler
    :prog_name: codegeass scheduler
    :depth: 1

## Examples

### View Status

```bash
# Check scheduler status
codegeass scheduler status
```

### View Upcoming Runs

```bash
# Show next 10 scheduled runs
codegeass scheduler upcoming

# Show more runs
codegeass scheduler upcoming --limit 20
```

### Run Due Tasks

```bash
# Run all tasks that are due
codegeass scheduler run-due

# Dry run - show what would run
codegeass scheduler run-due --dry-run
```

### Run Scheduler Once

```bash
# Run the scheduler loop once
codegeass scheduler run
```

## How the Scheduler Works

The scheduler is designed to run periodically via CRON:

```
┌─────────────────────────────────────────────────────────┐
│                    System CRON                          │
│  * * * * * /path/to/codegeass scheduler run-due         │
└─────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────┐
│                   run-due Command                       │
│                                                         │
│  1. Load tasks from config/schedules.yaml               │
│  2. Check which tasks are due (based on CRON schedule)  │
│  3. Execute each due task                               │
│  4. Log results                                         │
│  5. Send notifications                                  │
└─────────────────────────────────────────────────────────┘
```

## Integration with CRON

Install the scheduler CRON job:

```bash
# Install CRON entry
codegeass cron install

# View installed entry
crontab -l | grep codegeass
```

The CRON job runs every minute and checks for due tasks.

## Related Commands

- [`cron`](cron.md) - Install/manage the CRON job
- [`task`](task.md) - Manage individual tasks
- [`logs`](logs.md) - View execution logs
