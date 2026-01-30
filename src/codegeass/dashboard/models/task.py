"""Task models for API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskNotificationConfig(BaseModel):
    """Notification configuration for a task."""
    channels: list[str] = Field(default_factory=list, description="Channel IDs to notify")
    events: list[str] = Field(default_factory=list, description="Events to notify on")
    include_output: bool = Field(False, description="Include task output in notification")


class TaskStatus(str, Enum):
    """Task execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"


class TaskSummary(BaseModel):
    """Summary view of a task."""
    id: str
    name: str
    schedule: str
    skill: str | None = None
    enabled: bool = True
    last_run: str | None = None
    last_status: str | None = None
    next_run: str | None = None


class Task(BaseModel):
    """Full task model."""
    id: str
    name: str
    schedule: str
    working_dir: str
    skill: str | None = None
    prompt: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    model: str = "sonnet"
    autonomous: bool = False
    max_turns: int | None = None
    timeout: int = 300
    enabled: bool = True
    variables: dict[str, Any] = Field(default_factory=dict)
    notifications: TaskNotificationConfig | None = None
    last_run: str | None = None
    last_status: str | None = None

    # Plan mode configuration
    plan_mode: bool = False
    plan_timeout: int = 3600
    plan_max_iterations: int = 5

    # Computed fields for UI
    next_run: str | None = None
    schedule_description: str | None = None


class TaskCreate(BaseModel):
    """Model for creating a new task."""
    name: str = Field(..., min_length=1, max_length=100)
    schedule: str = Field(..., description="CRON expression")
    working_dir: str = Field(..., description="Working directory (absolute path)")
    skill: str | None = Field(None, description="Skill name to execute")
    prompt: str | None = Field(None, description="Direct prompt (if no skill)")
    allowed_tools: list[str] = Field(default_factory=list)
    model: str = Field("sonnet", pattern="^(haiku|sonnet|opus)$")
    autonomous: bool = False
    max_turns: int | None = Field(None, ge=1, le=100)
    timeout: int = Field(300, ge=30, le=3600)
    enabled: bool = True
    variables: dict[str, Any] = Field(default_factory=dict)
    notifications: TaskNotificationConfig | None = None
    plan_mode: bool = Field(False, description="Enable interactive plan approval")
    plan_timeout: int = Field(3600, ge=300, le=86400, description="Approval timeout in seconds")
    plan_max_iterations: int = Field(5, ge=1, le=20, description="Max discuss rounds")


class TaskUpdate(BaseModel):
    """Model for updating a task."""
    name: str | None = Field(None, min_length=1, max_length=100)
    schedule: str | None = None
    working_dir: str | None = None
    skill: str | None = None
    prompt: str | None = None
    allowed_tools: list[str] | None = None
    model: str | None = Field(None, pattern="^(haiku|sonnet|opus)$")
    autonomous: bool | None = None
    max_turns: int | None = Field(None, ge=1, le=100)
    timeout: int | None = Field(None, ge=30, le=3600)
    enabled: bool | None = None
    variables: dict[str, Any] | None = None
    notifications: TaskNotificationConfig | None = None
    plan_mode: bool | None = None
    plan_timeout: int | None = Field(None, ge=300, le=86400)
    plan_max_iterations: int | None = Field(None, ge=1, le=20)


class TaskStats(BaseModel):
    """Statistics for a task."""
    task_id: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    timeout_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    last_run: str | None = None
    last_status: str | None = None
