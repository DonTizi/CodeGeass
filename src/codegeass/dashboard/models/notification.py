"""Pydantic models for notification API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotificationEvent(str, Enum):
    """Types of events that can trigger notifications."""

    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    DAILY_SUMMARY = "daily_summary"


class Channel(BaseModel):
    """Notification channel model."""

    id: str
    name: str
    provider: str
    credential_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: str | None = None

    class Config:
        from_attributes = True


class ChannelCreate(BaseModel):
    """Model for creating a new channel."""

    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., pattern="^(telegram|discord|teams|slack)$")
    credentials: dict[str, str] = Field(..., min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelUpdate(BaseModel):
    """Model for updating a channel."""

    name: str | None = Field(None, min_length=1, max_length=100)
    config: dict[str, Any] | None = None
    enabled: bool | None = None


class CredentialField(BaseModel):
    """Credential field information."""

    name: str
    description: str
    sensitive: bool = True


class ConfigField(BaseModel):
    """Config field information."""

    name: str
    description: str
    default: Any = None
    sensitive: bool = False


class ProviderInfo(BaseModel):
    """Information about a notification provider."""

    name: str
    display_name: str
    description: str
    required_credentials: list[CredentialField]
    required_config: list[ConfigField]
    optional_config: list[ConfigField] = Field(default_factory=list)


class NotificationConfig(BaseModel):
    """Notification configuration for a task."""

    channels: list[str] = Field(default_factory=list)
    events: list[NotificationEvent] = Field(default_factory=list)
    include_output: bool = False
    mention_on_failure: bool = False


class TestResult(BaseModel):
    """Result of a channel test."""

    success: bool
    message: str
