# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-01-29

### Fixed

- Resolved all ruff lint errors (line length, unused imports)
- Fixed test assertion for command list checking
- Code formatting improvements across 34 files

## [0.1.1] - 2025-01-29

### Added

- One-line installer script for macOS and Linux (`install.sh`)
- Uninstaller script (`uninstall.sh`)
- launchd service support for macOS (24/7 scheduling)
- `/release` skill for automated PyPI releases
- Example configuration templates (`config/*.example.yaml`)

### Fixed

- Removed hardcoded personal paths from documentation
- Auto-detect project directory in `cron-runner.sh`
- Auto-detect Claude CLI path in settings

### Security

- Removed sensitive config files from git history
- Added `config/notifications.yaml` and `config/schedules.yaml` to `.gitignore`
- Repository now safe for public visibility

## [0.1.0] - 2025-01-29

### Added

- **Core Framework**
  - Task scheduling with CRON expressions via `croniter`
  - YAML-based configuration for tasks, settings, and notifications
  - JSONL execution logs with detailed metadata
  - Session management for Claude Code interactions

- **Execution Strategies**
  - `HeadlessStrategy`: Safe, read-only execution with `claude -p`
  - `AutonomousStrategy`: Full file modification support with `--dangerously-skip-permissions`
  - `SkillStrategy`: Skill invocation using `/skill-name` syntax

- **Plan Mode Support**
  - Interactive plan approval workflow
  - Telegram-based plan review and approval
  - Plan timeout and auto-rejection settings

- **Multi-Project Support**
  - Global project registry (`~/.codegeass/projects.yaml`)
  - Shared skills directory (`~/.codegeass/skills/`)
  - Per-project skill overrides
  - Project enable/disable functionality

- **CLI Commands**
  - `task`: Create, list, show, run, enable, disable, delete tasks
  - `skill`: List, show, validate, render skills
  - `project`: Add, list, show, remove, set-default, init, enable, disable, update projects
  - `scheduler`: Status, run, run-due, upcoming, install-cron
  - `logs`: List, show, tail, stats for execution logs
  - `notification`: Add, list, show, test, remove, enable, disable notification channels
  - `approval`: Manage plan mode approvals
  - `cron`: CRON job management
  - `execution`: Manage task executions

- **Notifications**
  - Telegram integration with plan approval buttons
  - Discord webhook support
  - Provider pattern for extensible notification backends

- **Dashboard** (separate package)
  - React + FastAPI web interface
  - Real-time task monitoring
  - Log viewing and filtering
  - Task execution controls

- **Skills System**
  - [Agent Skills](https://agentskills.io) standard support
  - YAML frontmatter with metadata (name, description, context, agent, allowed-tools)
  - Jinja2 templating for dynamic skill content
  - Skill resolution with project and shared skill priority

- **Documentation**
  - MkDocs Material theme documentation site
  - CLI reference with mkdocs-click
  - Getting started guides
  - Concept explanations

### Security

- Credentials stored separately in `~/.codegeass/credentials.yaml`
- ANTHROPIC_API_KEY deliberately unset in CRON to use Pro/Max subscription
- No API tokens in configuration files

[Unreleased]: https://github.com/DonTizi/CodeGeass/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/DonTizi/CodeGeass/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/DonTizi/CodeGeass/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DonTizi/CodeGeass/releases/tag/v0.1.0
