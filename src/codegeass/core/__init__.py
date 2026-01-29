"""Core domain layer - entities, value objects, and exceptions."""

from codegeass.core.entities import Prompt, Skill, Task, Template
from codegeass.core.exceptions import (
    CodeGeassError,
    ConfigurationError,
    ExecutionError,
    SchedulingError,
    SkillNotFoundError,
    TaskNotFoundError,
    TemplateNotFoundError,
    ValidationError,
)
from codegeass.core.value_objects import CronExpression, ExecutionResult, ExecutionStatus

__all__ = [
    # Entities
    "Task",
    "Template",
    "Skill",
    "Prompt",
    # Value Objects
    "CronExpression",
    "ExecutionResult",
    "ExecutionStatus",
    # Exceptions
    "CodeGeassError",
    "ConfigurationError",
    "ExecutionError",
    "SchedulingError",
    "SkillNotFoundError",
    "TaskNotFoundError",
    "TemplateNotFoundError",
    "ValidationError",
]
