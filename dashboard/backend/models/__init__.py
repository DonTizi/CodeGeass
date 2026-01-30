"""Pydantic models for CodeGeass Dashboard API."""

from .task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskSummary,
    TaskStats,
    TaskNotificationConfig,
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
from .notification import (
    Channel,
    ChannelCreate,
    ChannelUpdate,
    NotificationConfig,
    NotificationEvent,
    ProviderInfo,
    TestResult,
)
from .approval import (
    Approval,
    ApprovalSummary,
    ApprovalAction,
    ApprovalActionResult,
    ApprovalStats,
    ApprovalStatus as ApprovalStatusModel,
)
from .project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectSummary,
    TaskWithProject,
    SkillWithSource,
)

__all__ = [
    # Task
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskSummary",
    "TaskStats",
    "TaskNotificationConfig",
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
    # Notification
    "Channel",
    "ChannelCreate",
    "ChannelUpdate",
    "NotificationConfig",
    "NotificationEvent",
    "ProviderInfo",
    "TestResult",
    # Approval
    "Approval",
    "ApprovalSummary",
    "ApprovalAction",
    "ApprovalActionResult",
    "ApprovalStats",
    "ApprovalStatusModel",
    # Project
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectSummary",
    "TaskWithProject",
    "SkillWithSource",
]
