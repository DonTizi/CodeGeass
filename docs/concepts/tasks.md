# Tasks

Tasks are the core unit of work in CodeGeass. Each task defines what Claude should do and when it should run.

## What is a Task?

A task combines:

- **A prompt or skill** - Instructions for Claude
- **A schedule** - When to run (CRON expression)
- **Configuration** - Working directory, execution mode, etc.

```yaml
id: daily-review
name: Daily Code Review
schedule: "0 9 * * 1-5"
prompt: "Review commits from the last 24 hours and summarize changes"
working_dir: /home/user/project
mode: headless
enabled: true
```

## Creating Tasks

### Via CLI

```bash
# Basic task
codegeass task create \
  --name my-task \
  --schedule "0 9 * * *" \
  --prompt "Your instructions here"

# With all options
codegeass task create \
  --name my-task \
  --schedule "0 9 * * *" \
  --prompt "Your instructions" \
  --working-dir /path/to/project \
  --mode autonomous \
  --plan-mode
```

### Via YAML

Edit `config/schedules.yaml` directly:

```yaml
tasks:
  - id: my-task
    name: My Task
    schedule: "0 9 * * *"
    prompt: "Your instructions here"
    working_dir: /path/to/project
    mode: headless
    enabled: true
```

## Task Modes

### Headless Mode (Default)

Safe, read-only execution using `claude -p`:

```bash
codegeass task create --name safe-task --mode headless ...
```

- Cannot modify files
- Best for analysis, reporting, code review
- No risk of unintended changes

### Autonomous Mode

Full Claude capabilities with `--dangerously-skip-permissions`:

```bash
codegeass task create --name auto-task --mode autonomous ...
```

- Can create, edit, and delete files
- Can run shell commands
- Use only on trusted projects

!!! warning "Use with Caution"
    Autonomous mode gives Claude full control. Only use this on projects where you trust the outcome.

### Skill Mode

Invokes a predefined skill:

```bash
codegeass task create --name skill-task --mode skill --skill review ...
```

- Uses skills from `.claude/skills/`
- Follows the [Agent Skills](https://agentskills.io) standard
- Parameters passed via arguments

## Task Lifecycle

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌───────────┐
│ Created  │───>│  Enabled  │───>│ Running  │───>│ Completed │
└──────────┘    └───────────┘    └──────────┘    └───────────┘
                     │                                 │
                     v                                 v
               ┌───────────┐                    ┌───────────┐
               │ Disabled  │                    │  Failed   │
               └───────────┘                    └───────────┘
```

## Managing Tasks

```bash
# List all tasks
codegeass task list

# Show task details
codegeass task show <task-id>

# Enable/disable
codegeass task enable <task-id>
codegeass task disable <task-id>

# Run manually
codegeass task run <task-id>

# Delete
codegeass task delete <task-id>
```

## Task with Plan Mode

Plan mode adds an approval step before execution:

```bash
codegeass task create \
  --name careful-task \
  --mode autonomous \
  --plan-mode \
  --prompt "Refactor the authentication module"
```

When run:
1. Claude creates a plan
2. You receive a notification to approve
3. After approval, execution continues
4. Full results are logged

See [Plan Mode](plan-mode.md) for details.

## Best Practices

1. **Start with headless mode** - Only use autonomous when needed
2. **Use specific prompts** - Clear instructions get better results
3. **Test manually first** - Run `codegeass task run` before enabling schedules
4. **Enable notifications** - Know when tasks complete or fail
5. **Review logs regularly** - Check `codegeass logs list` for issues

## Related

- [Skills](skills.md) - Reusable prompt templates
- [Scheduling](scheduling.md) - CRON expressions
- [Execution](execution.md) - Execution strategies
