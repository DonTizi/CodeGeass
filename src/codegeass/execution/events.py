"""Execution event types for real-time monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ExecutionEventType(str, Enum):
    """Type of execution event."""

    STARTED = "execution.started"
    OUTPUT = "execution.output"
    PROGRESS = "execution.progress"
    COMPLETED = "execution.completed"
    FAILED = "execution.failed"


@dataclass
class ExecutionEvent:
    """Event emitted during task execution.

    Used to track real-time progress of Claude Code executions.
    """

    type: ExecutionEventType
    execution_id: str
    task_id: str
    task_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type.value,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionEvent":
        """Create event from dictionary."""
        return cls(
            type=ExecutionEventType(data["type"]),
            execution_id=data["execution_id"],
            task_id=data["task_id"],
            task_name=data["task_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
        )

    @classmethod
    def started(
        cls,
        execution_id: str,
        task_id: str,
        task_name: str,
        session_id: str | None = None,
    ) -> "ExecutionEvent":
        """Create a STARTED event."""
        return cls(
            type=ExecutionEventType.STARTED,
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            data={"session_id": session_id},
        )

    @classmethod
    def output(
        cls,
        execution_id: str,
        task_id: str,
        task_name: str,
        line: str,
    ) -> "ExecutionEvent":
        """Create an OUTPUT event."""
        return cls(
            type=ExecutionEventType.OUTPUT,
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            data={"line": line},
        )

    @classmethod
    def progress(
        cls,
        execution_id: str,
        task_id: str,
        task_name: str,
        phase: str,
        message: str | None = None,
    ) -> "ExecutionEvent":
        """Create a PROGRESS event."""
        return cls(
            type=ExecutionEventType.PROGRESS,
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            data={"phase": phase, "message": message},
        )

    @classmethod
    def completed(
        cls,
        execution_id: str,
        task_id: str,
        task_name: str,
        exit_code: int,
        duration_seconds: float,
    ) -> "ExecutionEvent":
        """Create a COMPLETED event."""
        return cls(
            type=ExecutionEventType.COMPLETED,
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            data={"exit_code": exit_code, "duration_seconds": duration_seconds},
        )

    @classmethod
    def failed(
        cls,
        execution_id: str,
        task_id: str,
        task_name: str,
        error: str,
        exit_code: int | None = None,
    ) -> "ExecutionEvent":
        """Create a FAILED event."""
        return cls(
            type=ExecutionEventType.FAILED,
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            data={"error": error, "exit_code": exit_code},
        )
