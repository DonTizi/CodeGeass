# Quick Start

Get CodeGeass running and create your first task.

## Step 1: Install CodeGeass

```bash
# macOS
brew install pipx && pipx ensurepath
source ~/.zshrc

# Linux
python3 -m pip install --user pipx && pipx ensurepath
source ~/.bashrc

# Install CodeGeass
pipx install codegeass
```

## Step 2: Setup the Scheduler

Run the setup command to install the 24/7 background scheduler:

```bash
codegeass setup
```

This automatically detects your OS and installs:
- **macOS**: launchd service
- **Linux**: systemd user timer

The scheduler runs every minute and executes any due tasks.

## Step 3: Create Your First Task

Create a simple task that runs daily:

```bash
codegeass task create \
  --name hello-world \
  --schedule "0 9 * * *" \
  --prompt "Say hello and tell me today's date"
```

This creates a task named `hello-world` that runs at 9 AM every day.

## Step 4: View Your Task

```bash
# List all tasks
codegeass task list

# Show task details
codegeass task show hello-world
```

## Step 5: Run Manually

Test your task without waiting for the schedule:

```bash
codegeass task run hello-world
```

!!! tip "Working Directory"
    By default, tasks run in the current directory. Use `--working-dir` to specify a different location.

## Step 6: Check Results

View execution logs:

```bash
# List recent executions
codegeass logs list

# Show detailed log
codegeass logs show <execution-id>

# Follow logs in real-time
codegeass logs tail
```

## Step 7: Verify Scheduling

The scheduler is already running from `codegeass setup`. Verify it:

```bash
# Check upcoming runs
codegeass scheduler upcoming

# View scheduler status
codegeass scheduler status

# Check scheduler is running
# macOS
launchctl list | grep codegeass

# Linux
systemctl --user status codegeass-scheduler.timer
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

## Working with Multiple Projects

If you work on multiple codebases, you can register them with CodeGeass:

```bash
# Register your projects
codegeass project add ~/projects/api-server --name api
codegeass project add ~/projects/web-app --name web
codegeass project add ~/projects/mobile-app --name mobile

# Set a default
codegeass project set-default api

# List registered projects
codegeass project list

# Run tasks against specific projects
codegeass --project web task run daily-review
```

!!! tip "Shared Skills"
    Place commonly-used skills in `~/.codegeass/skills/` to make them available across all your projects.

## Open the Dashboard

CodeGeass includes a web dashboard for visual management:

```bash
codegeass dashboard
```

Then open http://localhost:8001 in your browser.

## Next Steps

- [Configuration](configuration.md) - Learn about config files
- [Projects](../concepts/projects.md) - Multi-project support
- [Tasks](../concepts/tasks.md) - Deep dive into tasks
- [Scheduling](../concepts/scheduling.md) - CRON expression guide
- [Notifications](../guides/setup-notifications.md) - Get notified when tasks complete
