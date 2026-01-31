"""Callback handling for interactive notifications.

Modules:
- handler: Main CallbackHandler for processing button clicks
- telegram_server: TelegramCallbackServer for polling Telegram updates
- models: Data models (PendingFeedback)
- globals: Global instance management
"""

from codegeass.notifications.callbacks.globals import (
    get_callback_handler,
    get_callback_server,
    reset_callback_server,
)
from codegeass.notifications.callbacks.handler import CallbackHandler
from codegeass.notifications.callbacks.models import PendingFeedback
from codegeass.notifications.callbacks.telegram_server import TelegramCallbackServer

__all__ = [
    "CallbackHandler",
    "PendingFeedback",
    "TelegramCallbackServer",
    "get_callback_handler",
    "get_callback_server",
    "reset_callback_server",
]
