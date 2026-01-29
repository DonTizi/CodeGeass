# logs

View execution logs and history.

## Usage

```bash
codegeass logs [OPTIONS] COMMAND [ARGS]...
```

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.logs
    :command: logs
    :prog_name: codegeass logs
    :depth: 1

## Examples

### List Recent Executions

```bash
# List last 10 executions
codegeass logs list

# List more
codegeass logs list --limit 50

# Filter by task
codegeass logs list --task daily-review

# Filter by status
codegeass logs list --status failed
```

### Show Execution Details

```bash
# Show full execution log
codegeass logs show abc123

# Show with session output
codegeass logs show abc123 --output
```

### Follow Logs in Real-Time

```bash
# Tail logs
codegeass logs tail

# Tail specific task
codegeass logs tail --task daily-review
```

### View Statistics

```bash
# Execution statistics
codegeass logs stats

# Stats for specific task
codegeass logs stats --task daily-review
```

## Log Format

Logs are stored as JSONL files in `data/logs/`:

```json
{
  "id": "abc123",
  "task_id": "daily-review",
  "started_at": "2024-01-15T09:00:00Z",
  "completed_at": "2024-01-15T09:05:23Z",
  "status": "completed",
  "exit_code": 0,
  "duration_seconds": 323,
  "mode": "headless"
}
```

## Log Statuses

| Status | Description |
|--------|-------------|
| `running` | Task is currently executing |
| `completed` | Task finished successfully |
| `failed` | Task failed with error |
| `waiting_approval` | Plan mode task awaiting approval |
| `approved` | Plan was approved, continuing |
| `rejected` | Plan was rejected |
| `timeout` | Execution or approval timed out |

## Session Data

Detailed session data is stored in `data/sessions/`:

```bash
# List session files
ls data/sessions/

# View session details
cat data/sessions/<execution-id>.json | jq
```

## Related Commands

- [`task run`](task.md) - Run tasks
- [`execution`](execution.md) - Manage executions
- [`scheduler`](scheduler.md) - View scheduled runs
