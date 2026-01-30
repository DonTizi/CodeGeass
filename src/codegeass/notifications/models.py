"""Notification domain models."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Self


class NotificationEvent(str, Enum):
    """Types of events that can trigger notifications."""

    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    DAILY_SUMMARY = "daily_summary"

    @classmethod
    def from_string(cls, value: str) -> "NotificationEvent":
        """Create from string value."""
        # Handle both "task_start" and "start" formats
        normalized = value.lower().strip()
        if not normalized.startswith("task_") and normalized != "daily_summary":
            normalized = f"task_{normalized}"
        return cls(normalized)


@dataclass
class Channel:
    """A notification channel (e.g., a Telegram chat or Discord webhook).

    Channels represent destinations for notifications. The actual credentials
    (like bot tokens) are stored separately in ~/.codegeass/credentials.yaml
    and referenced via credential_key.
    """

    id: str
    name: str
    provider: str  # "telegram", "discord", "teams", "slack"
    credential_key: str  # Reference to credentials in ~/.codegeass/credentials.yaml
    config: dict[str, Any] = field(default_factory=dict)  # Non-secret config (e.g., chat_id)
    enabled: bool = True
    created_at: str | None = None

    @classmethod
    def create(
        cls,
        name: str,
        provider: str,
        credential_key: str,
        config: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> Self:
        """Factory method to create a new channel with generated ID."""
        channel_id = str(uuid.uuid4())[:8]
        return cls(
            id=channel_id,
            name=name,
            provider=provider,
            credential_key=credential_key,
            config=config or {},
            enabled=enabled,
            created_at=datetime.now().isoformat(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create channel from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            credential_key=data["credential_key"],
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "credential_key": self.credential_key,
            "config": self.config,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


@dataclass
class NotificationConfig:
    """Configuration for notifications on a task.

    This is embedded in Task.notifications field.
    """

    channels: list[str] = field(default_factory=list)  # Channel IDs
    events: list[NotificationEvent] = field(default_factory=list)  # Events to notify on
    include_output: bool = False  # Include task output in message
    mention_on_failure: bool = False  # Mention/ping on failure

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Self | None:
        """Create from dictionary. Returns None if data is None."""
        if data is None:
            return None

        events = []
        for event in data.get("events", []):
            if isinstance(event, str):
                events.append(NotificationEvent.from_string(event))
            else:
                events.append(event)

        return cls(
            channels=data.get("channels", []),
            events=events,
            include_output=data.get("include_output", False),
            mention_on_failure=data.get("mention_on_failure", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "channels": self.channels,
            "events": [e.value for e in self.events],
            "include_output": self.include_output,
            "mention_on_failure": self.mention_on_failure,
        }

    def should_notify(self, event: NotificationEvent) -> bool:
        """Check if this config should trigger notification for event."""
        if not self.channels:
            return False
        return event in self.events


@dataclass
class NotificationDefaults:
    """Default notification settings for the project."""

    enabled: bool = False  # OPT-IN: notifications disabled by default
    events: list[NotificationEvent] = field(
        default_factory=lambda: [NotificationEvent.TASK_FAILURE]
    )
    include_output: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Self:
        """Create from dictionary."""
        if data is None:
            return cls()

        events = []
        for event in data.get("events", ["task_failure"]):
            if isinstance(event, str):
                events.append(NotificationEvent.from_string(event))
            else:
                events.append(event)

        return cls(
            enabled=data.get("enabled", False),
            events=events,
            include_output=data.get("include_output", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "events": [e.value for e in self.events],
            "include_output": self.include_output,
        }
