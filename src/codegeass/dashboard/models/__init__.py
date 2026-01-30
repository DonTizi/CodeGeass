"""Pydantic models for CodeGeass Dashboard API."""

from .approval import (
    Approval,
    ApprovalAction,
    ApprovalActionResult,
    ApprovalStats,
    ApprovalSummary,
)
from .approval import (
    ApprovalStatus as ApprovalStatusModel,
)
from .execution import (
    ExecutionResult,
    ExecutionStatus,
    LogFilter,
    LogStats,
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
from .project import (
    Project,
    ProjectCreate,
    ProjectSummary,
    ProjectUpdate,
    SkillWithSource,
    TaskWithProject,
)
from .scheduler import (
    SchedulerStatus,
    UpcomingRun,
)
from .skill import (
    Skill,
    SkillSummary,
)
from .task import (
    Task,
    TaskCreate,
    TaskNotificationConfig,
    TaskStats,
    TaskSummary,
    TaskUpdate,
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
