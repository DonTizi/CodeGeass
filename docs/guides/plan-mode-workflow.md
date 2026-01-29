# Plan Mode Workflow

This guide explains how to use plan mode for safe, controlled automation with human approval.

## Why Plan Mode?

Plan mode adds a review step before Claude makes changes:

1. Claude analyzes the task and creates a plan
2. You review the plan and approve or reject
3. Only after approval does execution continue

This is essential for:
- Autonomous tasks that modify files
- Critical codebases where mistakes are costly
- Team environments where visibility is important

## Enabling Plan Mode

### On a New Task

```bash
codegeass task create \
  --name refactor-auth \
  --schedule "0 9 * * 1" \
  --prompt "Refactor the authentication module for better security" \
  --mode autonomous \
  --plan-mode
```

### On an Existing Task

Edit `config/schedules.yaml`:

```yaml
tasks:
  - id: refactor-auth
    schedule: "0 9 * * 1"
    prompt: "Refactor the authentication module"
    mode: autonomous
    plan_mode: true  # Add this line
```

## The Workflow

### Step 1: Task Runs and Creates Plan

When the scheduled time arrives (or you run manually):

```bash
$ codegeass task run refactor-auth
Task 'refactor-auth' started in plan mode
Creating plan...
Plan created. Waiting for approval.
Approval ID: abc123
```

### Step 2: You Receive a Notification

If notifications are configured, you'll get an alert:

```
🔔 Approval Required: refactor-auth

Plan Summary:
1. Analyze current auth module structure
2. Identify security improvements
3. Refactor password hashing to use bcrypt
4. Add rate limiting to login endpoint
5. Update tests

[Approve] [Reject]
```

### Step 3: Review the Plan

View full details:

```bash
$ codegeass approval show abc123
ID: abc123
Task: refactor-auth
Status: pending
Created: 2024-01-15 09:00:00
Expires: 2024-01-15 10:00:00

Plan:
─────────────────────────────────────────────────
Phase 1: Analysis
  - Read src/auth.py and understand current structure
  - Identify security weaknesses
  - List files that import from auth module

Phase 2: Implementation
  - Replace MD5 password hashing with bcrypt
  - Add rate limiting (5 attempts per minute)
  - Add account lockout after 10 failed attempts

Phase 3: Testing
  - Update unit tests for new behavior
  - Run full test suite
  - Verify no regressions

Files to Modify:
  - src/auth.py
  - src/middleware/rate_limit.py (new)
  - tests/test_auth.py
─────────────────────────────────────────────────
```

### Step 4: Approve or Reject

**If the plan looks good:**

```bash
$ codegeass approval approve abc123
Plan approved. Execution continuing...
```

**If you have concerns:**

```bash
$ codegeass approval reject abc123 --reason "Rate limit should be 10 attempts, not 5"
Plan rejected. Task stopped.
```

### Step 5: Execution Completes

After approval, Claude executes the plan:

```bash
$ codegeass logs show <execution-id>
Status: completed
Duration: 5m 23s

Output:
  - Refactored src/auth.py with bcrypt
  - Created src/middleware/rate_limit.py
  - Updated 12 tests
  - All tests passing
```

## Telegram Interactive Approval

With Telegram configured, you can approve/reject directly from the chat:

```
🔔 Approval Required: refactor-auth

Plan Summary:
1. Refactor password hashing
2. Add rate limiting
3. Update tests

[Approve] [Reject]
```

Tap the button to approve or reject without using the CLI.

## Timeout Handling

Plans expire after a configurable timeout (default: 1 hour):

```yaml
# config/settings.yaml
plan_mode:
  default_timeout: 3600  # seconds
```

When a plan times out:
- The task is marked as failed
- You receive a notification (if configured)
- No changes are made

## Best Practices

### 1. Enable Notifications

```bash
codegeass notification add telegram \
  --bot-token "..." \
  --chat-id "..."
```

Don't miss approval requests!

### 2. Review Carefully

Read the full plan before approving. Look for:
- Files that will be modified
- Scope of changes
- Potential risks

### 3. Set Reasonable Timeouts

```yaml
# Long-running analysis needs longer approval window
plan_mode:
  default_timeout: 7200  # 2 hours
```

### 4. Use Descriptive Rejection Reasons

```bash
codegeass approval reject abc123 \
  --reason "Please use argon2 instead of bcrypt"
```

The reason helps if you re-run the task with modified prompts.

### 5. Combine with Version Control

Autonomous mode + plan mode + git = safe automation:

```bash
# Always verify changes after approval
git status
git diff
```

## Example: Complete Workflow

```bash
# 1. Create a plan-mode task
codegeass task create \
  --name weekly-cleanup \
  --schedule "0 6 * * 6" \
  --prompt "Clean up unused code, dead imports, and fix linting issues" \
  --mode autonomous \
  --plan-mode

# 2. Set up notifications
codegeass notification add telegram \
  --bot-token "..." \
  --chat-id "..."

# 3. Task runs Saturday at 6 AM, creates plan

# 4. You receive Telegram notification at 6:01 AM

# 5. Review when convenient
codegeass approval show <id>

# 6. Approve if looks good
codegeass approval approve <id>

# 7. Claude makes the changes

# 8. Review results
codegeass logs show <execution-id>
git status
```

## Troubleshooting

### Plan Not Created

Check logs:
```bash
codegeass logs list --status failed
```

Common issues:
- Invalid working directory
- Missing permissions
- Claude CLI not found

### Approval Expired

The plan timed out. Options:
- Re-run the task: `codegeass task run <task-id>`
- Increase timeout in settings

### Telegram Buttons Not Working

Ensure your bot token and chat ID are correct:
```bash
codegeass notification test telegram
```

## Next Steps

- [Notifications](setup-notifications.md) - Set up alerts
- [Plan Mode Concept](../concepts/plan-mode.md) - Deeper understanding
- [Execution Modes](../concepts/execution.md) - When to use which mode
