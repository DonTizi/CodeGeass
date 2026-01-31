"""Data models for callback handling."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PendingFeedback:
    """Tracks a pending feedback request (user clicked Discuss)."""

    approval_id: str
    chat_id: str
    user_id: str
    message_id: int | str
    requested_at: datetime
    expires_at: datetime
