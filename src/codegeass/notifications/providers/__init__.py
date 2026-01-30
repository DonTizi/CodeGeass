"""Notification providers package."""

from codegeass.notifications.providers.base import NotificationProvider
from codegeass.notifications.providers.discord import DiscordProvider
from codegeass.notifications.providers.teams import TeamsProvider
from codegeass.notifications.providers.telegram import TelegramProvider

__all__ = ["NotificationProvider", "TelegramProvider", "DiscordProvider", "TeamsProvider"]
