<p align="center">
  <img src="assets/logo.png" alt="CodeGeass Logo" width="180" />
</p>

# CodeGeass

Task orchestration for AI coding agents.

---

## What It Does

CodeGeass helps you run AI coding tasks reliably:

- **Schedule tasks** with CRON expressions
- **Manage multiple projects** from one installation
- **Use reusable skills** (parameterized prompts)
- **Choose execution modes**: read-only, plan-first, or autonomous
- **Review changes** before they're applied
- **Get notifications** via Telegram, Discord, or Teams
- **Monitor everything** through a web dashboard

## Quick Install

```bash
pipx install codegeass
codegeass setup
```

## How It Works

1. You define tasks with prompts or skills
2. Tasks run on schedule (or manually)
3. AI agents execute in your chosen mode
4. Results are logged and notifications sent
5. For plan mode, you review and approve before execution

## Quick Start

```bash
# Create a task
codegeass task create \
  --name daily-review \
  --skill code-review \
  --schedule "0 9 * * 1-5"

# Run it
codegeass task run daily-review

# Open dashboard
codegeass dashboard
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
│  ┌─────────┐ ┌─────────────────────────────────────────┐│
│  │Projects │ │ Notifications                           ││
│  └─────────┘ └─────────────────────────────────────────┘│
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
