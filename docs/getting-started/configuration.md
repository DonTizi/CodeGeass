# Configuration

CodeGeass uses YAML files for configuration. This guide explains all configuration options.

## Configuration Files

```
./config/                     # Project configuration
├── schedules.yaml            # Task definitions
├── settings.yaml             # Project settings
└── notifications.yaml        # Notification channels

~/.codegeass/                 # Global user configuration
└── credentials.yaml          # Secrets (API keys, tokens)
```

## schedules.yaml

Defines all scheduled tasks:

```yaml
tasks:
  - id: daily-review
    name: Daily Code Review
    schedule: "0 9 * * 1-5"
    prompt: "Review commits from the last 24 hours"
    working_dir: /home/user/project
    enabled: true
    mode: headless

  - id: weekly-report
    name: Weekly Summary
    schedule: "0 10 * * 1"
    prompt: "Generate a weekly summary of project activity"
    enabled: true
    mode: autonomous
```

### Task Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique task identifier |
| `name` | string | No | Human-readable name |
| `schedule` | string | Yes | CRON expression |
| `prompt` | string | Yes* | Instructions for Claude |
| `skill` | string | Yes* | Skill to invoke (if using skill mode) |
| `working_dir` | string | No | Directory to run in |
| `enabled` | bool | No | Whether task is active (default: true) |
| `mode` | string | No | Execution mode (default: headless) |
| `plan_mode` | bool | No | Enable plan mode for approval workflow |

*Either `prompt` or `skill` is required, not both.

## settings.yaml

Project-wide settings:

```yaml
# Default working directory for tasks
default_working_dir: /home/user/project

# Default execution mode
default_mode: headless

# Logging settings
logging:
  level: INFO
  format: json

# Session settings
sessions:
  retention_days: 30
  max_sessions: 1000

# Plan mode settings
plan_mode:
  default_timeout: 3600  # seconds
  auto_approve: false
```

## notifications.yaml

Notification channel configuration:

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
```

!!! note "Secrets Storage"
    API keys and tokens are stored in `~/.codegeass/credentials.yaml`, not in the project config.

## credentials.yaml

Global secrets file (never commit this):

```yaml
# Telegram Bot
telegram:
  bot_token: "123456:ABC-DEF..."
  chat_id: "-1001234567890"

# Discord Webhook
discord:
  webhook_url: "https://discord.com/api/webhooks/..."
```

Set restrictive permissions:

```bash
chmod 600 ~/.codegeass/credentials.yaml
```

## Environment Variables

Settings can be overridden with environment variables:

| Variable | Description |
|----------|-------------|
| `CODEGEASS_CONFIG_DIR` | Override config directory |
| `CODEGEASS_DATA_DIR` | Override data directory |
| `CODEGEASS_LOG_LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |

## Validation

Validate your configuration:

```bash
# Validate task configuration
codegeass task list

# Validate skill files
codegeass skill validate .claude/skills/my-skill/SKILL.md

# Check notification setup
codegeass notification list
```

## Next Steps

- [Tasks](../concepts/tasks.md) - Learn about task configuration
- [Skills](../concepts/skills.md) - Create reusable skills
- [Notifications](../concepts/notifications.md) - Set up notifications
