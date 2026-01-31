"""Global instances for callback handling."""

from typing import TYPE_CHECKING

from codegeass.notifications.callbacks.handler import CallbackHandler
from codegeass.notifications.callbacks.telegram_server import TelegramCallbackServer

if TYPE_CHECKING:
    from codegeass.execution.plan_service import PlanApprovalService
    from codegeass.storage.channel_repository import ChannelRepository

_callback_server: TelegramCallbackServer | None = None
_callback_handler: CallbackHandler | None = None


def get_callback_handler(
    plan_service: "PlanApprovalService | None" = None,
    channel_repo: "ChannelRepository | None" = None,
) -> CallbackHandler:
    """Get the callback handler instance."""
    global _callback_handler

    if _callback_handler is None:
        if plan_service is None or channel_repo is None:
            raise ValueError("plan_service and channel_repo required on first call")
        _callback_handler = CallbackHandler(plan_service, channel_repo)

    return _callback_handler


def get_callback_server(
    callback_handler: CallbackHandler | None = None,
    channel_repo: "ChannelRepository | None" = None,
) -> TelegramCallbackServer:
    """Get the callback server instance."""
    global _callback_server

    if _callback_server is None:
        if callback_handler is None or channel_repo is None:
            raise ValueError("callback_handler and channel_repo required on first call")
        _callback_server = TelegramCallbackServer(callback_handler, channel_repo)

    return _callback_server


def reset_callback_server() -> None:
    """Reset global instances (for testing)."""
    global _callback_server, _callback_handler
    if _callback_server:
        _callback_server.stop()
    _callback_server = None
    _callback_handler = None
