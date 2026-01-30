"""Pydantic models for plan approval API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status of a pending plan approval."""

    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class MessageRef(BaseModel):
    """Reference to a message in a notification channel."""

    message_id: int | str
    chat_id: str
    provider: str


class FeedbackEntry(BaseModel):
    """A single feedback entry in the discuss history."""

    feedback: str
    timestamp: str
    plan_response: str = ""


class Approval(BaseModel):
    """Full approval model for API responses."""

    id: str
    task_id: str
    task_name: str
    session_id: str
    plan_text: str
    working_dir: str
    status: ApprovalStatus
    iteration: int = 0
    max_iterations: int = 5
    timeout_seconds: int = 3600
    created_at: str
    expires_at: str
    channel_messages: list[MessageRef] = Field(default_factory=list)
    feedback_history: list[FeedbackEntry] = Field(default_factory=list)
    final_output: str = ""
    error: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        if self.status != ApprovalStatus.PENDING:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires


class ApprovalSummary(BaseModel):
    """Summary approval model for list views."""

    id: str
    task_id: str
    task_name: str
    status: ApprovalStatus
    iteration: int
    max_iterations: int
    created_at: str
    expires_at: str
    is_expired: bool


class ApprovalAction(BaseModel):
    """Request model for approval actions (discuss)."""

    feedback: str = Field(..., min_length=1, description="User feedback for discuss action")


class ApprovalActionResult(BaseModel):
    """Response model for approval actions."""

    success: bool
    message: str
    approval: Approval | None = None


class ApprovalStats(BaseModel):
    """Statistics about approvals."""

    total: int
    pending: int
    approved: int
    cancelled: int
    expired: int
    failed: int
    completed: int
