# Execution Modes

CodeGeass supports different execution strategies for running Claude. Each mode offers different capabilities and safety levels.

## Code Execution Providers

CodeGeass v0.1.5+ supports multiple code execution providers, enabling you to use different AI coding assistants:

| Provider | ID | Status |
|----------|-----|--------|
| Claude Code | `claude-code` | Default |
| OpenAI Codex | `codex` | Experimental |

Use the `--code-source` flag when creating tasks to specify a provider:

```bash
codegeass task create --name my-task --code-source codex ...
```

See [Provider CLI Reference](../cli/provider.md) for more details.

## Execution Strategies

### Headless Strategy (Default)

The safest mode - read-only execution using `claude -p`:

```bash
codegeass task create --mode headless ...
```

**Capabilities:**
- Read files
- Search code
- Analyze codebases
- Generate reports

**Limitations:**
- Cannot modify files
- Cannot run shell commands
- Cannot create new files

**Best for:**
- Code review
- Analysis tasks
- Report generation
- Learning about codebases

### Autonomous Strategy

Full Claude capabilities with `--dangerously-skip-permissions`:

```bash
codegeass task create --mode autonomous ...
```

**Capabilities:**
- All headless capabilities
- Create, edit, delete files
- Run shell commands
- Install dependencies
- Commit changes

**Risks:**
- Unintended file modifications
- Potential for destructive commands
- Security considerations

**Best for:**
- Automated refactoring
- Code generation
- Maintenance tasks
- Trusted environments

!!! danger "Security Warning"
    Autonomous mode bypasses all safety checks. Only use on trusted projects where you accept the risk of unintended changes.

### Skill Strategy

Invokes predefined skills with controlled permissions:

```bash
codegeass task create --mode skill --skill review ...
```

**Capabilities:**
- Defined by the skill's `allowed-tools` field
- Scoped to specific operations
- Predictable behavior

**Best for:**
- Repeatable tasks
- Controlled automation
- Team standardization

## Mode Comparison

| Feature | Headless | Autonomous | Skill |
|---------|----------|------------|-------|
| Read files | Yes | Yes | Depends |
| Write files | No | Yes | Depends |
| Run commands | No | Yes | Depends |
| Safety | Highest | Lowest | Medium |
| Predictability | High | Low | High |
| Use case | Analysis | Full automation | Controlled tasks |

## Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Task Execution                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Load task configuration                             │
│  2. Determine execution strategy                        │
│  3. Prepare working directory                           │
│  4. Execute Claude with appropriate flags               │
│  5. Capture output and session data                     │
│  6. Log results                                         │
│  7. Send notifications (if configured)                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Command Mapping

| Mode | Claude Command |
|------|----------------|
| Headless | `claude -p "prompt"` |
| Autonomous | `claude -p "prompt" --dangerously-skip-permissions` |
| Skill | `claude -p "/skill-name args"` |

## Session Data

Each execution creates session data in `data/sessions/`:

```json
{
  "id": "abc123",
  "task_id": "daily-review",
  "started_at": "2024-01-15T09:00:00Z",
  "completed_at": "2024-01-15T09:05:23Z",
  "status": "completed",
  "mode": "headless",
  "output": "...",
  "exit_code": 0
}
```

## Execution Logs

View execution history:

```bash
# List recent executions
codegeass logs list

# Show execution details
codegeass logs show <execution-id>

# Follow logs in real-time
codegeass logs tail
```

## Best Practices

### Choosing a Mode

1. **Start with headless** - Default for new tasks
2. **Use skill mode** - When you have repeatable patterns
3. **Use autonomous sparingly** - Only when file changes are required

### Safety Measures

1. **Test manually first** - Run `codegeass task run` before scheduling
2. **Review outputs** - Check logs after each execution
3. **Use version control** - Ensure changes can be reverted
4. **Set up notifications** - Know when tasks fail

### Performance

1. **Clear prompts** - Reduce Claude's confusion
2. **Scoped tasks** - Smaller scope = faster execution
3. **Use skills** - Reusable prompts are more efficient

## Stopping Running Tasks

You can stop a running task execution at any time:

```bash
codegeass task stop <task-name>
```

This sends SIGTERM to the Claude process for graceful shutdown, falling back to SIGKILL if needed. The Dashboard also provides a Stop button for running tasks.

## Related

- [Tasks](tasks.md) - Task configuration
- [Skills](skills.md) - Creating skills
- [Plan Mode](plan-mode.md) - Approval workflow
- [Provider CLI](../cli/provider.md) - Managing code providers
