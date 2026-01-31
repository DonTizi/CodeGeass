# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-01-31

### Added

- **Setup & Uninstall CLI Commands**: One-command scheduler installation (#15)
  - `codegeass setup`: Detects OS and installs appropriate scheduler (launchd on macOS, systemd on Linux, cron as fallback)
  - `codegeass uninstall`: Remove scheduler with optional `--all` to remove global config and project data
  - Supports `--force` for reinstall, `--keep-global` and `--keep-project` flags

### Changed

- **Simplified Installation**: Replace curl-based installation with pipx (recommended) and pip in venv
- Remove legacy `install.sh` and `uninstall.sh` scripts in favor of CLI commands

### Documentation

- Updated README, installation guide, quickstart, and production setup with new installation methods

## [0.2.0] - 2026-01-31

### Added

- **Universal Code Execution Provider Architecture**: Pluggable code execution backends (#7)
  - `CodeProvider` abstract base class for execution providers
  - `ProviderRegistry` for lazy loading and provider discovery
  - `ClaudeCodeAdapter` and `CodexAdapter` implementations
  - CLI commands: `codegeass provider list|info|check`
  - `--code-source` flag for per-task provider override
  - Dashboard provider selector in task forms

- **Microsoft Teams Workflows Support**: Power Automate webhook integration (#5)
  - Replace deprecated O365 Connectors with Power Automate Workflows
  - Adaptive Cards for rich message formatting
  - Full plan approval workflow with action buttons
  - Provider-specific output limits (Teams: 20K, Telegram: 4K, Discord: 2K)

- **Discord Interactive Plan Approval**: Webhook-based plan approval (#12)
  - `DiscordHtmlFormatter` for HTML to Discord Markdown conversion
  - `DiscordEmbedBuilder` for rich embeds with status colors
  - Dashboard-linked approval buttons (same approach as Teams)

- **Stop Task Execution**: Ability to stop running tasks
  - CLI: `codegeass task stop <task-id>`
  - Dashboard: Stop button on running tasks

- **Refactor Skill**: Automated code cleanup and modularization (`/refactor`)
  - Split monolithic files into single-responsibility modules
  - Phase 5: Functional testing to verify CLI after refactoring

- **Dashboard Enhancements**
  - Native folder picker for working directory selection
  - Project selector dropdown for task creation/editing

- **API Documentation**: Comprehensive OpenAPI descriptions (#10)
  - All 67+ FastAPI endpoints with summary, description, and response codes
  - Enhanced Python library docstrings for execution strategies

### Changed

- **Execution Layer Modularization**: Split monolithic modules (#3, #8)
  - `strategies/` subpackage (8 files, ~672 lines split)
  - `tracker/` subpackage (4 files, ~591 lines split)
  - `plan_service/` subpackage (4 files, ~737 lines split)
  - CLI commands split into focused submodules

- Replaced `pymsteams` with `httpx` for Teams notifications

### Fixed

- Circular import between `approval_repository` and `plan_service` (TYPE_CHECKING guard)
- Channel lookup now supports both ID and name
- `DATA_DIR` → `data_dir` typo in execution_service.py
- MyPy configuration for optional dependencies
- CI lint errors and test failures

## [0.1.4] - 2025-01-30

### Added

- **New CodeGeass Logo**: Custom logo added across all platforms
- Logo in dashboard sidebar with transparent background
- Favicons (16x16, 32x32, 180x180, .ico) for dashboard and docs
- Logo in MkDocs documentation header
- Logo in README (visible on GitHub and PyPI)

### Fixed

- Added missing `src/lib/utils.ts` and `src/lib/api.ts` files for dashboard frontend
- Dashboard now starts correctly without import errors

## [0.1.3] - 2025-01-29

### Added

- **Integrated Dashboard**: `codegeass dashboard` command now starts the web dashboard
- Dashboard included in the pip package (no separate installation needed)
- FastAPI, uvicorn, and websockets added as default dependencies

### Changed

- Dashboard is now part of the core package, not a separate install

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

[Unreleased]: https://github.com/DonTizi/CodeGeass/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/DonTizi/CodeGeass/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DonTizi/CodeGeass/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/DonTizi/CodeGeass/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/DonTizi/CodeGeass/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/DonTizi/CodeGeass/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/DonTizi/CodeGeass/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DonTizi/CodeGeass/releases/tag/v0.1.0
