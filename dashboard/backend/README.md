# CodeGeass Dashboard - Backend

FastAPI backend for the CodeGeass Dashboard. Provides REST API endpoints for managing scheduled tasks, skills, logs, and the scheduler.

## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
PYTHONPATH=../../src uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

API available at http://localhost:8001

## Architecture

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── dependencies.py      # Dependency injection (singletons)
├── requirements.txt     # Python dependencies
│
├── models/              # Pydantic models for API
│   ├── __init__.py
│   ├── task.py          # Task, TaskCreate, TaskUpdate, TaskStats
│   ├── skill.py         # Skill, SkillSummary
│   ├── execution.py     # ExecutionResult, LogStats, LogFilter
│   └── scheduler.py     # SchedulerStatus, UpcomingRun
│
├── services/            # Business logic layer
│   ├── __init__.py
│   ├── task_service.py      # Wraps TaskRepository
│   ├── skill_service.py     # Wraps SkillRegistry
│   ├── log_service.py       # Wraps LogRepository
│   └── scheduler_service.py # Wraps Scheduler
│
└── routers/             # API route handlers
    ├── __init__.py
    ├── tasks.py         # /api/tasks/*
    ├── skills.py        # /api/skills/*
    ├── logs.py          # /api/logs/*
    └── scheduler.py     # /api/scheduler/*
```

## API Reference

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T09:00:00.000000"
}
```

---

### Tasks API

#### List All Tasks

```http
GET /api/tasks
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `summary_only` | bool | false | Return lighter weight summaries |

**Response:**
```json
[
  {
    "id": "abc12345",
    "name": "daily-review",
    "schedule": "0 9 * * 1-5",
    "working_dir": "/home/user/project",
    "skill": "code-review",
    "prompt": null,
    "allowed_tools": [],
    "model": "sonnet",
    "autonomous": false,
    "max_turns": null,
    "timeout": 300,
    "enabled": true,
    "variables": {},
    "last_run": "2026-01-29T09:00:00.000000",
    "last_status": "success",
    "next_run": "2026-01-30T09:00:00.000000",
    "schedule_description": "At 09:00 on weekdays"
  }
]
```

#### Get Single Task

```http
GET /api/tasks/{task_id}
```

**Response:** Same as single item from list

#### Create Task

```http
POST /api/tasks
Content-Type: application/json

