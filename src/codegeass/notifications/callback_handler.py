"""Callback handler for interactive notification buttons.

This module provides the infrastructure for handling button clicks
from Telegram, Discord, etc., and routing them to the appropriate
action handlers (approve, discuss, cancel).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from codegeass.notifications.interactive import CallbackQuery

if TYPE_CHECKING:
    from codegeass.execution.plan_service import PlanApprovalService
    from codegeass.storage.approval_repository import PendingApprovalRepository
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


@dataclass
class PendingFeedback:
    """Tracks a pending feedback request (user clicked Discuss)."""

    approval_id: str
    chat_id: str
    user_id: str
    message_id: int | str
    requested_at: datetime
    expires_at: datetime


class CallbackHandler:
    """Handler for processing button callbacks from notification providers.

    This class routes callback actions to the appropriate handlers:
    - plan:approve:<id> -> handle approval
    - plan:discuss:<id> -> request feedback
    - plan:cancel:<id> -> handle cancellation
    """

    def __init__(
        self,
        plan_service: "PlanApprovalService",
        channel_repo: "ChannelRepository",
    ):
        self._plan_service = plan_service
        self._channels = channel_repo
        # Track pending feedback requests: {chat_id:user_id -> PendingFeedback}
        self._pending_feedback: dict[str, PendingFeedback] = {}
        # Feedback timeout in seconds
        self._feedback_timeout = 300  # 5 minutes

    async def handle_callback(
        self,
        callback: CallbackQuery,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Handle a callback query from a button click.

        Args:
            callback: The callback query data
            credentials: Provider credentials for answering

        Returns:
            Tuple of (success, message_to_show_user)
        """
        prefix, action, approval_id = callback.parse_action()

        if prefix != "plan":
            logger.debug(f"Unknown callback prefix: {prefix}")
            return False, "Unknown action"

        if action == "approve":
            return await self._handle_approve(callback, approval_id, credentials)
        elif action == "discuss":
            return await self._handle_discuss_request(callback, approval_id, credentials)
        elif action == "cancel":
            return await self._handle_cancel(callback, approval_id, credentials)
        else:
            logger.warning(f"Unknown plan action: {action}")
            return False, f"Unknown action: {action}"

    async def _handle_approve(
        self,
        callback: CallbackQuery,
        approval_id: str,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Handle approve button click."""
        try:
            # Answer callback first to dismiss loading state
            await self._answer_callback(callback, credentials, "Approving plan...")

            # Execute the approval
            result = await self._plan_service.handle_approval(approval_id)

            if result and result.is_success:
                return True, "Plan approved and executed successfully!"
            elif result:
                return False, f"Execution failed: {result.error}"
            else:
                return False, "Approval not found or already processed"

        except Exception as e:
            logger.error(f"Error handling approval: {e}")
            return False, f"Error: {e}"

    async def _handle_discuss_request(
        self,
        callback: CallbackQuery,
        approval_id: str,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Handle discuss button click - request feedback from user."""
        try:
            # Check if approval exists and is pending
            approval = self._plan_service.find_by_id(approval_id)
            if not approval:
                return False, "Approval not found"

            from codegeass.execution.plan_approval import ApprovalStatus
            if approval.status != ApprovalStatus.PENDING:
                return False, "Approval already processed"

            if not approval.can_discuss:
                return False, "Maximum iterations reached"

            # Answer callback
            await self._answer_callback(
                callback,
                credentials,
                "Please reply to this message with your feedback.",
                show_alert=True,
            )

            # Track pending feedback
            from datetime import timedelta
            feedback_key = f"{callback.chat_id}:{callback.from_user_id}"
            self._pending_feedback[feedback_key] = PendingFeedback(
                approval_id=approval_id,
                chat_id=callback.chat_id,
                user_id=callback.from_user_id,
                message_id=callback.message_id,
                requested_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=self._feedback_timeout),
            )

            return True, "Reply to provide feedback"

        except Exception as e:
            logger.error(f"Error handling discuss request: {e}")
            return False, f"Error: {e}"

    async def _handle_cancel(
        self,
        callback: CallbackQuery,
        approval_id: str,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Handle cancel button click."""
        try:
            await self._answer_callback(callback, credentials, "Cancelling...")

            success = await self._plan_service.handle_cancel(approval_id)

            if success:
                return True, "Plan cancelled"
            else:
                return False, "Approval not found or already processed"

        except Exception as e:
            logger.error(f"Error handling cancel: {e}")
            return False, f"Error: {e}"

    async def handle_reply_message(
        self,
        chat_id: str,
        user_id: str,
        reply_to_message_id: int | str,
        text: str,
    ) -> tuple[bool, str]:
        """Handle a reply message that might be feedback.

        This is called when a user replies to a message. We check if
        there's a pending feedback request matching this user and chat.

        Args:
            chat_id: Chat where the reply was sent
            user_id: User who sent the reply
            reply_to_message_id: ID of the message being replied to
            text: The reply text (feedback)

        Returns:
            Tuple of (handled, message)
        """
        # Clean up expired feedback requests
        self._cleanup_expired_feedback()

        feedback_key = f"{chat_id}:{user_id}"
        pending = self._pending_feedback.get(feedback_key)

        if not pending:
            return False, ""

        # Check if reply is to the correct message
        if str(pending.message_id) != str(reply_to_message_id):
            return False, ""

        # Remove from pending
        del self._pending_feedback[feedback_key]

        # Process the feedback
        try:
            updated = await self._plan_service.handle_discuss(
                pending.approval_id,
                text,
            )

            if updated:
                return True, "Feedback processed, new plan sent."
            else:
                return False, "Failed to process feedback"

        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return False, f"Error: {e}"

    def _cleanup_expired_feedback(self) -> None:
        """Remove expired feedback requests."""
        now = datetime.now()
        expired = [
            key for key, pending in self._pending_feedback.items()
            if pending.expires_at < now
        ]
        for key in expired:
            del self._pending_feedback[key]

    async def _answer_callback(
        self,
        callback: CallbackQuery,
        credentials: dict[str, str],
        text: str | None = None,
        show_alert: bool = False,
    ) -> None:
        """Answer a callback query using the provider."""
        from codegeass.notifications.registry import get_provider_registry

        try:
            registry = get_provider_registry()
            provider = registry.get(callback.provider)

            if hasattr(provider, "answer_callback"):
                await provider.answer_callback(
                    credentials=credentials,
                    callback_query=callback,
                    text=text,
                    show_alert=show_alert,
                )
        except Exception as e:
            logger.warning(f"Failed to answer callback: {e}")


class TelegramCallbackServer:
    """Polling server for handling Telegram callbacks and replies.

    This server polls the Telegram Bot API for updates and routes
    callback queries and reply messages to the CallbackHandler.
    """

    def __init__(
        self,
        callback_handler: CallbackHandler,
        channel_repo: "ChannelRepository",
        poll_interval: float = 0.5,  # Short interval since we use long polling
    ):
        self._handler = callback_handler
        self._channels = channel_repo
        self._poll_interval = poll_interval
        self._running = False
        self._last_update_id: dict[str, int] = {}  # bot_token -> last_update_id

    async def start(self) -> None:
        """Start the polling loop."""
        self._running = True
        logger.info("Telegram callback server starting...")
        print("[Callback Server] Starting polling loop...")

        poll_count = 0
        while self._running:
            try:
                await self._poll_all_bots()
                poll_count += 1
                # Log every 10 polls for debugging
                if poll_count % 10 == 0:
                    print(f"[Callback Server] Polling active ({poll_count} polls)", flush=True)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                print(f"[Callback Server] Error in polling: {e}", flush=True)

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        logger.info("Telegram callback server stopping...")

    async def _poll_all_bots(self) -> None:
        """Poll all configured Telegram bots for updates."""
        # Get all Telegram channels
        all_channels = self._channels.find_all()
        telegram_channels = [ch for ch in all_channels if ch.provider == "telegram"]

        if not telegram_channels:
            return

        # Group by bot token (credential_key)
        seen_tokens: set[str] = set()

        for channel in telegram_channels:
            if not channel.enabled:
                continue

            try:
                _, credentials = self._channels.get_channel_with_credentials(channel.id)
                bot_token = credentials.get("bot_token")

                if not bot_token or bot_token in seen_tokens:
                    continue

                seen_tokens.add(bot_token)
                await self._poll_bot(bot_token, credentials)

            except Exception as e:
                print(f"[Callback Server] Error getting credentials for {channel.id}: {e}")

    async def _poll_bot(self, bot_token: str, credentials: dict[str, str]) -> None:
        """Poll a specific bot for updates."""
        try:
            from telegram import Bot, Update
        except ImportError:
            print("[Callback Server] telegram package not installed")
            return

        bot = Bot(token=bot_token)
        offset = self._last_update_id.get(bot_token, 0) + 1 if bot_token in self._last_update_id else None

        try:
            updates = await bot.get_updates(
                offset=offset,
                timeout=2,  # Short polling with 2 second timeout
                allowed_updates=["callback_query", "message"],
            )

            if updates:
                print(f"[Callback Server] Received {len(updates)} update(s)", flush=True)

            for update in updates:
                self._last_update_id[bot_token] = update.update_id
                await self._process_update(update, credentials)

        except Exception as e:
            # Don't log timeout errors (expected with long polling)
            if "Timed out" not in str(e):
                logger.error(f"Error polling bot: {e}")
                print(f"[Callback Server] Error polling: {e}", flush=True)

    async def _process_update(self, update: "Update", credentials: dict[str, str]) -> None:
        """Process a single update from Telegram."""
        from codegeass.notifications.interactive import CallbackQuery as CQ

        # Handle callback queries (button clicks)
        if update.callback_query:
            cq = update.callback_query
            print(f"[Callback Server] Button clicked: {cq.data}")
            callback = CQ(
                query_id=str(cq.id),
                from_user_id=str(cq.from_user.id),
                from_username=cq.from_user.username,
                message_id=cq.message.message_id if cq.message else 0,
                chat_id=str(cq.message.chat.id) if cq.message else "",
                callback_data=cq.data or "",
                provider="telegram",
            )

            success, message = await self._handler.handle_callback(callback, credentials)
            print(f"[Callback Server] Callback result: success={success}, message={message}")

        # Handle reply messages (for feedback)
        elif update.message and update.message.reply_to_message:
            msg = update.message
            print(f"[Callback Server] Reply received: '{msg.text[:50] if msg.text else '(no text)'}' replying to msg_id={msg.reply_to_message.message_id}", flush=True)
            handled, result = await self._handler.handle_reply_message(
                chat_id=str(msg.chat.id),
                user_id=str(msg.from_user.id) if msg.from_user else "",
                reply_to_message_id=msg.reply_to_message.message_id,
                text=msg.text or "",
            )
            print(f"[Callback Server] Reply result: handled={handled}, message={result}", flush=True)
        elif update.message:
            print(f"[Callback Server] Message received (not a reply): '{update.message.text[:50] if update.message.text else '(no text)'}'", flush=True)


# Global callback server instance
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
