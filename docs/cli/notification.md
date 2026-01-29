# notification

Manage notification channels for task alerts.

## Usage

```bash
codegeass notification [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.notification
    :command: notification
    :prog_name: codegeass notification
    :depth: 1

## Examples

### List Channels

```bash
# List all notification channels
codegeass notification list
```

### List Providers

```bash
# Show available providers
codegeass notification providers
```

### Add a Channel

```bash
# Add Telegram
codegeass notification add telegram \
  --bot-token "123456:ABC-DEF..." \
  --chat-id "-1001234567890"

# Add Discord
codegeass notification add discord \
  --webhook-url "https://discord.com/api/webhooks/..."
```

### Show Channel Details

```bash
codegeass notification show telegram-main
```

### Test a Channel

```bash
# Send test notification
codegeass notification test telegram-main
```

### Enable/Disable

```bash
# Disable notifications
codegeass notification disable telegram-main

# Re-enable
codegeass notification enable telegram-main
```

### Remove a Channel

```bash
codegeass notification remove telegram-main
```

## Providers

### Telegram

Required credentials:
- `bot_token` - Bot token from @BotFather
- `chat_id` - Chat ID (positive for private, negative for groups)

```bash
codegeass notification add telegram \
  --bot-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID"
```

### Discord

Required credentials:
- `webhook_url` - Discord webhook URL

```bash
codegeass notification add discord \
  --webhook-url "YOUR_WEBHOOK_URL"
```

## Event Types

Configure which events trigger notifications:

| Event | Description |
|-------|-------------|
| `task_completed` | Task finished successfully |
| `task_failed` | Task failed with error |
| `approval_required` | Plan mode needs approval |
| `approval_timeout` | Approval window expired |

## Configuration Files

Channels are stored in `config/notifications.yaml`:

```yaml
channels:
  - id: telegram-main
    provider: telegram
    enabled: true
    events:
      - task_completed
      - task_failed
```

Credentials are stored in `~/.codegeass/credentials.yaml`:

```yaml
telegram:
  bot_token: "..."
  chat_id: "..."
```

## Related

- [Notifications Concept](../concepts/notifications.md)
- [Setup Guide](../guides/setup-notifications.md)
