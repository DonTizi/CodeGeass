# CodeGeass Architecture

This document describes the complete architecture of the CodeGeass scheduled task system and its Dashboard interface.

## System Overview

CodeGeass is a scheduler framework for automating Claude Code sessions. It allows you to define tasks that run on a schedule, executing Claude Code skills or prompts against your codebase.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           User Interface Layer                            │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │     Dashboard (React)      │  │        CLI (Click)                 │  │
│  │    http://localhost:5173   │  │    codegeass <command>            │  │
│  └────────────────────────────┘  └────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────┬┘
                                 │                                        │
┌────────────────────────────────┼────────────────────────────────────────┼┐
│                           API Layer                                      ││
│  ┌────────────────────────────┐                                          ││
│  │    FastAPI Backend         │◄─────────────────────────────────────────┘│
│  │   http://localhost:8001    │                                          │
│  └────────────────────────────┘                                          │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────────────┐
│                          Service Layer                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ TaskService  │ │ SkillService │ │  LogService  │ │ SchedulerService │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘ │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────────────┐
│                           Core Layer                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │TaskRepository│ │SkillRegistry │ │LogRepository │ │    Scheduler     │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────┴────────────────────────────────────┐   │
│  │                       ClaudeExecutor                               │   │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌───────────────────────┐  │   │
│  │  │SkillStrategy│  │ HeadlessStrategy│  │  AutonomousStrategy   │  │   │
│  │  └─────────────┘  └─────────────────┘  └───────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────────────┐
│                         Storage Layer                                     │
│  ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────────┐  │
│  │ config/          │  │ data/logs/        │  │ .claude/skills/       │  │
│  │ schedules.yaml   │  │ *.jsonl           │  │ */SKILL.md            │  │
│  └──────────────────┘  └───────────────────┘  └───────────────────────┘  │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────────────┐
│                        External Systems                                   │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                      Claude Code CLI                              │    │
│  │     claude -p "<prompt>" --output-format json --model sonnet      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Core Domain Layer (`src/codegeass/core/`)

#### Entities

```python
@dataclass
class Task:
    """A scheduled task definition."""
    id: str                     # Auto-generated 8-char UUID
    name: str                   # Unique task name
    schedule: str               # CRON expression
    working_dir: Path           # Execution directory

    # Execution config
    skill: str | None           # Skill to execute
    prompt: str | None          # Direct prompt (if no skill)
    allowed_tools: list[str]    # Tool restrictions
    model: str                  # haiku, sonnet, opus
    autonomous: bool            # Skip permissions
    max_turns: int | None       # Agentic turn limit
    timeout: int                # Seconds

    # State
    enabled: bool               # Is active
    variables: dict             # Template variables
    last_run: str | None        # ISO timestamp
    last_status: str | None     # success/failure/timeout/skipped/running

@dataclass
class Skill:
    """A Claude Code skill definition."""
    name: str                   # Skill identifier
    path: Path                  # Path to skill directory
    description: str            # From SKILL.md frontmatter
    allowed_tools: list[str]    # Tool restrictions
    context: str                # inline or fork
    agent: str | None           # Custom agent
    content: str                # Rendered SKILL.md content

@dataclass(frozen=True)
class ExecutionResult:
    """Result of a task execution."""
    task_id: str
    session_id: str | None
    status: ExecutionStatus     # Enum
    output: str                 # STDOUT
    error: str | None           # Error message
    exit_code: int | None
    started_at: datetime
    finished_at: datetime

    @property
    def duration_seconds(self) -> float

    @property
    def is_success(self) -> bool
```

#### Value Objects

```python
class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"

@dataclass(frozen=True)
class CronExpression:
    """Validated CRON expression."""
    expression: str

    def get_next(self) -> datetime
    def get_description(self) -> str
    def is_due(self, window_seconds: int = 60) -> bool
```

### 2. Storage Layer (`src/codegeass/storage/`)

#### TaskRepository

Manages task persistence in YAML format.

