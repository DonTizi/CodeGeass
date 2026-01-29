# execution

Manage task executions.

## Usage

```bash
codegeass execution [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.execution
    :command: execution
    :prog_name: codegeass execution
    :depth: 1

## Examples

### List Executions

```bash
# List recent executions
codegeass execution list

# Filter by task
codegeass execution list --task daily-review

# Filter by status
codegeass execution list --status running
```

### Show Execution Details

```bash
codegeass execution show abc123
```

### Stop a Running Execution

```bash
# Stop execution gracefully
codegeass execution stop abc123
```

## Execution Lifecycle

```
┌───────────┐     ┌───────────┐     ┌────────────┐
│  Queued   │────>│  Running  │────>│ Completed  │
└───────────┘     └───────────┘     └────────────┘
                       │
                       │            ┌────────────┐
                       └───────────>│  Failed    │
                                    └────────────┘
```

For plan mode tasks:

```
Running ──> waiting_approval ──> approved ──> Completed
                 │
                 └──> rejected ──> Stopped
                 │
                 └──> timeout ──> Stopped
```

## Execution Data

Each execution creates:

1. **Log entry** in `data/logs/*.jsonl`
2. **Session data** in `data/sessions/<id>.json`

### Log Entry Fields

| Field | Description |
|-------|-------------|
| `id` | Unique execution ID |
| `task_id` | Task that was executed |
| `started_at` | Execution start time |
| `completed_at` | Execution end time |
| `status` | Current status |
| `exit_code` | Claude exit code |
| `mode` | Execution mode used |

### Session Data

Contains full Claude session information:

```json
{
  "id": "abc123",
  "task_id": "daily-review",
  "output": "Claude's full response...",
  "tool_calls": [...],
  "duration_seconds": 145
}
```

## Viewing Output

```bash
# Show execution with output
codegeass execution show abc123 --output

# Read session file directly
cat data/sessions/abc123.json | jq
```

## Related

- [`logs`](logs.md) - View execution logs
- [`task run`](task.md) - Trigger new executions
- [`scheduler`](scheduler.md) - View scheduled executions
