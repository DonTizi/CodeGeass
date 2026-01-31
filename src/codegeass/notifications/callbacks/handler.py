"""Callback handler for interactive notification buttons."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from codegeass.notifications.callbacks.models import PendingFeedback
from codegeass.notifications.interactive import CallbackQuery

if TYPE_CHECKING:
    from codegeass.execution.plan_service import PlanApprovalService
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Handler for processing button callbacks from notification providers.

    Routes callback actions to the appropriate handlers:
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
        self._pending_feedback: dict[str, PendingFeedback] = {}
        self._feedback_timeout = 300  # 5 minutes

    async def handle_callback(
        self,
        callback: CallbackQuery,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Handle a callback query from a button click."""
        prefix, action, approval_id = callback.parse_action()

        if prefix != "plan":
            logger.debug(f"Unknown callback prefix: {prefix}")
            return False, "Unknown action"

        handlers = {
            "approve": self._handle_approve,
            "discuss": self._handle_discuss_request,
            "cancel": self._handle_cancel,
        }

        handler = handlers.get(action)
        if handler:
            return await handler(callback, approval_id, credentials)

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
            await self._answer_callback(callback, credentials, "Approving plan...")
            result = await self._plan_service.handle_approval(approval_id)

            if result and result.is_success:
                return True, "Plan approved and executed successfully!"
            elif result:
                return False, f"Execution failed: {result.error}"
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
            approval = self._plan_service.find_by_id(approval_id)
            if not approval:
                return False, "Approval not found"

            from codegeass.execution.plan_approval import ApprovalStatus

            if approval.status != ApprovalStatus.PENDING:
                return False, "Approval already processed"

            if not approval.can_discuss:
                return False, "Maximum iterations reached"

            await self._answer_callback(
                callback, credentials,
                "Please reply to this message with your feedback.",
                show_alert=True,
            )

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
        """Handle a reply message that might be feedback."""
        self._cleanup_expired_feedback()

        feedback_key = f"{chat_id}:{user_id}"
        pending = self._pending_feedback.get(feedback_key)

        if not pending:
            return False, ""

        if str(pending.message_id) != str(reply_to_message_id):
            return False, ""

        del self._pending_feedback[feedback_key]

        try:
            updated = await self._plan_service.handle_discuss(pending.approval_id, text)
            if updated:
                return True, "Feedback processed, new plan sent."
            return False, "Failed to process feedback"
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return False, f"Error: {e}"

    def _cleanup_expired_feedback(self) -> None:
        """Remove expired feedback requests."""
        now = datetime.now()
        expired = [k for k, p in self._pending_feedback.items() if p.expires_at < now]
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
