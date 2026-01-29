# CodeGeass Dashboard

A web interface for managing CodeGeass scheduled tasks, built with FastAPI (backend) and React (frontend).

## Overview

CodeGeass Dashboard provides a visual interface to:
- **CRUD Tasks**: Create, read, update, and delete scheduled tasks
- **Manage Skills**: View and reload Claude Code skills
- **Monitor Logs**: Visualize execution history with success/failure stats
- **Scheduler Status**: Real-time scheduler monitoring and manual task execution

## Quick Start

```bash
# First-time setup
./setup.sh

# Run the dashboard
./run.sh
```

Then open http://localhost:5173

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                     http://localhost:5173                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  Dashboard  │  │    Tasks    │  │   Skills    │  │  Logs   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                            │                                     │
│                    Zustand Stores + API Client                   │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┼─────────────────────────────────────┐
│                         Backend (FastAPI)                        │
│                     http://localhost:8001                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ /api/tasks  │  │ /api/skills │  │  /api/logs  │  │scheduler│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                            │                                     │
│                      Service Layer                               │
└────────────────────────────┼─────────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────────┐
│                    CodeGeass Core (Python)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │TaskRepository│ │SkillRegistry│  │LogRepository│  │Scheduler│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                            │                                     │
│  config/schedules.yaml    .claude/skills/     data/logs/*.jsonl  │
└──────────────────────────────────────────────────────────────────┘
```

## CRON Expression Syntax

CodeGeass uses standard CRON expressions with 5 fields:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, 0=Sunday)
│ │ │ │ │
* * * * *
```

### Examples

| Expression | Description |
|------------|-------------|
| `0 9 * * 1-5` | Every weekday at 9:00 AM |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 * * 0` | Every Sunday at midnight |
| `30 14 1 * *` | 1st of each month at 2:30 PM |
| `0 */2 * * *` | Every 2 hours |

### Special Strings

| String | Equivalent |
|--------|------------|
| `@hourly` | `0 * * * *` |
| `@daily` | `0 0 * * *` |
| `@weekly` | `0 0 * * 0` |
| `@monthly` | `0 0 1 * *` |
| `@yearly` | `0 0 1 1 *` |

## Claude SDK Integration

CodeGeass executes tasks using Claude Code CLI. Each task can use one of three execution strategies:

### 1. Skill Strategy (Recommended)
```yaml
tasks:
  - name: daily-review
    schedule: "0 9 * * 1-5"
    skill: code-review        # Uses /.claude/skills/code-review/SKILL.md
    working_dir: /path/to/project
```

Executes: `claude -p "/code-review" --output-format json`

### 2. Direct Prompt Strategy
```yaml
tasks:
  - name: test-runner
    schedule: "0 */4 * * *"
    prompt: "Run all tests and report failures"
    working_dir: /path/to/project
```

Executes: `claude -p "Run all tests..." --output-format json`

### 3. Autonomous Strategy
```yaml
tasks:
  - name: auto-fix
    schedule: "0 2 * * *"
    prompt: "Fix all linting errors"
    autonomous: true          # Skips permission prompts
    working_dir: /path/to/project
```

Executes: `claude -p "Fix all..." --dangerously-skip-permissions --output-format json`

### Task Configuration Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Unique task identifier |
| `schedule` | string | required | CRON expression |
| `working_dir` | string | required | Absolute path to working directory |
| `skill` | string | null | Skill name to execute |
| `prompt` | string | null | Direct prompt (if no skill) |
| `model` | string | "sonnet" | Model: haiku, sonnet, opus |
| `timeout` | int | 300 | Execution timeout in seconds |
| `max_turns` | int | null | Max agentic turns |
| `enabled` | bool | true | Whether task is active |
| `autonomous` | bool | false | Skip permission prompts |
| `allowed_tools` | list | [] | Restrict available tools |
| `variables` | dict | {} | Template variables |

## Directory Structure

```
dashboard/
├── backend/                 # FastAPI API server
│   ├── main.py             # Entry point
│   ├── config.py           # Configuration
│   ├── dependencies.py     # Dependency injection
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic (wraps core)
│   └── routers/            # API endpoints
│
├── frontend/               # React + Vite application
│   ├── src/
│   │   ├── types/         # TypeScript interfaces
│   │   ├── lib/           # API client, utilities
│   │   ├── stores/        # Zustand state management
│   │   ├── components/    # React components
│   │   └── pages/         # Route pages
│   └── index.css          # Claude Design System
│
├── run.sh                  # Start both servers
├── setup.sh               # First-time setup
└── README.md              # This file
```

## API Reference

See [backend/README.md](backend/README.md) for full API documentation.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create a task |
| POST | `/api/tasks/{id}/run` | Run task manually |
| GET | `/api/skills` | List available skills |
| GET | `/api/logs` | Get execution history |
| GET | `/api/scheduler/status` | Scheduler status |

## Design System

The dashboard uses the Claude Design System:

- **Primary**: #C15F3C (rust-orange)
- **Background**: #F4F3EE (off-white)
- **Foreground**: #3d3929 (dark brown)
- **Typography**: Georgia (headers), Inter (body)

## Development

```bash
# Backend only
cd backend
source venv/bin/activate
PYTHONPATH=../../src uvicorn main:app --port 8001 --reload

# Frontend only
cd frontend
npm run dev

# Build frontend for production
npm run build
```

## Troubleshooting

### Port already in use
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Backend import errors
Ensure PYTHONPATH includes the codegeass source:
```bash
export PYTHONPATH=/path/to/codegeass/src:$PYTHONPATH
```

### Frontend build errors
```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```
