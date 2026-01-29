"""Domain exceptions for CodeGeass."""


class CodeGeassError(Exception):
    """Base exception for all CodeGeass errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(CodeGeassError):
    """Raised when configuration is invalid or missing."""


class ValidationError(CodeGeassError):
    """Raised when validation fails."""


class TaskNotFoundError(CodeGeassError):
    """Raised when a task is not found."""

    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}", {"task_id": task_id})
        self.task_id = task_id


class TemplateNotFoundError(CodeGeassError):
    """Raised when a template is not found."""

    def __init__(self, template_name: str):
        super().__init__(f"Template not found: {template_name}", {"template_name": template_name})
        self.template_name = template_name


class SkillNotFoundError(CodeGeassError):
    """Raised when a skill is not found."""

    def __init__(self, skill_name: str):
        super().__init__(f"Skill not found: {skill_name}", {"skill_name": skill_name})
        self.skill_name = skill_name


class ExecutionError(CodeGeassError):
    """Raised when task execution fails."""

    def __init__(self, message: str, task_id: str | None = None, cause: Exception | None = None):
        super().__init__(message, {"task_id": task_id})
        self.task_id = task_id
        self.cause = cause


class SchedulingError(CodeGeassError):
    """Raised when scheduling operations fail."""
