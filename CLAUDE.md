# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Never add "Co-Authored-By: Claude" or similar attribution lines in commits or messages**

- **CLI + Dashboard Sync**: When implementing new features for the CLI backend, always consider if they need to be exposed in the dashboard. If so, implement the full stack:
  1. CLI command in `src/codegeass/cli/`
  2. Backend API endpoint in `dashboard/backend/routers/`
  3. Frontend UI in `dashboard/frontend/src/`

- **Always verify before completion**: After implementing changes, start both frontend and backend to confirm they work. If they fail, troubleshoot until fixed.

## Project Overview

CodeGeass is a Claude Code Scheduler Framework - a system for orchestrating automated Claude Code sessions using CRON jobs with Claude Pro/Max subscriptions. Users define reusable AI-powered tasks that run on schedules, execute skills, and track execution history.

## Development Commands

### Core CLI

```bash
# Setup (from source)
git clone https://github.com/DonTizi/CodeGeass.git
cd CodeGeass
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Or install from PyPI
pip install codegeass

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

# Projects (multi-project support)
codegeass project list | add | show | remove | set-default | init | enable | disable | update

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
├── core/           # Domain: Task, Skill, Template, Prompt, Project entities + value objects
├── storage/        # YAML backend, task/log/project repositories, channel/credential managers
│   └── project_repository.py  # Multi-project registry management
├── factory/        # SkillRegistry, TaskFactory, TaskBuilder, SkillResolver
│   └── skill_resolver.py  # Project + shared skills with priority
├── execution/      # HeadlessStrategy, AutonomousStrategy, SkillStrategy
├── scheduling/     # CronParser (croniter), Scheduler, Job wrappers
├── notifications/  # Chat notifications (Telegram, Discord) with provider pattern
└── cli/            # Click commands: task, skill, project, scheduler, logs, notification

dashboard/
├── backend/        # FastAPI + Uvicorn (port 8001)
│   ├── routers/    # tasks, skills, logs, scheduler, notifications endpoints
│   └── services/   # Business logic layer
└── frontend/       # React 18 + Vite + TypeScript + Tailwind v4 + shadcn/ui + Zustand

~/.codegeass/       # Global user configuration
├── projects.yaml   # Project registry (multi-project mode)
├── credentials.yaml # Secrets (API keys, tokens)
└── skills/         # Shared skills (available to all projects)
```

### Execution Strategies

- **HeadlessStrategy**: Safe, read-only with `claude -p` (default)
- **AutonomousStrategy**: Allows file modifications with `--dangerously-skip-permissions`
- **SkillStrategy**: Invokes skills using `/skill-name` syntax

### Data Storage

- **Tasks**: `config/schedules.yaml` (YAML list)
- **Settings**: `config/settings.yaml`
- **Notifications**: `config/notifications.yaml` (channels, non-secret)
- **Projects**: `~/.codegeass/projects.yaml` (project registry, global)
- **Credentials**: `~/.codegeass/credentials.yaml` (secrets, global)
- **Shared Skills**: `~/.codegeass/skills/` (available to all projects)
- **Logs**: `data/logs/*.jsonl` (one JSON per line)
- **Sessions**: `data/sessions/`

## Key Design Decisions

