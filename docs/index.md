# CodeGeass

**Claude Code Scheduler Framework** - Orchestrate automated Claude Code sessions using CRON jobs with your Claude Pro/Max subscription.

---

## What is CodeGeass?

CodeGeass lets you define reusable AI-powered tasks that run on schedules, execute skills, and track execution history. It's designed for developers who want to automate repetitive coding tasks using Claude's capabilities.

```bash
# Create a task that runs daily
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * *" \
  --prompt "Review recent commits and summarize changes"

# Run it manually anytime
codegeass task run daily-review
```

## Key Features

- **Scheduled Automation** - Run Claude Code sessions on CRON schedules
- **Subscription-First** - Uses your Claude Pro/Max subscription, not API credits
- **Skills System** - Reusable, parameterized prompts following the [Agent Skills](https://agentskills.io) standard
- **Plan Mode** - Interactive approval workflow for complex tasks
- **Notifications** - Get notified via Telegram or Discord when tasks complete
- **Execution History** - Full logging and session tracking

## Quick Example

```bash
# Install CodeGeass
pip install codegeass

# Create your first task
codegeass task create \
  --name test-task \
  --schedule "*/30 * * * *" \
  --prompt "Run the test suite and report any failures"

# Enable the scheduler
codegeass scheduler install-cron

# Check upcoming runs
codegeass scheduler upcoming
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     CodeGeass                           │
├─────────────────────────────────────────────────────────┤
│  CLI Commands                                           │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌─────────────┐  │
│  │  task   │ │  skill  │ │ scheduler │ │ notification│  │
│  └─────────┘ └─────────┘ └───────────┘ └─────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Core                                                   │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌─────────────┐  │
│  │  Tasks  │ │ Skills  │ │ Scheduler │ │  Execution  │  │
│  └─────────┘ └─────────┘ └───────────┘ └─────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Storage (YAML/JSONL)                                   │
│  ┌─────────────────┐ ┌──────────────┐ ┌───────────────┐ │
│  │ config/         │ │ data/logs/   │ │ data/sessions/│ │
│  │ schedules.yaml  │ │ *.jsonl      │ │ *.json        │ │
│  └─────────────────┘ └──────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Next Steps

<div class="grid cards" markdown>

-   :material-download: **[Installation](getting-started/installation.md)**

    Get CodeGeass installed on your system

-   :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Create your first task in 5 minutes

-   :material-book-open-variant: **[Concepts](concepts/tasks.md)**

    Learn about tasks, skills, and scheduling

-   :material-console: **[CLI Reference](cli/index.md)**

    Complete command documentation

</div>
