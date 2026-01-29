"""Task models for API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    last_run: str | None = None
    last_status: str | None = None

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