```python
class TaskRepository:
    def __init__(self, config_path: Path):
        """Load tasks from config/schedules.yaml"""

    # CRUD
    def save(self, task: Task) -> None
    def find_by_id(self, task_id: str) -> Task | None
    def find_by_name(self, name: str) -> Task | None
    def find_all(self) -> list[Task]
    def delete(self, task_id: str) -> bool
    def update(self, task: Task) -> None

    # Queries
    def find_enabled(self) -> list[Task]
    def find_due(self, window_seconds: int = 60) -> list[Task]

    # State changes
    def enable(self, task_id: str) -> bool
    def disable(self, task_id: str) -> bool
```

**Storage Format** (`config/schedules.yaml`):

```yaml
tasks:
  - id: abc12345
    name: daily-review
    schedule: "0 9 * * 1-5"
    working_dir: /home/user/project
    skill: code-review
    model: sonnet
    timeout: 300
    enabled: true
    last_run: "2026-01-29T09:15:32.123456"
    last_status: success
```

#### LogRepository

Manages execution logs in JSON Lines format.

```python
class LogRepository:
    def __init__(self, logs_dir: Path):
        """Logs stored in data/logs/*.jsonl"""

    # Write
    def save(self, result: ExecutionResult) -> None

    # Read
    def find_by_task_id(self, task_id: str, limit: int = 10) -> list[ExecutionResult]
    def find_latest(self, task_id: str) -> ExecutionResult | None
    def find_all(self, limit: int = 100) -> list[ExecutionResult]
    def find_by_status(self, status: str, limit: int = 100) -> list[ExecutionResult]
    def find_by_date_range(self, start: datetime, end: datetime) -> list[ExecutionResult]

    # Analytics
    def get_task_stats(self, task_id: str) -> dict

    # Maintenance
    def clear_task_logs(self, task_id: str) -> bool
    def tail(self, task_id: str, lines: int = 20) -> list[ExecutionResult]
```

**Storage Format** (`data/logs/{task_id}.jsonl`):

```jsonl
{"task_id":"abc12345","session_id":"sess-xyz","status":"success","output":"...","started_at":"2026-01-29T09:00:00","finished_at":"2026-01-29T09:01:30","duration_seconds":90.5}
{"task_id":"abc12345","session_id":"sess-abc","status":"failure","error":"Command failed","started_at":"2026-01-29T10:00:00","finished_at":"2026-01-29T10:00:05","duration_seconds":5.0}
```

### 3. Factory Layer (`src/codegeass/factory/`)

#### SkillRegistry (Singleton)

Discovers and manages Claude Code skills.

```python
class SkillRegistry:
    @classmethod
    def get_instance(cls, skills_dir: Path | None = None) -> SkillRegistry

    def get(self, name: str) -> Skill              # Raises SkillNotFoundError
    def get_all(self) -> list[Skill]
    def exists(self, name: str) -> bool
    def reload(self) -> None                       # Rescan disk
```

**Skill Discovery:**

Scans `.claude/skills/*/SKILL.md` for skill definitions following the Claude Code skill format:

```markdown
---
description: Review code for issues
allowed-tools:
  - Read
  - Grep
  - Glob
context: inline
---

# Code Review

Review the codebase for:
1. Code quality issues
2. Security vulnerabilities
3. Performance problems

$ARGUMENTS
```

### 4. Execution Layer (`src/codegeass/execution/`)

#### ClaudeExecutor

Orchestrates task execution by selecting and running the appropriate strategy.

```python
class ClaudeExecutor:
    def __init__(self, skill_registry: SkillRegistry,
                 session_manager: SessionManager,
                 log_repository: LogRepository):
        pass

    def execute(self, task: Task, dry_run: bool = False) -> ExecutionResult
    def get_command(self, task: Task) -> list[str]  # For debugging
```

#### Execution Strategies

