"""Plan mode approval entities for interactive task approval."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Self


class ApprovalStatus(str, Enum):
    """Status of a pending plan approval."""

    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class MessageRef:
    """Reference to a message sent to a notification channel.

    Used to track messages so we can edit them later (e.g., update with buttons).
    """

    message_id: int | str
    chat_id: str
    provider: str  # "telegram", "discord", etc.

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            chat_id=data["chat_id"],
            provider=data["provider"],
        )


@dataclass
class FeedbackEntry:
    """A single feedback entry in the discuss history."""

    feedback: str
    timestamp: str
    plan_response: str = ""  # Claude's response to the feedback

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feedback": self.feedback,
            "timestamp": self.timestamp,
            "plan_response": self.plan_response,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            feedback=data["feedback"],
            timestamp=data["timestamp"],
            plan_response=data.get("plan_response", ""),
        )


@dataclass
class PendingApproval:
    """Represents a pending plan awaiting user approval.

    This tracks the state of a plan mode task execution, including:
    - The original task and plan output
    - Claude session ID for resumption
    - Message references for editing notifications
    - Discussion history for iterative refinement
    - Worktree path for isolated execution
    """

    id: str
    task_id: str
    task_name: str
    session_id: str  # Claude session ID for --resume
    plan_text: str  # The plan output from Claude
    working_dir: str  # Task working directory (original)
    status: ApprovalStatus = ApprovalStatus.PENDING
    iteration: int = 0  # Current discuss iteration
    max_iterations: int = 5
    timeout_seconds: int = 3600
    created_at: str = ""
    expires_at: str = ""
    channel_messages: list[MessageRef] = field(default_factory=list)
    feedback_history: list[FeedbackEntry] = field(default_factory=list)
    final_output: str = ""  # Output after execution
    error: str | None = None
    worktree_path: str | None = None  # Isolated worktree for this execution
    task_timeout: int = 300  # Original task execution timeout
    notification_channels: list[str] = field(default_factory=list)  # Channel IDs for notifications

    def __post_init__(self) -> None:
        """Set default timestamps if not provided."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.expires_at:
            from datetime import timedelta

            expires = datetime.now() + timedelta(seconds=self.timeout_seconds)
            self.expires_at = expires.isoformat()

    @classmethod
    def create(
        cls,
        task_id: str,
        task_name: str,
        session_id: str,
        plan_text: str,
        working_dir: str,
        timeout_seconds: int = 3600,
        max_iterations: int = 5,
        worktree_path: str | None = None,
        task_timeout: int = 300,
        notification_channels: list[str] | None = None,
    ) -> Self:
        """Factory method to create a new pending approval."""
        return cls(
            id=str(uuid.uuid4())[:8],
            task_id=task_id,
            task_name=task_name,
            session_id=session_id,
            plan_text=plan_text,
            working_dir=working_dir,
            timeout_seconds=timeout_seconds,
            max_iterations=max_iterations,
            worktree_path=worktree_path,
            task_timeout=task_timeout,
            notification_channels=notification_channels or [],
        )

    @property
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        if self.status != ApprovalStatus.PENDING:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires

    @property
    def can_discuss(self) -> bool:
        """Check if more discuss iterations are allowed."""
        return self.iteration < self.max_iterations

    def add_feedback(self, feedback: str, plan_response: str = "") -> None:
        """Add a feedback entry to history."""
        entry = FeedbackEntry(
            feedback=feedback,
            timestamp=datetime.now().isoformat(),
            plan_response=plan_response,
        )
        self.feedback_history.append(entry)
        self.iteration += 1

    def add_message_ref(self, message_ref: MessageRef) -> None:
        """Add a message reference for later editing."""
        self.channel_messages.append(message_ref)

    def mark_approved(self) -> None:
        """Mark as approved and ready for execution."""
        self.status = ApprovalStatus.APPROVED

    def mark_executing(self) -> None:
        """Mark as currently executing."""
        self.status = ApprovalStatus.EXECUTING

    def mark_completed(self, output: str) -> None:
        """Mark as completed with output."""
        self.status = ApprovalStatus.COMPLETED
        self.final_output = output

    def mark_cancelled(self) -> None:
        """Mark as cancelled by user."""
        self.status = ApprovalStatus.CANCELLED

    def mark_expired(self) -> None:
        """Mark as expired due to timeout."""
        self.status = ApprovalStatus.EXPIRED

    def mark_failed(self, error: str) -> None:
        """Mark as failed with error."""
        self.status = ApprovalStatus.FAILED
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "session_id": self.session_id,
            "plan_text": self.plan_text,
            "working_dir": self.working_dir,
            "status": self.status.value,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "channel_messages": [m.to_dict() for m in self.channel_messages],
            "feedback_history": [f.to_dict() for f in self.feedback_history],
            "final_output": self.final_output,
            "error": self.error,
            "worktree_path": self.worktree_path,
            "task_timeout": self.task_timeout,
            "notification_channels": self.notification_channels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            task_name=data["task_name"],
            session_id=data["session_id"],
            plan_text=data["plan_text"],
            working_dir=data["working_dir"],
            status=ApprovalStatus(data["status"]),
            iteration=data.get("iteration", 0),
            max_iterations=data.get("max_iterations", 5),
            timeout_seconds=data.get("timeout_seconds", 3600),
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            channel_messages=[MessageRef.from_dict(m) for m in data.get("channel_messages", [])],
            feedback_history=[FeedbackEntry.from_dict(f) for f in data.get("feedback_history", [])],
            final_output=data.get("final_output", ""),
            error=data.get("error"),
            worktree_path=data.get("worktree_path"),
            task_timeout=data.get("task_timeout", 300),
            notification_channels=data.get("notification_channels", []),
        )
