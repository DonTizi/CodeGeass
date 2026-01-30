# Configuration Files

Complete reference for all CodeGeass configuration files.

## File Locations

```
./config/                     # Project configuration
├── schedules.yaml            # Task definitions
├── settings.yaml             # Project settings
└── notifications.yaml        # Notification channels

~/.codegeass/                 # Global user configuration
├── projects.yaml             # Project registry (multi-project)
├── credentials.yaml          # Secrets (API keys, tokens)
└── skills/                   # Shared skills (all projects)

./data/                       # Runtime data (gitignored)
├── logs/                     # Execution logs (JSONL)
└── sessions/                 # Claude session data
```

## schedules.yaml

Task definitions file.

### Schema

```yaml
tasks:
  - id: string              # Required: Unique identifier
    name: string            # Optional: Human-readable name
    schedule: string        # Required: CRON expression
    prompt: string          # Required*: Instructions for Claude
    skill: string           # Required*: Skill name (if using skill mode)
    skill_args: string      # Optional: Arguments for skill
    working_dir: string     # Optional: Directory to run in
    enabled: bool           # Optional: Whether active (default: true)
    mode: string            # Optional: headless|autonomous|skill
    plan_mode: bool         # Optional: Enable approval workflow
    timeout: int            # Optional: Execution timeout (seconds)
```

*Either `prompt` or `skill` is required, not both.

### Example

```yaml
tasks:
  - id: daily-review
    name: Daily Code Review
    schedule: "0 9 * * 1-5"
    prompt: |
      Review commits from the last 24 hours.
      Focus on:
      - Code quality
      - Potential bugs
      - Security issues
    working_dir: /home/user/myproject
    enabled: true
    mode: headless

  - id: weekly-cleanup
    name: Weekly Cleanup
    schedule: "0 6 * * 6"
    prompt: "Clean up unused imports and fix linting issues"
    mode: autonomous
    plan_mode: true
    timeout: 1800

  - id: skill-based-task
    name: Skill Task
    schedule: "0 10 * * *"
    skill: review
    skill_args: "Check the API module"
    mode: skill
```

### Task Modes

| Mode | Description |
|------|-------------|
| `headless` | Read-only, uses `claude -p` |
| `autonomous` | Full access, uses `--dangerously-skip-permissions` |
| `skill` | Invokes a skill from `.claude/skills/` |

## settings.yaml

Project-wide settings.

### Schema

```yaml
# Working directory default
default_working_dir: string

# Default execution mode
default_mode: string

# Logging configuration
logging:
  level: string             # DEBUG|INFO|WARNING|ERROR
  format: string            # json|text

# Session management
sessions:
  retention_days: int       # Days to keep sessions
  max_sessions: int         # Maximum sessions to retain

# Plan mode defaults
plan_mode:
  default_timeout: int      # Approval timeout (seconds)
  auto_approve: bool        # Skip approval (not recommended)

# Scheduler settings
scheduler:
  check_interval: int       # Seconds between checks
  max_concurrent: int       # Max concurrent executions
```

### Example

```yaml
default_working_dir: /home/user/myproject
default_mode: headless

logging:
  level: INFO
  format: json

sessions:
  retention_days: 30
  max_sessions: 1000

plan_mode:
  default_timeout: 3600
  auto_approve: false

scheduler:
  check_interval: 60
  max_concurrent: 3
```

## notifications.yaml

Notification channel configuration.

### Schema

```yaml
channels:
  - id: string              # Required: Unique identifier
    provider: string        # Required: telegram|discord
    enabled: bool           # Optional: Whether active (default: true)
    events:                 # Optional: Events to notify on
      - string              # task_completed|task_failed|approval_required|approval_timeout
```

### Example

```yaml
channels:
  - id: telegram-main
    provider: telegram
    enabled: true
    events:
      - task_completed
      - task_failed
      - approval_required

  - id: discord-alerts
    provider: discord
    enabled: true
    events:
      - task_failed

  - id: telegram-approvals
    provider: telegram
    enabled: true
    events:
      - approval_required
      - approval_timeout
```

### Event Types

| Event | When Triggered |
|-------|----------------|
| `task_completed` | Task finished successfully |
| `task_failed` | Task failed with error |
| `approval_required` | Plan mode task needs approval |
| `approval_timeout` | Approval window expired |

## credentials.yaml

Secrets file (global, never commit).

