"""Notification providers package."""

from codegeass.notifications.providers.base import NotificationProvider
from codegeass.notifications.providers.discord import DiscordProvider
from codegeass.notifications.providers.telegram import TelegramProvider

# TeamsProvider requires httpx which is optional
try:
    from codegeass.notifications.providers.teams import TeamsProvider
except ImportError:
    TeamsProvider = None  # type: ignore[misc, assignment]

__all__ = ["NotificationProvider", "TelegramProvider", "DiscordProvider", "TeamsProvider"]
