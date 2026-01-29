# Notifications

CodeGeass can notify you via Telegram or Discord when tasks complete, fail, or need approval.

## Overview

Notifications keep you informed about:

- **Task completion** - Know when tasks finish successfully
- **Task failures** - Alert on errors or exceptions
- **Approval requests** - Plan mode tasks waiting for approval

## Supported Providers

| Provider | Events Supported | Interactive |
|----------|-----------------|-------------|
| Telegram | All | Yes (approve/reject via bot) |
| Discord | All | No (webhook only) |

## Quick Setup

### Telegram

```bash
# Add Telegram channel
codegeass notification add telegram \
  --bot-token "123456:ABC-DEF..." \
  --chat-id "-1001234567890"

# Test the connection
codegeass notification test telegram
```

### Discord

```bash
# Add Discord webhook
codegeass notification add discord \
  --webhook-url "https://discord.com/api/webhooks/..."

# Test the connection
codegeass notification test discord
```

## Configuration

### Channel Configuration

Channels are defined in `config/notifications.yaml`:

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

### Credentials

Secrets are stored in `~/.codegeass/credentials.yaml`:

```yaml
telegram:
  bot_token: "123456:ABC-DEF..."
  chat_id: "-1001234567890"

discord:
  webhook_url: "https://discord.com/api/webhooks/..."
```

!!! warning "Security"
    Set restrictive permissions: `chmod 600 ~/.codegeass/credentials.yaml`

## Event Types

| Event | Description | Data Included |
|-------|-------------|---------------|
| `task_completed` | Task finished successfully | Task name, duration, summary |
| `task_failed` | Task failed with error | Task name, error message |
| `approval_required` | Plan mode task needs approval | Task name, plan summary |
| `approval_timeout` | Approval window expired | Task name |

## Managing Notifications

```bash
# List all channels
codegeass notification list

# Show channel details
codegeass notification show telegram-main

# Enable/disable a channel
codegeass notification enable telegram-main
codegeass notification disable discord-alerts

# Remove a channel
codegeass notification remove telegram-main
```

## Provider Details

### Telegram Setup

1. **Create a bot** via [@BotFather](https://t.me/botfather)
2. **Get the bot token** from BotFather
3. **Get your chat ID**:
   - Add the bot to your group/channel
   - Send a message
   - Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find the `chat.id` in the response

```bash
codegeass notification add telegram \
  --bot-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID"
```

!!! tip "Private vs Group"
    - Private chat: positive chat ID (e.g., `123456789`)
    - Group/channel: negative chat ID (e.g., `-1001234567890`)

### Discord Setup

1. **Go to channel settings** → Integrations → Webhooks
2. **Create a new webhook**
3. **Copy the webhook URL**

```bash
codegeass notification add discord \
  --webhook-url "YOUR_WEBHOOK_URL"
```

## Message Examples

### Task Completed (Telegram)

```
✅ Task Completed: daily-review

Duration: 2m 34s
Summary: Reviewed 15 commits, found 2 potential issues

View logs: codegeass logs show abc123
```

### Task Failed (Discord)

```
❌ Task Failed: weekly-report

Error: Claude process exited with code 1
Details: Permission denied accessing /protected/file

View logs: codegeass logs show def456
```

### Approval Required (Telegram)

```
🔔 Approval Required: upgrade-deps

Plan Summary:
1. Upgrade react from 17.0.2 to 18.2.0
2. Update react-dom to match
3. Run tests to verify compatibility

[Approve] [Reject]
```

## Best Practices

1. **Separate channels** - Use different channels for different severity levels
2. **Enable only needed events** - Reduce noise
3. **Test before production** - Use `codegeass notification test`
4. **Secure credentials** - Restrict file permissions
5. **Monitor delivery** - Check notification logs

## Troubleshooting

### Notifications Not Sending

```bash
# Test the provider
codegeass notification test telegram

# Check channel is enabled
codegeass notification show telegram-main

# Verify credentials
cat ~/.codegeass/credentials.yaml
```

### Telegram Bot Issues

- Ensure bot is added to the chat
- Check bot has permission to send messages
- Verify chat ID is correct (positive for private, negative for groups)

### Discord Webhook Issues

- Verify webhook URL is complete and correct
- Check webhook hasn't been deleted
- Test webhook directly with curl

## Related

- [Setup Guide](../guides/setup-notifications.md) - Detailed setup instructions
- [Plan Mode](plan-mode.md) - Approval notifications
- [CLI Reference](../cli/notification.md) - Notification commands
