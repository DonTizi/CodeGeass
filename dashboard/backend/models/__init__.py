"""Pydantic models for CodeGeass Dashboard API."""

from .task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskSummary,
    TaskStats,
)
from .skill import (
    Skill,
    SkillSummary,
)
from .execution import (
    ExecutionResult,
    ExecutionStatus,
    LogStats,
    LogFilter,
)
from .scheduler import (
    SchedulerStatus,
    UpcomingRun,
)

__all__ = [
    # Task
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskSummary",
    "TaskStats",
    # Skill
    "Skill",
    "SkillSummary",
    # Execution
    "ExecutionResult",
    "ExecutionStatus",
    "LogStats",
    "LogFilter",
    # Scheduler
    "SchedulerStatus",
    "UpcomingRun",
]