### Location

```
~/.codegeass/credentials.yaml
```

### Schema

```yaml
telegram:
  bot_token: string         # Telegram bot token
  chat_id: string           # Telegram chat ID

discord:
  webhook_url: string       # Discord webhook URL
```

### Example

```yaml
telegram:
  bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  chat_id: "-1001234567890"

discord:
  webhook_url: "https://discord.com/api/webhooks/1234567890/abcdefghijk..."
```

### Security

Set restrictive permissions:

```bash
chmod 600 ~/.codegeass/credentials.yaml
```

## Log Files

### Location

```
./data/logs/*.jsonl
```

### Format (JSONL)

Each line is a JSON object:

```json
{"id": "abc123", "task_id": "daily-review", "started_at": "2024-01-15T09:00:00Z", "completed_at": "2024-01-15T09:05:23Z", "status": "completed", "exit_code": 0, "mode": "headless"}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Execution ID |
| `task_id` | string | Task that was run |
| `started_at` | datetime | Start time (ISO 8601) |
| `completed_at` | datetime | End time (ISO 8601) |
| `status` | string | Status (see below) |
| `exit_code` | int | Claude exit code |
| `mode` | string | Execution mode used |
| `error` | string | Error message (if failed) |

### Status Values

| Status | Description |
|--------|-------------|
| `running` | Currently executing |
| `completed` | Finished successfully |
| `failed` | Failed with error |
| `waiting_approval` | Plan mode awaiting approval |
| `approved` | Plan approved, continuing |
| `rejected` | Plan rejected |
| `timeout` | Execution or approval timed out |

## Session Files

### Location

```
./data/sessions/<execution-id>.json
```

### Format

```json
{
  "id": "abc123",
  "task_id": "daily-review",
  "started_at": "2024-01-15T09:00:00Z",
  "completed_at": "2024-01-15T09:05:23Z",
  "status": "completed",
  "mode": "headless",
  "working_dir": "/home/user/myproject",
  "output": "Claude's full response...",
  "tool_calls": [
    {
      "tool": "Read",
      "input": {"file": "src/main.py"},
      "output": "..."
    }
  ],
  "duration_seconds": 323,
  "exit_code": 0
}
```

## projects.yaml

Global project registry for multi-project mode.

### Location

```
~/.codegeass/projects.yaml
```

### Schema

```yaml
version: int                  # Schema version (currently 1)
default_project: string       # ID of default project
shared_skills_dir: string     # Path to shared skills directory

projects:
  - id: string                # Required: Unique project ID (auto-generated)
    name: string              # Required: Human-readable name
    path: string              # Required: Absolute path to project
    description: string       # Optional: Project description
    default_model: string     # Optional: Default Claude model (haiku|sonnet|opus)
    default_timeout: int      # Optional: Default timeout in seconds
    default_autonomous: bool  # Optional: Enable autonomous mode by default
    git_remote: string        # Optional: Git remote URL (auto-detected)
    enabled: bool             # Optional: Whether project is active (default: true)
    use_shared_skills: bool   # Optional: Include shared skills (default: true)
    created_at: string        # Optional: ISO 8601 timestamp
```

### Example

```yaml
version: 1
default_project: a1b2c3d4
shared_skills_dir: ~/.codegeass/skills
projects:
  - id: a1b2c3d4
    name: api-server
    path: /home/user/projects/api-server
    description: "REST API backend"
    default_model: sonnet
    default_timeout: 300
    default_autonomous: false
    git_remote: https://github.com/user/api-server
    enabled: true
    use_shared_skills: true
    created_at: "2024-01-15T09:00:00Z"

  - id: e5f6g7h8
    name: web-frontend
    path: /home/user/projects/web-frontend
    description: "React web application"
    default_model: haiku
    default_timeout: 180
    enabled: true
    use_shared_skills: true
    created_at: "2024-01-20T14:30:00Z"
```

### Management

This file is managed by CLI commands:

```bash
# Add a project
codegeass project add /path/to/project --name my-project

# Remove a project
codegeass project remove my-project

# Update settings
codegeass project update my-project --model opus --timeout 600

# Set default
codegeass project set-default my-project
```

## Validation

Validate configuration files:

```bash
# Validate tasks
codegeass task list

# Validate skills
codegeass skill validate --all

# Validate projects
codegeass project list

# Test notifications
codegeass notification test telegram
```
