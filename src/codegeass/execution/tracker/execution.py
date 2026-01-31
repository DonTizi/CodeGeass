"""Active execution data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class ActiveExecution:
    """Represents an active execution being tracked.

    Contains state and metadata for a running task execution.
    """

    execution_id: str
    task_id: str
    task_name: str
    session_id: str | None
    started_at: datetime
    status: Literal["starting", "running", "finishing", "waiting_approval", "stopped"] = "starting"
    output_lines: list[str] = field(default_factory=list)
    current_phase: str = "initializing"
    approval_id: str | None = None
    pid: int | None = None

    _max_output_lines: int = 1000

    def append_output(self, line: str) -> None:
        """Append output line to buffer, keeping only the last N lines."""
        self.output_lines.append(line)
        if len(self.output_lines) > self._max_output_lines:
            self.output_lines = self.output_lines[-self._max_output_lines:]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
            "output_lines": self.output_lines[-20:],
            "current_phase": self.current_phase,
            "approval_id": self.approval_id,
            "pid": self.pid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActiveExecution":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            task_id=data["task_id"],
            task_name=data["task_name"],
            session_id=data.get("session_id"),
            started_at=datetime.fromisoformat(data["started_at"]),
            status=data.get("status", "running"),
            output_lines=data.get("output_lines", []),
            current_phase=data.get("current_phase", "unknown"),
            approval_id=data.get("approval_id"),
            pid=data.get("pid"),
        )
