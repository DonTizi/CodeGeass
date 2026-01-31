"""Value objects for CodeGeass domain."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Self

from croniter import croniter

from codegeass.core.exceptions import ValidationError


class ExecutionStatus(Enum):
    """Status of a task execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result of a task execution."""

    task_id: str
    session_id: str | None
    status: ExecutionStatus
    output: str
    started_at: datetime
    finished_at: datetime
    error: str | None = None
    exit_code: int | None = None
    metadata: dict | None = None  # Optional metadata (e.g., worktree_path for plan mode)

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS

    @property
    def clean_output(self) -> str:
        """Get human-readable output (parsed based on provider format)."""
        # Check provider from metadata to use correct parser
        provider = self.metadata.get("provider") if self.metadata else None

        if provider == "codex":
            # Use Codex JSONL parser
            from codegeass.providers.codex.output_parser import extract_clean_text

            return extract_clean_text(self.output)
        else:
            # Default to Claude stream-json parser
            from codegeass.execution.output_parser import extract_clean_text

            return extract_clean_text(self.output)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "output": self.output,
            "clean_output": self.clean_output,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "error": self.error,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            session_id=data.get("session_id"),
            status=ExecutionStatus(data["status"]),
            output=data["output"],
            started_at=datetime.fromisoformat(data["started_at"]),
            finished_at=datetime.fromisoformat(data["finished_at"]),
            error=data.get("error"),
            exit_code=data.get("exit_code"),
            metadata=data.get("metadata"),
        )


@dataclass(frozen=True)
class CronExpression:
    """Validated CRON expression value object."""

    expression: str

    def __post_init__(self) -> None:
        """Validate the CRON expression."""
        if not self._is_valid(self.expression):
            raise ValidationError(f"Invalid CRON expression: {self.expression}")

    @staticmethod
    def _is_valid(expression: str) -> bool:
        """Check if CRON expression is valid."""
        try:
            croniter(expression)
            return True
        except (ValueError, KeyError):
            return False

    def get_next(self, base_time: datetime | None = None) -> datetime:
        """Get next scheduled time from base_time (default: now)."""
        base = base_time or datetime.now()
        cron = croniter(self.expression, base)
        return cron.get_next(datetime)

    def get_prev(self, base_time: datetime | None = None) -> datetime:
        """Get previous scheduled time from base_time (default: now)."""
        base = base_time or datetime.now()
        cron = croniter(self.expression, base)
        return cron.get_prev(datetime)

    def is_due(self, window_seconds: int = 60) -> bool:
        """Check if task is due within the time window."""
        now = datetime.now()
        prev = self.get_prev(now)
        return (now - prev).total_seconds() <= window_seconds

    def describe(self) -> str:
        """Return human-readable description of schedule."""
        parts = self.expression.split()
        if len(parts) != 5:
            return self.expression

        minute, hour, dom, month, dow = parts

        # Common patterns
        if self.expression == "* * * * *":
            return "Every minute"
        if minute != "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
            return f"Every hour at minute {minute}"
        if minute != "*" and hour != "*" and dom == "*" and month == "*" and dow == "*":
            return f"Daily at {hour}:{minute.zfill(2)}"
        if minute != "*" and hour != "*" and dow != "*" and dom == "*" and month == "*":
            days = {
                "0": "Sun",
                "1": "Mon",
                "2": "Tue",
                "3": "Wed",
                "4": "Thu",
                "5": "Fri",
                "6": "Sat",
                "1-5": "Mon-Fri",
                "0,6": "Sat-Sun",
            }
            day_str = days.get(dow, dow)
            return f"{day_str} at {hour}:{minute.zfill(2)}"

        return self.expression
