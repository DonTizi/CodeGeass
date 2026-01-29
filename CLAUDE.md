# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Never add "Co-Authored-By: Claude" or similar attribution lines in commits or messages**

## Project Overview

CodeGeass is a Claude Code Scheduler Framework - a system for orchestrating automated Claude Code sessions using CRON jobs with Claude Pro/Max subscriptions. Users define reusable AI-powered tasks that run on schedules, execute skills, and track execution history.

## Development Commands

### Core CLI

```bash
# Setup
cd /home/dontizi/Projects/codegeass
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Verify
codegeass --version
```

### Testing & Quality

```bash
pytest tests/ -v                    # Run all tests
pytest tests/test_entities.py -v    # Single test file
mypy src/codegeass                 # Type checking
ruff check src/codegeass           # Linting
ruff check src/codegeass --fix     # Auto-fix lint issues
```

### Dashboard

```bash
cd dashboard
./setup.sh    # First-time setup
./run.sh      # Run frontend (5173) + backend (8001)

# Or manually:
cd dashboard/backend && source venv/bin/activate && uvicorn main:app --port 8001 --reload
cd dashboard/frontend && npm run dev
```

### CLI Commands

```bash
# Tasks
codegeass task list | show | create | run | enable | disable | delete

# Skills
codegeass skill list | show | validate | render

# Scheduler
codegeass scheduler status | run | run-due | upcoming | install-cron

# Logs
codegeass logs list | show | tail | stats

# Notifications
codegeass notification list | add | show | test | remove | enable | disable | providers
```

## Architecture

```
src/codegeass/
├── core/           # Domain: Task, Skill, Template, Prompt entities + value objects
├── storage/        # YAML backend, task/log repositories, channel/credential managers
├── factory/        # SkillRegistry, TaskFactory, TaskBuilder
├── execution/      # HeadlessStrategy, AutonomousStrategy, SkillStrategy
├── scheduling/     # CronParser (croniter), Scheduler, Job wrappers
├── notifications/  # Chat notifications (Telegram, Discord) with provider pattern
└── cli/            # Click commands: task, skill, scheduler, logs, notification

dashboard/
├── backend/        # FastAPI + Uvicorn (port 8001)
│   ├── routers/    # tasks, skills, logs, scheduler, notifications endpoints
│   └── services/   # Business logic layer
└── frontend/       # React 18 + Vite + TypeScript + Tailwind v4 + shadcn/ui + Zustand
```

### Execution Strategies

- **HeadlessStrategy**: Safe, read-only with `claude -p` (default)
- **AutonomousStrategy**: Allows file modifications with `--dangerously-skip-permissions`
- **SkillStrategy**: Invokes skills using `/skill-name` syntax

### Data Storage

- **Tasks**: `config/schedules.yaml` (YAML list)
- **Settings**: `config/settings.yaml`
- **Notifications**: `config/notifications.yaml` (channels, non-secret)
- **Credentials**: `~/.codegeass/credentials.yaml` (secrets, global)
- **Logs**: `data/logs/*.jsonl` (one JSON per line)
- **Sessions**: `data/sessions/`

## Key Design Decisions

1. **Subscription-Only**: Deliberately unsets `ANTHROPIC_API_KEY` in CRON to use Pro/Max subscription, not API credits
2. **File-Based Storage**: No database - YAML for config, JSONL for logs
3. **Strategy Pattern**: Multiple execution modes via interchangeable strategies
4. **Skill Standard**: Uses [Agent Skills](https://agentskills.io) open standard for reusable prompts

## Skills Format

Skills live in `.claude/skills/` and follow this YAML frontmatter format:

```yaml
---
name: my-skill
description: What it does
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---
# Instructions for $ARGUMENTS
```

## Frontend Patterns

**lucide-react icons**: Always use `import type` for `LucideIcon`:
```typescript
// CORRECT
import type { LucideIcon } from 'lucide-react';
import { Home, Settings } from 'lucide-react';

// WRONG - causes Vite error
import { LucideIcon } from 'lucide-react';
```

## Configuration

Python 3.11+ required. Key dependencies: pydantic, click, rich, pyyaml, jinja2, croniter.

ruff line-length: 100, mypy strict mode enabled.