```python
class SkillStrategy(BaseStrategy):
    """Execute using a skill invocation."""
    # Command: claude -p "/skill-name arguments" --output-format json

class HeadlessStrategy(BaseStrategy):
    """Execute using a direct prompt."""
    # Command: claude -p "prompt" --output-format json --model sonnet

class AutonomousStrategy(BaseStrategy):
    """Execute with permission skipping."""
    # Command: claude -p "prompt" --dangerously-skip-permissions --output-format json
```

**Strategy Selection Logic:**

```python
if task.skill:
    return SkillStrategy()
elif task.autonomous:
    return AutonomousStrategy()
else:
    return HeadlessStrategy()
```

#### SessionManager

Tracks execution sessions.

```python
class SessionManager:
    def __init__(self, sessions_dir: Path):
        """Sessions stored in data/sessions/*.json"""

    def create_session(self, task_id: str, metadata: dict = None) -> Session
    def get_session(self, session_id: str) -> Session | None
    def complete_session(self, session_id: str, status: str, output: str, error: str = None) -> Session
    def get_sessions_for_task(self, task_id: str, limit: int = 10) -> list[Session]
    def cleanup_old_sessions(self, days: int = 30) -> int
```

### 5. Scheduling Layer (`src/codegeass/scheduling/`)

#### Scheduler

Main scheduling orchestrator.

```python
class Scheduler:
    def __init__(self, task_repository: TaskRepository,
                 skill_registry: SkillRegistry,
                 session_manager: SessionManager,
                 log_repository: LogRepository,
                 max_concurrent: int = 1):
        pass

    # Query
    def find_due_tasks(self, window_seconds: int = 60) -> list[Task]
    def get_upcoming(self, hours: int = 24) -> list[dict]
    def status(self) -> dict

    # Execute
    def run_task(self, task: Task, dry_run: bool = False) -> ExecutionResult
    def run_due(self, window_seconds: int = 60, dry_run: bool = False) -> list[ExecutionResult]
    def run_all(self, dry_run: bool = False) -> list[ExecutionResult]
    def run_by_name(self, name: str, dry_run: bool = False) -> ExecutionResult | None

    # Callbacks
    def set_callbacks(self, on_start: Callable, on_complete: Callable) -> None
```

#### CronParser

CRON expression utilities built on `croniter`.

```python
class CronParser:
    @classmethod
    def validate(cls, expression: str) -> bool

    @classmethod
    def get_next(cls, expression: str, base_time: datetime = None) -> datetime

    @classmethod
    def get_prev(cls, expression: str, base_time: datetime = None) -> datetime

    @classmethod
    def get_next_n(cls, expression: str, n: int, base_time: datetime = None) -> list[datetime]

    @classmethod
    def is_due(cls, expression: str, window_seconds: int = 60) -> bool

    @classmethod
    def describe(cls, expression: str) -> str  # Human-readable

    @classmethod
    def normalize(cls, expression: str) -> str  # Expand @daily, etc.
```

### 6. CLI Layer (`src/codegeass/cli/`)

Command-line interface built with Click.

```python
@click.group()
@click.pass_context
def cli(ctx):
    """CodeGeass - Claude Code Scheduler"""
    ctx.obj = Context()

# Task commands
@cli.group()
def task():
    """Manage scheduled tasks"""

@task.command('list')
@task.command('create')
@task.command('show')
@task.command('edit')
@task.command('delete')
@task.command('enable')
@task.command('disable')
@task.command('run')

# Skill commands
@cli.group()
def skill():
    """Manage skills"""

@skill.command('list')
@skill.command('show')
@skill.command('reload')

# Scheduler commands
@cli.group()
def scheduler():
    """Control the scheduler"""

@scheduler.command('status')
@scheduler.command('run-due')
@scheduler.command('upcoming')

# Log commands
@cli.group()
def logs():
    """View execution logs"""

@logs.command('list')
@logs.command('show')
@logs.command('stats')
@logs.command('clear')
```

## Data Flow

### Task Creation Flow

```
User creates task via Dashboard or CLI
         │
         ▼
    ┌─────────────┐
    │ Validate    │◄──── CRON expression validation
    │ input       │◄──── Check unique name
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │TaskRepository│
    │    .save()   │
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │ schedules   │
    │   .yaml     │
    └─────────────┘
```