{
  "name": "my-task",
  "schedule": "0 9 * * 1-5",
  "working_dir": "/home/user/project",
  "skill": "code-review",
  "model": "sonnet",
  "timeout": 300,
  "enabled": true
}
```

**Required Fields:**
- `name` - Unique task name (1-100 chars)
- `schedule` - Valid CRON expression
- `working_dir` - Absolute path

**Optional Fields:**
- `skill` - Skill name to execute
- `prompt` - Direct prompt (if no skill)
- `model` - haiku, sonnet, or opus (default: sonnet)
- `timeout` - 30-3600 seconds (default: 300)
- `max_turns` - 1-100 (default: null)
- `enabled` - boolean (default: true)
- `autonomous` - boolean (default: false)
- `allowed_tools` - list of tool names
- `variables` - dict of template variables

**Response:** Created task object (201)

**Errors:**
- 400: Invalid CRON expression
- 400: Task name already exists

#### Update Task

```http
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "schedule": "0 10 * * 1-5",
  "enabled": false
}
```

All fields are optional. Only provided fields are updated.

**Response:** Updated task object

#### Delete Task

```http
DELETE /api/tasks/{task_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task abc12345 deleted"
}
```

#### Enable Task

```http
POST /api/tasks/{task_id}/enable
```

**Response:**
```json
{
  "status": "success",
  "message": "Task abc12345 enabled"
}
```

#### Disable Task

```http
POST /api/tasks/{task_id}/disable
```

**Response:**
```json
{
  "status": "success",
  "message": "Task abc12345 disabled"
}
```

#### Run Task Manually

```http
POST /api/tasks/{task_id}/run?dry_run=false
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dry_run` | bool | false | Simulate without executing |

**Response:**
```json
{
  "task_id": "abc12345",
  "task_name": "daily-review",
  "session_id": "session-xyz",
  "status": "success",
  "output": "Task completed successfully...",
  "error": null,
  "exit_code": 0,
  "started_at": "2026-01-29T09:00:00.000000",
  "finished_at": "2026-01-29T09:01:30.000000",
  "duration_seconds": 90.5
}
```

**Status Values:**
- `success` - Task completed successfully
- `failure` - Task failed with error
- `timeout` - Task exceeded timeout
- `skipped` - Task was skipped
- `running` - Task is currently executing

#### Get Task Statistics

```http
GET /api/tasks/{task_id}/stats
```

**Response:**
```json
{
  "task_id": "abc12345",
  "total_runs": 150,
  "successful_runs": 142,
  "failed_runs": 5,
  "timeout_runs": 3,
  "success_rate": 94.67,
  "avg_duration_seconds": 45.2,
  "last_run": "2026-01-29T09:00:00.000000",
  "last_status": "success"
}
```

---

### Skills API

#### List All Skills

```http
GET /api/skills
```

**Response:**
```json
[
  {
    "name": "code-review",
    "description": "Review code for issues and improvements",
    "context": "inline",
    "has_agent": false
  },
  {
    "name": "test-generator",
    "description": "Generate unit tests for functions",
    "context": "fork",
    "has_agent": true
  }
]
```

#### Get Skill Details

```http
GET /api/skills/{name}
```

**Response:**
```json
{
  "name": "code-review",
  "path": "/home/user/project/.claude/skills/code-review",
  "description": "Review code for issues and improvements",
  "allowed_tools": ["Read", "Grep", "Glob"],
  "context": "inline",
  "agent": null,
  "disable_model_invocation": false,
  "content": "# Code Review Skill\n\nReview the codebase...",
  "dynamic_commands": ["git diff", "npm test"]
}
```

#### Reload Skills from Disk

```http
POST /api/skills/reload
```

Rescans the `.claude/skills/` directory for skill definitions.

**Response:** Updated list of skills

#### Preview Skill Content

```http
GET /api/skills/{name}/preview?arguments=src/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `arguments` | string | "" | Arguments to pass to skill |

**Response:**
```json
{
  "name": "code-review",
  "arguments": "src/",
  "content": "# Code Review Skill\n\nReview the code in src/..."
}
```

---

### Logs API

#### List Execution Logs

```http
GET /api/logs?status=success&task_id=abc12345&limit=50
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter by status |
| `task_id` | string | null | Filter by task ID |
| `start_date` | string | null | ISO date filter start |
| `end_date` | string | null | ISO date filter end |
| `limit` | int | 100 | Max results (1-1000) |
| `offset` | int | 0 | Pagination offset |

**Response:**
```json
[
  {
    "task_id": "abc12345",
    "task_name": "daily-review",
    "session_id": "session-xyz",
    "status": "success",
    "output": "Review completed...",
    "error": null,
    "exit_code": 0,
    "started_at": "2026-01-29T09:00:00.000000",
    "finished_at": "2026-01-29T09:01:30.000000",
    "duration_seconds": 90.5
  }
]
```

#### Get Logs for Specific Task

```http
GET /api/logs/task/{task_id}?limit=10
```

**Response:** Array of execution results for that task

#### Get Latest Log for Task

```http
GET /api/logs/task/{task_id}/latest
```

**Response:** Single most recent execution result

#### Get Overall Statistics

```http
GET /api/logs/stats
```

**Response:**
```json
{
  "total_executions": 1500,
  "successful": 1420,
  "failed": 50,
  "timeout": 30,
  "success_rate": 94.67,
  "avg_duration_seconds": 42.3,
  "last_execution": "2026-01-29T09:00:00.000000",
  "by_task": {
    "abc12345": {
      "name": "daily-review",
      "total": 150,
      "success": 142,
      "failure": 5,
      "success_rate": 94.67
    }
  }
}
```

#### Clear Logs for Task

```http
DELETE /api/logs/task/{task_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Logs for task abc12345 cleared"
}
```

---

### Scheduler API

#### Get Scheduler Status

```http
GET /api/scheduler/status
```

**Response:**
```json
{
  "running": true,
  "check_interval": 60,
  "max_concurrent": 1,
  "total_tasks": 10,
  "enabled_tasks": 8,
  "due_tasks": 2,
  "last_check": "2026-01-29T08:59:00.000000",
  "next_check": "2026-01-29T09:00:00.000000"
}
```

#### Get Upcoming Runs

```http
GET /api/scheduler/upcoming?hours=24
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | int | 24 | Hours to look ahead (1-168) |

