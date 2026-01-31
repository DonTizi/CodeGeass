"""Callback handler for interactive notification buttons.

This module re-exports from the callbacks/ package for backward compatibility.
The functionality is now split into:
- callbacks/handler.py: Main CallbackHandler class
- callbacks/telegram_server.py: TelegramCallbackServer for polling
- callbacks/models.py: Data models (PendingFeedback)
- callbacks/globals.py: Global instance management
"""

from codegeass.notifications.callbacks import (
    CallbackHandler,
    PendingFeedback,
    TelegramCallbackServer,
    get_callback_handler,
    get_callback_server,
    reset_callback_server,
)

__all__ = [
    "CallbackHandler",
    "PendingFeedback",
    "TelegramCallbackServer",
    "get_callback_handler",
    "get_callback_server",
    "reset_callback_server",
]
