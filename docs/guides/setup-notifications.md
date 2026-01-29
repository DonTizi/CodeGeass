# Setting Up Notifications

This guide walks through configuring Telegram and Discord notifications for CodeGeass.

## Overview

Notifications alert you when:
- Tasks complete successfully
- Tasks fail with errors
- Plan mode tasks need approval

## Telegram Setup

### Step 1: Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Choose a name (e.g., "CodeGeass Notifications")
4. Choose a username (e.g., "myproject_codegeass_bot")
5. Save the **bot token** (format: `123456:ABC-DEF...`)

### Step 2: Get Your Chat ID

**For private chats:**

1. Start a conversation with your bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find `"chat":{"id":123456789}` in the response

**For groups/channels:**

1. Add your bot to the group
2. Send a message in the group
3. Visit the same URL above
4. The chat ID will be negative (e.g., `-1001234567890`)

### Step 3: Add to CodeGeass

```bash
codegeass notification add telegram \
  --bot-token "123456:ABC-DEF..." \
  --chat-id "-1001234567890"
```

### Step 4: Test

```bash
codegeass notification test telegram
```

You should receive a test message in Telegram.

## Discord Setup

### Step 1: Create a Webhook

1. Open Discord and go to your server
2. Right-click the channel → **Edit Channel**
3. Go to **Integrations** → **Webhooks**
4. Click **New Webhook**
5. Name it (e.g., "CodeGeass")
6. Copy the **Webhook URL**

### Step 2: Add to CodeGeass

```bash
codegeass notification add discord \
  --webhook-url "https://discord.com/api/webhooks/..."
```

### Step 3: Test

```bash
codegeass notification test discord
```

You should see a test message in the Discord channel.

## Configuring Events

By default, channels receive all events. Customize in `config/notifications.yaml`:

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
      - task_failed  # Only failures
```

### Available Events

| Event | Description |
|-------|-------------|
| `task_completed` | Task finished successfully |
| `task_failed` | Task failed with error |
| `approval_required` | Plan mode needs approval |
| `approval_timeout` | Approval window expired |

## Multiple Channels

You can configure multiple channels for different purposes:

```yaml
channels:
  # Personal notifications - everything
  - id: telegram-personal
    provider: telegram
    enabled: true
    events:
      - task_completed
      - task_failed
      - approval_required

  # Team channel - only failures
  - id: discord-team
    provider: discord
    enabled: true
    events:
      - task_failed

  # Ops channel - approvals only
  - id: telegram-ops
    provider: telegram
    enabled: true
    events:
      - approval_required
```

## Managing Channels

```bash
# List all channels
codegeass notification list

# Show channel details
codegeass notification show telegram-main

# Disable temporarily
codegeass notification disable telegram-main

# Re-enable
codegeass notification enable telegram-main

# Remove permanently
codegeass notification remove discord-alerts
```

## Credentials Security

Credentials are stored separately from channel config:

```bash
# Channel config (safe to commit)
cat config/notifications.yaml

# Credentials (never commit!)
cat ~/.codegeass/credentials.yaml
```

Set proper permissions:

```bash
chmod 600 ~/.codegeass/credentials.yaml
```

## Troubleshooting

### Telegram Issues

**"Chat not found" error:**
- Ensure the bot is added to the chat
- For groups, make sure the bot has permission to send messages
- Verify the chat ID is correct (negative for groups)

**"Unauthorized" error:**
- Check the bot token is correct
- Regenerate the token via @BotFather if needed

### Discord Issues

**"Invalid webhook" error:**
- Verify the webhook URL is complete
- Check the webhook hasn't been deleted

**Messages not appearing:**
- Check the channel permissions
- Verify the webhook is for the correct channel

### General Issues

```bash
# Test connection
codegeass notification test telegram

# Check configuration
codegeass notification show telegram-main

# View logs for errors
codegeass logs list --status failed
```

## Best Practices

1. **Separate channels** - Use different channels for different severity
2. **Limit events** - Only subscribe to events you care about
3. **Test after setup** - Always verify with test command
4. **Secure credentials** - Never commit tokens/webhooks
5. **Monitor delivery** - Check notifications are arriving

## Next Steps

- [Plan Mode](../concepts/plan-mode.md) - Interactive approvals via Telegram
- [Tasks](../concepts/tasks.md) - Create tasks that send notifications
- [CLI Reference](../cli/notification.md) - Full command reference
