# approval

Manage plan mode approvals.

## Usage

```bash
codegeass approval [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.approval
    :command: approval
    :prog_name: codegeass approval
    :depth: 1

## Examples

### List Pending Approvals

```bash
# Show all pending approvals
codegeass approval list

# Show all approvals (including resolved)
codegeass approval list --all
```

### Show Approval Details

```bash
# View plan and details
codegeass approval show abc123
```

### Approve a Plan

```bash
# Approve and continue execution
codegeass approval approve abc123
```

### Reject a Plan

```bash
# Reject with reason
codegeass approval reject abc123 --reason "Too risky"

# Reject without reason
codegeass approval reject abc123
```

## Approval Workflow

```
Task Start (plan_mode=true)
         │
         v
  ┌──────────────┐
  │ Claude Plans │
  └──────────────┘
         │
         v
  ┌──────────────┐     ┌──────────────┐
  │   Pending    │────>│   Approve    │───> Execution Continues
  │   Approval   │     └──────────────┘
  └──────────────┘
         │
         │            ┌──────────────┐
         └───────────>│   Reject     │───> Task Stops
                      └──────────────┘
                             │
                      ┌──────────────┐
                      │   Timeout    │───> Task Stops (auto-reject)
                      └──────────────┘
```

## Approval Statuses

| Status | Description |
|--------|-------------|
| `pending` | Waiting for user action |
| `approved` | Plan approved, execution continuing |
| `rejected` | Plan rejected by user |
| `timeout` | Approval window expired |

## Timeout Configuration

Configure approval timeout in `config/settings.yaml`:

```yaml
plan_mode:
  default_timeout: 3600  # seconds (1 hour)
```

## Notifications

Get notified when approval is needed:

```yaml
# config/notifications.yaml
channels:
  - id: telegram-approvals
    provider: telegram
    events:
      - approval_required
```

## Related

- [Plan Mode Concept](../concepts/plan-mode.md)
- [Plan Mode Guide](../guides/plan-mode-workflow.md)
- [`task`](task.md) - Create tasks with `--plan-mode`
