"""Task entity for scheduled tasks."""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

from codegeass.core.exceptions import ValidationError
from codegeass.core.value_objects import CronExpression


@dataclass
class Task:
    """Scheduled task entity."""

    id: str
    name: str
    schedule: str  # CRON expression
    working_dir: Path

    # Execution configuration
    skill: str | None = None  # Reference to skill name
    prompt: str | None = None  # Direct prompt (if no skill)
    allowed_tools: list[str] = field(default_factory=list)
    model: str = "sonnet"
    autonomous: bool = False
    max_turns: int | None = None
    timeout: int = 300

    # Code execution provider (claude, codex, etc.)
    code_source: str = "claude"

    # Task state
    enabled: bool = True
    variables: dict[str, Any] = field(default_factory=dict)
    last_run: str | None = None  # ISO timestamp
    last_status: str | None = None

    # Notification configuration
    notifications: dict[str, Any] | None = None  # NotificationConfig as dict

    # Plan mode configuration
    plan_mode: bool = False  # Enable interactive plan approval
    plan_timeout: int = 3600  # Approval timeout in seconds (default 1 hour)
    plan_max_iterations: int = 5  # Max discuss rounds before auto-cancel

    def __post_init__(self) -> None:
        """Validate task configuration."""
        CronExpression(self.schedule)  # Validate CRON expression
        if not self.working_dir.is_absolute():
            raise ValidationError(f"working_dir must be absolute: {self.working_dir}")
        if not self.skill and not self.prompt:
            raise ValidationError("Task must have either 'skill' or 'prompt'")

    @classmethod
    def create(
        cls,
        name: str,
        schedule: str,
        working_dir: Path,
        skill: str | None = None,
        prompt: str | None = None,
        **kwargs: Any,
    ) -> Self:
        """Factory method to create a new task with generated ID."""
        task_id = str(uuid.uuid4())[:8]
        return cls(
            id=task_id,
            name=name,
            schedule=schedule,
            working_dir=working_dir,
            skill=skill,
            prompt=prompt,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            schedule=data["schedule"],
            working_dir=Path(data["working_dir"]),
            skill=data.get("skill"),
            prompt=data.get("prompt"),
            allowed_tools=data.get("allowed_tools", []),
            model=data.get("model", "sonnet"),
            autonomous=data.get("autonomous", False),
            max_turns=data.get("max_turns"),
            timeout=data.get("timeout", 300),
            code_source=data.get("code_source", "claude"),
            enabled=data.get("enabled", True),
            variables=data.get("variables", {}),
            last_run=data.get("last_run"),
            last_status=data.get("last_status"),
            notifications=data.get("notifications"),
            plan_mode=data.get("plan_mode", False),
            plan_timeout=data.get("plan_timeout", 3600),
            plan_max_iterations=data.get("plan_max_iterations", 5),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "working_dir": str(self.working_dir),
            "skill": self.skill,
            "prompt": self.prompt,
            "allowed_tools": self.allowed_tools,
            "model": self.model,
            "autonomous": self.autonomous,
            "max_turns": self.max_turns,
            "timeout": self.timeout,
            "code_source": self.code_source,
            "enabled": self.enabled,
            "variables": self.variables,
            "last_run": self.last_run,
            "last_status": self.last_status,
        }
        if self.notifications:
            result["notifications"] = self.notifications
        if self.plan_mode:
            result["plan_mode"] = self.plan_mode
            result["plan_timeout"] = self.plan_timeout
            result["plan_max_iterations"] = self.plan_max_iterations
        return result

    @property
    def cron(self) -> CronExpression:
        """Get CRON expression value object."""
        return CronExpression(self.schedule)

    def is_due(self, window_seconds: int = 60) -> bool:
        """Check if task is due for execution."""
        return self.enabled and self.cron.is_due(window_seconds)

    def update_last_run(self, status: str) -> None:
        """Update last run timestamp and status."""
        from datetime import datetime

        self.last_run = datetime.now().isoformat()
        self.last_status = status
