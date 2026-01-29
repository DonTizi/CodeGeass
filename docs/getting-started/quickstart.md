# Quick Start

Create your first automated Claude task in 5 minutes.

## Step 1: Create a Task

Create a simple task that runs daily:

```bash
codegeass task create \
  --name hello-world \
  --schedule "0 9 * * *" \
  --prompt "Say hello and tell me today's date"
```

This creates a task named `hello-world` that runs at 9 AM every day.

## Step 2: View Your Task

```bash
# List all tasks
codegeass task list

# Show task details
codegeass task show hello-world
```

## Step 3: Run Manually

Test your task without waiting for the schedule:

```bash
codegeass task run hello-world
```

!!! tip "Working Directory"
    By default, tasks run in the current directory. Use `--working-dir` to specify a different location.

## Step 4: Check Results

View execution logs:

```bash
# List recent executions
codegeass logs list

# Show detailed log
codegeass logs show <execution-id>

# Follow logs in real-time
codegeass logs tail
```

## Step 5: Enable Scheduling

Install the CRON job to run tasks automatically:

```bash
# Install scheduler
codegeass cron install

# Check upcoming runs
codegeass scheduler upcoming

# View scheduler status
codegeass scheduler status
```

## A Real-World Example

Here's a more practical task - daily code review:

```bash
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * 1-5" \
  --prompt "Review commits from the last 24 hours. Summarize changes and flag any potential issues." \
  --working-dir /path/to/your/project \
  --mode autonomous
```

!!! warning "Autonomous Mode"
    The `--mode autonomous` flag allows Claude to make file changes. Use with caution and only on trusted projects.

## Task Options

| Option | Description |
|--------|-------------|
| `--name` | Unique task identifier |
| `--schedule` | CRON expression (e.g., `0 9 * * *`) |
| `--prompt` | Instructions for Claude |
| `--working-dir` | Directory to run in |
| `--mode` | Execution mode: `headless`, `autonomous`, `skill` |
| `--skill` | Skill to invoke (for skill mode) |

## Next Steps

- [Configuration](configuration.md) - Learn about config files
- [Tasks](../concepts/tasks.md) - Deep dive into tasks
- [Scheduling](../concepts/scheduling.md) - CRON expression guide
- [Notifications](../guides/setup-notifications.md) - Get notified when tasks complete
