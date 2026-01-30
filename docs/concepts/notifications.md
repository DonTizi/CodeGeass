# Notifications

CodeGeass can notify you via Telegram, Discord, or Microsoft Teams when tasks complete, fail, or need approval.

## Overview

Notifications keep you informed about:

- **Task completion** - Know when tasks finish successfully
- **Task failures** - Alert on errors or exceptions
- **Approval requests** - Plan mode tasks waiting for approval

## Supported Providers

| Provider | Events Supported | Interactive | Approval Flow |
|----------|-----------------|-------------|---------------|
| Telegram | All | Yes (approve/reject via bot) | Inline buttons |
| Discord | All | No (webhook only) | Dashboard link |
| Teams | All | Yes (via Dashboard) | Dashboard buttons |

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

### Microsoft Teams

```bash
# Add Teams Workflows webhook
codegeass notification add teams \
  --webhook-url "https://prod-XX.westus.logic.azure.com/workflows/..."

# Test the connection
codegeass notification test teams
```

!!! note "Teams Webhooks"
    Teams uses Power Automate Workflows webhooks (O365 Connectors were retired Dec 2025).
    Create one via: Apps tab → Workflows → "Post to a channel when a webhook request is received"

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

### Microsoft Teams Setup

Teams uses Power Automate Workflows webhooks (O365 Connectors were deprecated in December 2025).

1. **Open your Teams channel**
2. **Click ⋯ (three dots)** → **Workflows**
3. **Search for** "Post to a channel when a webhook request is received"
4. **Click Add** and configure the workflow
5. **Copy the HTTP POST URL** (starts with `https://prod-XX.westus.logic.azure.com/workflows/...`)

```bash
codegeass notification add teams \
  --webhook-url "YOUR_WORKFLOW_URL"
```

!!! tip "Supported URL Formats"
    - Power Automate: `https://*.logic.azure.com/workflows/...`
    - Power Platform: `https://*.api.powerplatform.com/workflows/...`
    - Legacy O365 (deprecated): `https://*.webhook.office.com/webhookb2/...`

!!! info "Plan Mode Approvals"
    Teams doesn't support inline callback buttons, so approval actions link to the
    CodeGeass Dashboard. When you receive a plan approval notification, click the
    Approve/Discuss/Cancel buttons to open the Dashboard where you can take action.

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
