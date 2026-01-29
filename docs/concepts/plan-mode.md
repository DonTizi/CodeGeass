# Plan Mode

Plan mode adds an interactive approval workflow to task execution. Claude creates a plan, you review and approve, then execution continues.

## What is Plan Mode?

Plan mode splits execution into two phases:

1. **Planning Phase** - Claude analyzes the task and creates a plan
2. **Execution Phase** - After approval, Claude executes the plan

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌───────────┐
│   Task      │────>│   Claude     │────>│   Review    │────>│  Execute  │
│   Start     │     │   Plans      │     │   Approve   │     │   Plan    │
└─────────────┘     └──────────────┘     └──────────────┘     └───────────┘
                                                │
                                                v
                                         ┌───────────┐
                                         │   Reject  │
                                         │   (Stop)  │
                                         └───────────┘
```

## Why Use Plan Mode?

- **Safety** - Review changes before they happen
- **Control** - Approve or reject proposed actions
- **Visibility** - Understand what Claude will do
- **Collaboration** - Human-in-the-loop automation

## Enabling Plan Mode

### Per Task

```bash
codegeass task create \
  --name careful-refactor \
  --mode autonomous \
  --plan-mode \
  --prompt "Refactor the authentication module"
```

### In YAML

```yaml
tasks:
  - id: careful-refactor
    name: Careful Refactor
    schedule: "0 9 * * *"
    prompt: "Refactor the authentication module"
    mode: autonomous
    plan_mode: true
```

## Approval Workflow

### 1. Task Runs and Creates Plan

When a plan-mode task executes, it pauses after planning:

```bash
$ codegeass task run careful-refactor
Task 'careful-refactor' started in plan mode
Waiting for approval...
Use 'codegeass approval list' to see pending approvals
```

### 2. Review Pending Approvals

```bash
$ codegeass approval list
ID        Task              Status    Created
────────────────────────────────────────────────
abc123    careful-refactor  pending   2024-01-15 09:00
```

### 3. View Plan Details

```bash
$ codegeass approval show abc123
Task: careful-refactor
Status: pending
Plan:
  1. Read current auth module (src/auth.py)
  2. Create new auth module with improved structure
  3. Update imports in dependent files
  4. Run tests to verify changes
```

### 4. Approve or Reject

```bash
# Approve the plan
codegeass approval approve abc123

# Reject the plan
codegeass approval reject abc123 --reason "Too risky"
```

### 5. Execution Continues

After approval, the task continues with the planned changes:

```bash
$ codegeass approval approve abc123
Plan approved. Execution continuing...
Task 'careful-refactor' completed successfully.
```

## Notifications

Plan mode integrates with notifications. When approval is needed, you receive an alert:

```yaml
# config/notifications.yaml
channels:
  - id: telegram-approvals
    provider: telegram
    events:
      - approval_required
      - task_completed
```

See [Notifications Setup](../guides/setup-notifications.md) for configuration.

## Timeout Handling

Plans expire after a configurable timeout (default: 1 hour):

```yaml
# config/settings.yaml
plan_mode:
  default_timeout: 3600  # seconds
```

Expired plans are automatically rejected.

## Best Practices

### When to Use Plan Mode

- **Autonomous tasks** - Any task that modifies files
- **Critical systems** - Production codebases
- **Large changes** - Refactoring, migrations
- **Team workflows** - When multiple people need visibility

### When to Skip Plan Mode

- **Headless tasks** - Read-only tasks don't need approval
- **Well-tested skills** - Trusted, repeatable operations
- **CI/CD pipelines** - Where human approval isn't practical

### Tips

1. **Enable notifications** - Don't miss approval requests
2. **Review carefully** - Read the full plan before approving
3. **Use meaningful prompts** - Clear instructions lead to better plans
4. **Set appropriate timeouts** - Balance urgency with review time

## Example Workflow

Complete example of a plan mode task:

```bash
# Create the task
codegeass task create \
  --name upgrade-deps \
  --schedule "0 9 * * 1" \
  --mode autonomous \
  --plan-mode \
  --prompt "Check for outdated dependencies and upgrade them safely"

# Task runs Monday at 9 AM, creates plan, and waits

# You receive a Telegram notification: "Approval needed for 'upgrade-deps'"

# Review the plan
codegeass approval show <approval-id>

# If it looks good, approve
codegeass approval approve <approval-id>

# Task continues and completes
# You receive: "Task 'upgrade-deps' completed successfully"
```

## Related

- [Tasks](tasks.md) - Task configuration
- [Execution](execution.md) - Execution modes
- [Notifications](notifications.md) - Notification setup
- [Approval Commands](../cli/approval.md) - CLI reference
