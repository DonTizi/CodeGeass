# task

Manage scheduled tasks.

## Usage

```bash
codegeass task [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.task
    :command: task
    :prog_name: codegeass task
    :depth: 1

## Examples

### Create a Task

```bash
# Basic task
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * *" \
  --prompt "Review recent changes"

# With all options
codegeass task create \
  --name full-example \
  --schedule "0 9 * * 1-5" \
  --prompt "Your prompt here" \
  --working-dir /path/to/project \
  --mode autonomous \
  --plan-mode

# Using a different code provider
codegeass task create \
  --name codex-task \
  --schedule "0 9 * * *" \
  --prompt "Review code" \
  --code-source codex
```

### List Tasks

```bash
# List all tasks
codegeass task list

# Show detailed output
codegeass task list --verbose
```

### Show Task Details

```bash
codegeass task show daily-review
```

### Run a Task Manually

```bash
# Run immediately
codegeass task run daily-review

# Run with custom arguments
codegeass task run daily-review --args "Focus on security"
```

### Enable/Disable Tasks

```bash
# Disable a task
codegeass task disable daily-review

# Enable a task
codegeass task enable daily-review
```

### Stop a Running Task

```bash
# Stop a running task execution
codegeass task stop daily-review
```

This gracefully terminates the Claude process (SIGTERM), falling back to SIGKILL if needed. The Dashboard also provides a Stop button for running tasks.

### Delete a Task

```bash
# Delete with confirmation
codegeass task delete old-task

# Delete without confirmation
codegeass task delete old-task --yes
```

## Task Modes

| Mode | Description |
|------|-------------|
| `headless` | Safe, read-only (default) |
| `autonomous` | Full Claude capabilities |
| `skill` | Invoke a predefined skill |

## Schedule Format

Tasks use standard CRON expressions:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6)
│ │ │ │ │
* * * * *
```

Common patterns:
- `0 9 * * *` - Daily at 9 AM
- `0 9 * * 1-5` - Weekdays at 9 AM
- `*/15 * * * *` - Every 15 minutes
- `0 */2 * * *` - Every 2 hours
