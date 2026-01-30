"""Notification system for CodeGeass.

This module provides a pluggable notification system that can send
notifications to various chat platforms (Telegram, Discord, Teams, Slack)
when task execution events occur.

Note: Service and Handler are not imported at package level to avoid
circular imports with storage modules. Import them directly:
    from codegeass.notifications.service import NotificationService
    from codegeass.notifications.handler import NotificationHandler
"""

from codegeass.notifications.exceptions import (
    ChannelConfigError,
    ChannelNotFoundError,
    CredentialError,
    NotificationError,
    ProviderError,
    ProviderNotFoundError,
)
from codegeass.notifications.formatter import MessageFormatter, get_message_formatter
from codegeass.notifications.models import (
    Channel,
    NotificationConfig,
    NotificationDefaults,
    NotificationEvent,
)
from codegeass.notifications.registry import ProviderRegistry, get_provider_registry

__all__ = [
    # Models
    "Channel",
    "NotificationConfig",
    "NotificationDefaults",
    "NotificationEvent",
    # Exceptions
    "NotificationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ChannelNotFoundError",
    "ChannelConfigError",
    "CredentialError",
    # Registry
    "ProviderRegistry",
    "get_provider_registry",
    # Formatter
    "MessageFormatter",
    "get_message_formatter",
]
