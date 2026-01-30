"""Execution and log models for API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"


class ExecutionResult(BaseModel):
    """Result of a task execution."""
    task_id: str
    task_name: str | None = None
    session_id: str | None = None
    status: ExecutionStatus
    output: str = ""
    clean_output: str = ""  # Parsed human-readable output from stream-json
    error: str | None = None
    exit_code: int | None = None
    started_at: str
    finished_at: str | None = None
    duration_seconds: float | None = None


class LogFilter(BaseModel):
    """Filter for log queries."""
    status: ExecutionStatus | None = None
    task_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class LogStats(BaseModel):
    """Overall log statistics."""
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    timeout: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    last_execution: str | None = None

    # Per-task breakdown
    by_task: dict[str, dict[str, Any]] = Field(default_factory=dict)
