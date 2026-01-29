# Troubleshooting

Solutions to common issues with CodeGeass.

## Installation Issues

### "codegeass: command not found"

**Cause:** CodeGeass not in PATH.

**Solution:**
```bash
# Check installation
pip show codegeass

# Install if missing
pip install codegeass

# Or add to PATH
export PATH=$PATH:~/.local/bin
```

### Import Errors

**Cause:** Missing dependencies.

**Solution:**
```bash
pip install codegeass[notifications]  # For Telegram/Discord
pip install codegeass[docs]           # For documentation
```

## Task Issues

### Tasks Not Running on Schedule

**Cause:** CRON not installed or task disabled.

**Solution:**
```bash
# Check CRON status
codegeass cron status

# If not installed
codegeass cron install

# Check task is enabled
codegeass task show my-task
# Look for: enabled: true
```

### "Task not found"

**Cause:** Task ID doesn't exist.

**Solution:**
```bash
# List available tasks
codegeass task list

# Check spelling in schedules.yaml
cat config/schedules.yaml
```

### Task Fails Immediately

**Cause:** Invalid working directory or Claude CLI issues.

**Solution:**
```bash
# Test the task
codegeass task run my-task

# Check logs
codegeass logs list --limit 1
codegeass logs show <execution-id>

# Verify working directory exists
ls -la /path/to/working/dir

# Verify Claude CLI works
claude --version
```

## CRON Issues

### CRON Job Not Firing

**Cause:** CRON service not running or misconfigured.

**Solution:**
```bash
# Check CRON service
systemctl status cron

# Check crontab
crontab -l | grep codegeass

# Check CRON logs
grep codegeass /var/log/syslog
# or
journalctl -u cron | grep codegeass
```

### "codegeass: Permission denied" in CRON

**Cause:** File permissions or missing executable.

**Solution:**
```bash
# Check Python path
which python

# Use absolute paths in crontab
* * * * * /usr/bin/python -m codegeass scheduler run-due
```

### PATH Issues in CRON

**Cause:** CRON has minimal PATH.

**Solution:**
```cron
# Add PATH to crontab
PATH=/usr/local/bin:/usr/bin:/bin:/home/user/.local/bin
* * * * * codegeass scheduler run-due
```

## Notification Issues

### Telegram Not Sending

**Cause:** Invalid bot token or chat ID.

**Solution:**
```bash
# Test notification
codegeass notification test telegram

# Verify credentials
cat ~/.codegeass/credentials.yaml

# Check bot token
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Get chat ID
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

### "Chat not found" Error

**Cause:** Bot not added to chat or wrong chat ID.

**Solution:**
1. Add bot to the group/channel
2. Send a message in the chat
3. Get updates to find the correct chat ID
4. Use negative ID for groups (e.g., `-1001234567890`)

### Discord Webhook Failing

**Cause:** Invalid or deleted webhook.

**Solution:**
```bash
# Test webhook directly
curl -H "Content-Type: application/json" \
  -d '{"content": "Test"}' \
  "YOUR_WEBHOOK_URL"

# Verify in Discord: Channel Settings → Integrations → Webhooks
```

## Plan Mode Issues

### Approval Not Appearing

**Cause:** Notifications not configured or plan creation failed.

**Solution:**
```bash
# Check pending approvals
codegeass approval list

# Check notifications are configured
codegeass notification list

# Test notification
codegeass notification test telegram
```

### Approval Timeout

**Cause:** Approval window expired.

**Solution:**
```yaml
# Increase timeout in config/settings.yaml
plan_mode:
  default_timeout: 7200  # 2 hours instead of 1
```

### Plan Mode Task Stuck

**Cause:** Approval pending but not visible.

**Solution:**
```bash
# List all approvals
codegeass approval list --all

# Check execution status
codegeass execution list

# Force reject if stuck
codegeass approval reject <id> --reason "Stuck, restarting"
```

## Log and Session Issues

### "No logs found"

**Cause:** No tasks have run or logs directory missing.

**Solution:**
```bash
# Check logs directory
ls -la data/logs/

# Create if missing
mkdir -p data/logs data/sessions

# Run a task to generate logs
codegeass task run my-task
```

### Session Files Too Large

**Cause:** Verbose Claude output or many executions.

**Solution:**
```bash
# Check disk usage
du -sh data/

# Clean old sessions
find data/sessions -name "*.json" -mtime +30 -delete
find data/logs -name "*.jsonl" -mtime +30 -delete
```

## Claude CLI Issues

### "Claude CLI not found"

**Cause:** Claude Code not installed or not in PATH.

**Solution:**
```bash
# Check Claude installation
claude --version

# If not installed, see:
# https://claude.ai/code
```

### Claude Authentication Issues

**Cause:** Not logged in or expired session.

**Solution:**
```bash
# Re-authenticate
claude login

# Verify
claude --version
```

### "API key required" in CRON

**Cause:** CodeGeass unsets ANTHROPIC_API_KEY by design.

**Explanation:** This is intentional. CodeGeass uses your Claude Pro/Max subscription, not API credits. The Claude CLI should work without an API key if you're logged in.

**Solution:**
```bash
# Ensure Claude CLI is authenticated
claude login

# Test Claude CLI works without API key
unset ANTHROPIC_API_KEY
claude -p "Hello"
```

## Configuration Issues

### "Invalid YAML"

**Cause:** YAML syntax error.

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/schedules.yaml'))"

# Common issues:
# - Missing quotes around special characters
# - Incorrect indentation
# - Tabs instead of spaces
```

### "Task ID already exists"

**Cause:** Duplicate task ID in schedules.yaml.

**Solution:**
```bash
# Check for duplicates
grep -E "^  - id:" config/schedules.yaml | sort | uniq -d

# Use unique IDs for each task
```

## Getting Help

If you can't resolve an issue:

1. **Check logs:**
   ```bash
   codegeass logs list --status failed
   codegeass logs show <execution-id>
   ```

2. **Enable debug logging:**
   ```bash
   export CODEGEASS_LOG_LEVEL=DEBUG
   codegeass task run my-task
   ```

3. **Report an issue:**
   https://github.com/dontizi/codegeass/issues

Include:
- CodeGeass version (`codegeass --version`)
- Python version (`python --version`)
- OS and version
- Error messages
- Steps to reproduce
