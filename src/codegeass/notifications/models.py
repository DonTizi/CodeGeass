"""Notification domain models.

This module defines the core data structures for the notification system:

- NotificationEvent: Event types that trigger notifications
- Channel: A configured notification destination (Telegram, Discord, etc.)
- NotificationConfig: Per-task notification settings
- NotificationDefaults: Project-wide default notification settings

Credentials are stored separately in ~/.codegeass/credentials.yaml.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Self


class NotificationEvent(str, Enum):
    """Types of events that can trigger notifications.

    Events can be subscribed to on a per-task basis via NotificationConfig.

    Values:
        TASK_START: Fired when a task begins execution.
        TASK_COMPLETE: Fired when a task finishes (success or failure).
        TASK_SUCCESS: Fired only on successful completion.
        TASK_FAILURE: Fired only on execution failure.
        DAILY_SUMMARY: Fired once daily with execution statistics.
    """

    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    DAILY_SUMMARY = "daily_summary"

    @classmethod
    def from_string(cls, value: str) -> "NotificationEvent":
        """Create from string value.

        Handles both full format ("task_start") and short format ("start").

        Args:
            value: Event name, with or without "task_" prefix.

        Returns:
            Corresponding NotificationEvent enum value.
        """
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
    """Configuration for notifications on a specific task.

    This dataclass is embedded in Task.notifications field and controls
    which events trigger notifications and to which channels.

    Attributes:
        channels: List of channel IDs to notify (references Channel.id).
        events: List of events that trigger notifications.
        include_output: If True, includes task output in notification message.
        mention_on_failure: If True, uses @mentions/pings on failure events.

    Example:
        >>> config = NotificationConfig(
        ...     channels=["abc123"],
        ...     events=[NotificationEvent.TASK_FAILURE],
        ...     mention_on_failure=True
        ... )
    """

    channels: list[str] = field(default_factory=list)
    events: list[NotificationEvent] = field(default_factory=list)
    include_output: bool = False
    mention_on_failure: bool = False

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
    """Default notification settings for the project.

    These defaults apply to all tasks that don't have explicit
    NotificationConfig. Stored in config/settings.yaml.

    Attributes:
        enabled: Master switch for notifications (OPT-IN, default False).
        events: Default events to notify on (default: [TASK_FAILURE]).
        include_output: Default for including output in messages.

    Example:
        >>> defaults = NotificationDefaults(
        ...     enabled=True,
        ...     events=[NotificationEvent.TASK_FAILURE, NotificationEvent.DAILY_SUMMARY]
        ... )
    """

    enabled: bool = False
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
