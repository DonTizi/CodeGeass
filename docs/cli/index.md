# CLI Reference

CodeGeass provides a comprehensive command-line interface for managing scheduled Claude tasks.

## Overview

```bash
codegeass [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

## Commands

| Command | Description |
|---------|-------------|
| [`task`](task.md) | Manage scheduled tasks |
| [`skill`](skill.md) | Manage skills |
| [`project`](project.md) | Manage multiple projects |
| [`provider`](provider.md) | Manage code execution providers |
| [`scheduler`](scheduler.md) | Scheduler operations |
| [`logs`](logs.md) | View execution logs |
| [`notification`](notification.md) | Manage notifications |
| [`approval`](approval.md) | Manage plan mode approvals |
| [`cron`](cron.md) | CRON job management |
| [`execution`](execution.md) | Manage task executions |

## Quick Examples

### Task Management

```bash
# Create a task
codegeass task create --name my-task --schedule "0 9 * * *" --prompt "Do something"

# List tasks
codegeass task list

# Run a task manually
codegeass task run my-task

# Stop a running task
codegeass task stop my-task

# Enable/disable a task
codegeass task enable my-task
codegeass task disable my-task
```

### Scheduling

```bash
# Install CRON job
codegeass cron install

# View upcoming runs
codegeass scheduler upcoming

# Check scheduler status
codegeass scheduler status
```

### Logs

```bash
# List recent executions
codegeass logs list

# Show execution details
codegeass logs show <execution-id>

# Follow logs in real-time
codegeass logs tail
```

### Projects

```bash
# Register a project
codegeass project add /path/to/project --name my-project

# List projects
codegeass project list

# Set default project
codegeass project set-default my-project

# Initialize new project
codegeass project init /path/to/new-project
```

### Notifications

```bash
# Add Telegram notification
codegeass notification add telegram --bot-token "..." --chat-id "..."

# Test notification
codegeass notification test telegram

# List channels
codegeass notification list
```

## Getting Help

Each command has built-in help:

```bash
# Top-level help
codegeass --help

# Command help
codegeass task --help

# Subcommand help
codegeass task create --help
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