**Response:**
```json
[
  {
    "task_id": "abc12345",
    "task_name": "daily-review",
    "schedule": "0 9 * * 1-5",
    "next_run": "2026-01-29T09:00:00.000000",
    "skill": "code-review",
    "enabled": true
  }
]
```

#### Run Due Tasks

```http
POST /api/scheduler/run-due?window_seconds=60&dry_run=false
```

Executes all tasks that are due within the time window.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `window_seconds` | int | 60 | Time window (30-3600) |
| `dry_run` | bool | false | Simulate without executing |

**Response:** Array of execution results

#### Get Due Tasks

```http
GET /api/scheduler/due?window_seconds=60
```

**Response:**
```json
[
  {
    "id": "abc12345",
    "name": "daily-review",
    "schedule": "0 9 * * 1-5",
    "skill": "code-review"
  }
]
```

---

### CRON Validation

```http
POST /api/cron/validate
Content-Type: application/json

{
  "expression": "0 9 * * 1-5"
}
```

**Response (valid):**
```json
{
  "valid": true,
  "description": "At 09:00 on weekdays",
  "next_runs": [
    "2026-01-29T09:00:00",
    "2026-01-30T09:00:00",
    "2026-02-02T09:00:00",
    "2026-02-03T09:00:00",
    "2026-02-04T09:00:00"
  ]
}
```

**Response (invalid):**
```json
{
  "valid": false,
  "error": "Invalid CRON expression"
}
```

---

## Service Layer

The backend uses a service layer pattern to wrap the CodeGeass core components:

| Service | Wraps | Purpose |
|---------|-------|---------|
| `TaskService` | `TaskRepository` | CRUD operations on tasks |
| `SkillService` | `SkillRegistry` | Skill discovery and preview |
| `LogService` | `LogRepository` | Execution history queries |
| `SchedulerService` | `Scheduler` | Task execution and scheduling |

### Dependency Injection

Services are singletons, created on first access:

```python
from dependencies import get_task_service

service = get_task_service()
tasks = service.list_tasks()
```

## Configuration

Settings in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `PROJECT_DIR` | Parent of backend | CodeGeass root |
| `CONFIG_DIR` | `{PROJECT_DIR}/config` | YAML configs |
| `DATA_DIR` | `{PROJECT_DIR}/data` | Logs, sessions |
| `SKILLS_DIR` | `{PROJECT_DIR}/.claude/skills` | Skill definitions |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8001 | Server port |
| `CORS_ORIGINS` | localhost:5173 | Allowed origins |

## Error Handling

All errors return JSON:

```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (validation error) |
| 404 | Resource not found |
| 500 | Internal server error |

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload --port 8001

# Run with custom PYTHONPATH
PYTHONPATH=/path/to/codegeass/src uvicorn main:app --port 8001
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test tasks endpoint
curl http://localhost:8001/api/tasks

# Test CRON validation
curl -X POST http://localhost:8001/api/cron/validate \
  -H "Content-Type: application/json" \
  -d '{"expression": "0 9 * * 1-5"}'
```
