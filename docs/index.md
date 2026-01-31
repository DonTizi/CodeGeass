<p align="center">
  <img src="assets/logo.png" alt="CodeGeass Logo" width="180" />
</p>

# CodeGeass

**Claude Code Scheduler Framework** - Orchestrate automated Claude Code sessions using CRON jobs with your Claude Pro/Max subscription.

---

## What is CodeGeass?

CodeGeass lets you define reusable AI-powered tasks that run on schedules, execute skills, and track execution history. It's designed for developers who want to automate repetitive coding tasks using Claude's capabilities.

## Quick Install

```bash
# macOS
brew install pipx && pipx ensurepath && source ~/.zshrc

# Linux
python3 -m pip install --user pipx && pipx ensurepath && source ~/.bashrc

# Install CodeGeass + 24/7 scheduler
pipx install codegeass
codegeass setup
```

That's it! The scheduler is now running in the background.

## Create Your First Task

```bash
# Create a task that runs daily at 9 AM
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * *" \
  --prompt "Review recent commits and summarize changes"

# Run it manually to test
codegeass task run daily-review

# Check upcoming scheduled runs
codegeass scheduler upcoming
```

## Key Features

- **Scheduled Automation** - Run Claude Code sessions on CRON schedules
- **Subscription-First** - Uses your Claude Pro/Max subscription, not API credits
- **Multi-Project Support** - Manage multiple projects from a single installation with shared skills
- **Skills System** - Reusable, parameterized prompts following the [Agent Skills](https://agentskills.io) standard
- **Plan Mode** - Interactive approval workflow for complex tasks
- **Notifications** - Get notified via Telegram, Discord, or Teams when tasks complete
- **Execution History** - Full logging and session tracking
- **Web Dashboard** - Visual management interface

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