### Task Execution Flow

```
Scheduler checks for due tasks (every 60s)
         │
         ▼
    ┌─────────────────┐
    │ find_due_tasks()│
    └─────────────────┘
         │
         ▼ (for each due task)
    ┌─────────────────┐
    │ Create Session  │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Select Strategy │
    │ (skill/prompt/  │
    │  autonomous)    │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Build command   │────► claude -p "/skill" --output-format json
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ subprocess.run()│
    │ with timeout    │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Capture output  │
    │ Parse JSON      │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ Create          │
    │ ExecutionResult │
    └─────────────────┘
         │
         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ LogRepository   │      │ TaskRepository  │
    │   .save()       │      │  .update()      │
    └─────────────────┘      └─────────────────┘
         │                          │
         ▼                          ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ {task_id}.jsonl │      │ Update last_run │
    └─────────────────┘      │ and last_status │
                             └─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_MODEL` | sonnet | Default model |
| `CODEGEASS_CONFIG` | config/ | Config directory |
| `CODEGEASS_DATA` | data/ | Data directory |
| `CODEGEASS_SKILLS` | .claude/skills/ | Skills directory |

### Configuration Files

```
codegeass/
├── config/
│   ├── settings.yaml      # Global settings
│   └── schedules.yaml     # Task definitions
├── data/
│   ├── logs/              # Execution logs
│   │   ├── {task_id}.jsonl
│   │   └── all.jsonl      # Aggregated
│   └── sessions/          # Session data
│       └── {session_id}.json
└── .claude/
    └── skills/            # Skill definitions
        ├── code-review/
        │   └── SKILL.md
        └── test-generator/
            └── SKILL.md
```

### settings.yaml

```yaml
claude:
  default_model: sonnet     # haiku, sonnet, opus
  default_timeout: 300      # Seconds
  unset_api_key: true       # Use subscription, not API key

paths:
  skills: .claude/skills/
  logs: data/logs/
  sessions: data/sessions/

scheduler:
  check_interval: 60        # Seconds between checks
  max_concurrent: 1         # Parallel executions
```

## Error Handling

### Exception Hierarchy

```python
class CodeGeassError(Exception):
    """Base exception."""

class ConfigurationError(CodeGeassError):
    """Invalid configuration."""

class ValidationError(CodeGeassError):
    """Validation failed."""

class TaskNotFoundError(CodeGeassError):
    """Task doesn't exist."""
    def __init__(self, task_id: str):
        self.task_id = task_id

class SkillNotFoundError(CodeGeassError):
    """Skill doesn't exist."""
    def __init__(self, skill_name: str):
        self.skill_name = skill_name

class ExecutionError(CodeGeassError):
    """Task execution failed."""
    def __init__(self, message: str, task_id: str = None, cause: Exception = None):
        self.task_id = task_id
        self.cause = cause

class SchedulingError(CodeGeassError):
    """Scheduling operation failed."""
```

## Security Considerations

### Autonomous Mode

When `autonomous: true`, tasks run with `--dangerously-skip-permissions`:
- No user confirmation required
- Full file system access
- Network access enabled
- Use with caution for trusted operations only

### Recommendations

1. **Limit autonomous tasks** - Only use for well-tested, trusted operations
2. **Review skill definitions** - Check allowed tools and prompts
3. **Monitor logs** - Regularly review execution history
4. **Use tool restrictions** - Set `allowed_tools` to minimum required
5. **Secure config files** - Protect schedules.yaml with proper permissions

## Performance

### Scaling Considerations

- **Single instance**: Designed for single-machine operation
- **Sequential execution**: `max_concurrent: 1` by default
- **Log rotation**: Implement cleanup for long-running deployments
- **Memory**: Skills are loaded on demand, not cached permanently

### Optimization Tips

1. Use Haiku model for simple tasks (faster, cheaper)
2. Set appropriate timeouts to prevent hanging
3. Limit max_turns for predictable execution time
4. Clear old logs periodically
