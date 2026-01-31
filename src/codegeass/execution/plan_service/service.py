"""Plan approval service facade."""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.output_parser import parse_stream_json
from codegeass.execution.plan_approval import MessageRef, PendingApproval
from codegeass.execution.plan_service.approval_handler import ApprovalHandler
from codegeass.execution.plan_service.message_sender import ApprovalMessageSender
from codegeass.notifications.interactive import create_plan_approval_message

if TYPE_CHECKING:
    from codegeass.storage.approval_repository import PendingApprovalRepository
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


class PlanApprovalService:
    """Service for orchestrating plan mode approval workflows.

    This service handles the full lifecycle of plan approvals:
    1. Execute task in plan mode
    2. Extract session ID and plan from output
    3. Send interactive message with buttons to notification channels
    4. Handle user actions (approve, discuss, cancel)
    5. Resume session with appropriate strategy
    """

    def __init__(
        self,
        approval_repo: "PendingApprovalRepository",
        channel_repo: "ChannelRepository",
    ):
        """Initialize with repositories."""
        self._approvals = approval_repo
        self._channels = channel_repo
        self._messenger = ApprovalMessageSender(channel_repo)
        self._handler = ApprovalHandler(approval_repo, self._messenger)

    async def create_approval_from_result(
        self,
        task: Task,
        result: ExecutionResult,
    ) -> PendingApproval | None:
        """Create a pending approval from a plan mode execution result."""
        if result.status != ExecutionStatus.SUCCESS:
            logger.error(f"Plan mode execution failed: {result.error}")
            return None

        parsed = parse_stream_json(result.output)
        session_id = parsed.session_id
        plan_text = parsed.text

        if not session_id:
            logger.error("Could not extract session_id from plan mode output")
            session_id = f"unknown-{task.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        approval = PendingApproval.create(
            task_id=task.id,
            task_name=task.name,
            session_id=session_id,
            plan_text=plan_text,
            working_dir=str(task.working_dir),
            timeout_seconds=task.plan_timeout,
            max_iterations=task.plan_max_iterations,
            task_timeout=task.timeout,
        )

        self._approvals.save(approval)
        return approval

    async def send_approval_request(
        self,
        approval: PendingApproval,
        task: Task,
    ) -> bool:
        """Send interactive approval request to notification channels."""
        from codegeass.notifications.models import NotificationConfig

        notification_config = NotificationConfig.from_dict(task.notifications)
        if not notification_config or not notification_config.channels:
            logger.warning(f"No notification channels configured for task {task.name}")
            return False

        message = create_plan_approval_message(
            approval_id=approval.id,
            task_name=task.name,
            plan_text=approval.plan_text,
            iteration=approval.iteration,
            max_iterations=approval.max_iterations,
        )

        success_count = 0

        for channel_id in notification_config.channels:
            try:
                result = await self._messenger.send_interactive_to_channel(
                    channel_id=channel_id,
                    message=message,
                )

                if result.get("success"):
                    success_count += 1
                    # Store message reference for later editing (only if we got a message_id)
                    # Teams webhooks don't return message IDs, so we skip storing refs for them
                    msg_id = result.get("message_id")
                    if msg_id is not None:
                        msg_ref = MessageRef(
                            message_id=msg_id,
                            chat_id=result.get("chat_id", ""),
                            provider=result.get("provider", "telegram"),
                        )
                        approval.add_message_ref(msg_ref)
                        logger.info(f"Stored message ref for {channel_id}: msg_id={msg_id}")
                    else:
                        logger.info(f"Sent to {channel_id} (no message_id - Teams webhook)")

            except Exception as e:
                logger.error(f"Failed to send approval request to {channel_id}: {e}")

        if success_count > 0:
            self._approvals.update(approval)

        return success_count > 0

    async def handle_approval(self, approval_id: str) -> ExecutionResult | None:
        """Handle user approving a plan."""
        return await self._handler.handle_approval(approval_id)

    async def handle_discuss(
        self,
        approval_id: str,
        feedback: str,
    ) -> PendingApproval | None:
        """Handle user providing feedback on a plan."""
        result = await self._handler.handle_discuss(approval_id, feedback)

        # If successful, send new approval request
        if result:
            task = Task(
                id=result.task_id,
                name=result.task_name,
                schedule="* * * * *",
                working_dir=Path(result.working_dir),
                prompt="Updated plan",
                plan_mode=True,
                plan_timeout=result.timeout_seconds,
                plan_max_iterations=result.max_iterations,
            )
            task.notifications = {
                "channels": self._messenger.get_channel_ids_from_approval(result)
            }

            result.channel_messages = []
            await self.send_approval_request(result, task)

        return result

    async def handle_cancel(self, approval_id: str) -> bool:
        """Handle user cancelling a plan."""
        return await self._handler.handle_cancel(approval_id)

    def find_pending(self) -> list[PendingApproval]:
        """Find all pending approvals."""
        return self._approvals.find_pending()

    def find_by_id(self, approval_id: str) -> PendingApproval | None:
        """Find approval by ID."""
        return self._approvals.find_by_id(approval_id)

    def find_by_task_id(self, task_id: str) -> PendingApproval | None:
        """Find approval by task ID."""
        return self._approvals.find_by_task_id(task_id)

    def cleanup_expired(self) -> int:
        """Cleanup expired approvals (including worktrees) and return count."""
        pending = self._approvals.find_pending()
        expired_approvals = [a for a in pending if a.is_expired]

        for approval in expired_approvals:
            self._handler._cleanup_worktree(approval)

        return self._approvals.cleanup_expired()


# Global service instance
_plan_service: PlanApprovalService | None = None


def get_plan_approval_service(
    approval_repo: "PendingApprovalRepository | None" = None,
    channel_repo: "ChannelRepository | None" = None,
) -> PlanApprovalService:
    """Get the plan approval service instance."""
    global _plan_service

    if _plan_service is None:
        if approval_repo is None or channel_repo is None:
            raise ValueError("approval_repo and channel_repo must be provided on first call")
        _plan_service = PlanApprovalService(approval_repo, channel_repo)

    return _plan_service


def reset_plan_approval_service() -> None:
    """Reset the global service (for testing)."""
    global _plan_service
    _plan_service = None