1. **Subscription-Only**: Deliberately unsets `ANTHROPIC_API_KEY` in CRON to use Pro/Max subscription, not API credits
2. **File-Based Storage**: No database - YAML for config, JSONL for logs
3. **Strategy Pattern**: Multiple execution modes via interchangeable strategies
4. **Skill Standard**: Uses [Agent Skills](https://agentskills.io) open standard for reusable prompts
5. **Multi-Project Support**: Global project registry with shared skills and per-project overrides

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

## Available Skills

| Skill | Purpose | Usage |
|-------|---------|-------|
| `/new-feature` | Plan new features/integrations with SOLID principles, research docs, create GitHub issue | `/new-feature WhatsApp notification channel` |
| `/implement` | Implement code from a GitHub issue specification using TDD-style incremental development | `/implement #4` |
| `/refactor` | Refactor monolithic code into clean modules | `/refactor src/codegeass/cli/` |
| `/release` | Release new version to PyPI | `/release 0.2.0` |
| `/code-review` | Automated code review (security, performance, maintainability) | `/code-review .` |
| `/security-scan` | Security vulnerability scan | `/security-scan` |

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

Python 3.10+ required. Key dependencies: pydantic, click, rich, pyyaml, jinja2, croniter.

ruff line-length: 100, mypy strict mode enabled.

## Release Process

### PyPI Distribution (v0.1.0+)

The package is published on PyPI: https://pypi.org/project/codegeass/

**To release a new version:**

```bash
# Use the release skill (recommended)
/release 0.2.0

# Or manually:
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit and push
git add -A && git commit -m "Release vX.Y.Z" && git push origin main
# 4. Create and push tag (triggers GitHub Actions)
git tag vX.Y.Z && git push origin vX.Y.Z
```

**GitHub Actions Workflows:**
- `ci.yml`: Runs on push/PR - lint, test, build
- `release.yml`: Runs on tag `v*` - build, test install, publish to PyPI, create GitHub release
- `docs.yml`: Runs on push/tag - deploy versioned docs with mike

**Trusted Publishing (OIDC):**
- No API tokens stored - uses GitHub OIDC
- Configured on PyPI: Owner=`DonTizi`, Repo=`CodeGeass`, Workflow=`release.yml`, Environment=`pypi`

### Systemd Service (24/7 Scheduling)

```bash
# Install service (auto-detects codegeass location)
./service/install.sh

# Check status
systemctl --user status codegeass-scheduler.timer

# View logs
journalctl --user -u codegeass-scheduler -f

# Uninstall
./service/uninstall.sh
```

### Documentation

- **Live docs**: https://dontizi.github.io/codegeass/
- **Versioning**: mike (version selector in docs)
- **Build locally**: `pip install -e ".[docs]" && mkdocs serve`

## Architecture Principle: CLI is the Source of Truth

**CRITICAL**: The CLI (`src/codegeass/`) is ALWAYS the source of truth. The Dashboard is just a UI layer.

- ALL features must be implemented in the CLI first
- The Dashboard backend should ONLY call CLI/library code
- Never implement business logic in the Dashboard that doesn't exist in CLI
- Telegram callbacks, plan approvals, notifications - everything must work from CLI

## Testing Procedure for Features

**When testing a new feature or debugging an existing one, follow this procedure:**

1. **Create a test task**
   ```bash
   codegeass task create --name test-<feature> --schedule "0 0 * * *" --prompt "<test prompt>" --working-dir $(pwd)
   ```

2. **Run the task and observe**
   ```bash
   codegeass task run test-<feature>
   ```

3. **Verify execution logs**
   ```bash
   codegeass logs list --limit 5
   codegeass task show test-<feature>
   ```

4. **Check session data**
   ```bash
   ls -lt data/sessions/ | head -5
   cat data/sessions/<latest-session>.json | python -m json.tool
   ```

5. **Test through the Dashboard**
   - Start dashboard: `cd dashboard && ./run.sh`
   - Open http://localhost:5173
   - Verify the feature works in the UI

6. **Keep test tasks until user confirms**
   - Do NOT delete test tasks automatically
   - Wait for user confirmation that everything works
   - Only then: `codegeass task delete test-<feature> --yes`

### Example: Testing Isolation
```bash
# Create test task
codegeass task create --name test-isolation --schedule "0 0 * * *" --prompt "just say hello"

# Check worktrees before
git worktree list | wc -l

# Run and observe
codegeass task run test-isolation

# Check worktrees during/after execution
git worktree list

# Verify session metadata shows isolation
cat data/sessions/<session>.json | grep -E "isolated|worktree"
```
