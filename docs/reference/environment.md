# Environment Variables

Complete reference for environment variables used by CodeGeass.

## Configuration Variables

### CODEGEASS_CONFIG_DIR

Override the configuration directory location.

```bash
export CODEGEASS_CONFIG_DIR=/custom/path/config
```

Default: `./config` (relative to current directory)

### CODEGEASS_DATA_DIR

Override the data directory location.

```bash
export CODEGEASS_DATA_DIR=/custom/path/data
```

Default: `./data` (relative to current directory)

### CODEGEASS_LOG_LEVEL

Set logging verbosity.

```bash
export CODEGEASS_LOG_LEVEL=DEBUG
```

Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
Default: `INFO`

### CODEGEASS_CREDENTIALS_FILE

Override credentials file location.

```bash
export CODEGEASS_CREDENTIALS_FILE=/custom/path/credentials.yaml
```

Default: `~/.codegeass/credentials.yaml`

## Claude Configuration

### ANTHROPIC_API_KEY

API key for Anthropic API access.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

!!! warning "CRON Behavior"
    CodeGeass **deliberately unsets** this variable in CRON context to force usage of your Claude Pro/Max subscription instead of API credits.

### CLAUDE_MODEL

Override the default Claude model.

```bash
export CLAUDE_MODEL=claude-3-opus
```

Default: Uses Claude Code's default model

## Notification Variables

### TELEGRAM_BOT_TOKEN

Alternative way to provide Telegram bot token.

```bash
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

Overrides value in `credentials.yaml`.

### TELEGRAM_CHAT_ID

Alternative way to provide Telegram chat ID.

```bash
export TELEGRAM_CHAT_ID=-1001234567890
```

Overrides value in `credentials.yaml`.

### DISCORD_WEBHOOK_URL

Alternative way to provide Discord webhook URL.

```bash
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Overrides value in `credentials.yaml`.

## Path Variables

### PATH

Ensure CRON can find required binaries.

```bash
# In crontab
PATH=/usr/local/bin:/usr/bin:/bin:/home/user/.local/bin
```

### PYTHONPATH

If needed for custom installations.

```bash
export PYTHONPATH=/custom/lib/python
```

## Runtime Variables

These are set automatically during task execution:

### CODEGEASS_TASK_ID

Current task identifier.

```bash
echo $CODEGEASS_TASK_ID
# Output: daily-review
```

### CODEGEASS_EXECUTION_ID

Current execution identifier.

```bash
echo $CODEGEASS_EXECUTION_ID
# Output: abc123
```

### CODEGEASS_WORKING_DIR

Task's working directory.

```bash
echo $CODEGEASS_WORKING_DIR
# Output: /home/user/myproject
```

## CRON Environment

When running via CRON, the environment is minimal. Important settings:

### Recommended CRON Setup

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/home/user/.local/bin
CODEGEASS_LOG_LEVEL=INFO

* * * * * cd /home/user/project && codegeass scheduler run-due
```

### Environment Inheritance

CRON does not inherit your shell environment. To use environment from your profile:

```cron
* * * * * . /home/user/.profile && codegeass scheduler run-due
```

Or source specific files:

```cron
* * * * * . /home/user/.env && codegeass scheduler run-due
```

## Docker Environment

When running in Docker:

```dockerfile
ENV CODEGEASS_CONFIG_DIR=/app/config
ENV CODEGEASS_DATA_DIR=/app/data
ENV CODEGEASS_LOG_LEVEL=INFO
```

```yaml
# docker-compose.yml
services:
  codegeass:
    environment:
      - CODEGEASS_CONFIG_DIR=/app/config
      - CODEGEASS_DATA_DIR=/app/data
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
```

## Priority Order

Settings are loaded in this order (later overrides earlier):

1. Default values
2. Configuration files (`settings.yaml`, etc.)
3. Environment variables
4. Command-line arguments

## Debugging

View current environment:

```bash
# In shell
env | grep CODEGEASS

# What Claude Code sees
claude --print-env
```

Test CRON environment:

```bash
# Add to crontab temporarily
* * * * * env > /tmp/cron-env.txt
```

Then check `/tmp/cron-env.txt` to see what CRON provides.
