"""Notification handler for scheduler integration."""

import logging
from typing import TYPE_CHECKING

from codegeass.execution.output_parser import parse_stream_json
from codegeass.execution.tracker import get_execution_tracker
from codegeass.notifications.interactive import create_plan_approval_message
from codegeass.notifications.interactive_sender import send_interactive_to_channel
from codegeass.notifications.models import NotificationConfig, NotificationEvent
from codegeass.notifications.service import NotificationService

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult
    from codegeass.scheduling.scheduler import Scheduler
    from codegeass.storage.approval_repository import PendingApprovalRepository
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handler that connects the Scheduler to the NotificationService.

    This class provides async callback methods that the Scheduler calls
    when task events occur. The Scheduler handles running the async callbacks
    properly whether in sync or async context.

    Also handles plan mode approval workflow by:
    1. Creating pending approvals when plan mode tasks complete their planning phase
    2. Sending interactive messages with Approve/Discuss/Cancel buttons
    """

    def __init__(
        self,
        service: NotificationService,
        approval_repo: "PendingApprovalRepository | None" = None,
        channel_repo: "ChannelRepository | None" = None,
    ):
        self._service = service
        self._approval_repo = approval_repo
        self._channel_repo = channel_repo

    async def on_task_start(self, task: "Task") -> None:
        """Async callback called when a task starts execution.

        Args:
            task: The task being started
        """
        logger.debug(f"Task starting: {task.name}")

        # Check if task has notifications configured
        if not task.notifications:
            logger.debug(f"No notifications configured for {task.name}")
            return

        try:
            result = await self._service.notify(
                event=NotificationEvent.TASK_START,
                task=task,
                result=None,
            )
            logger.debug(f"Start notification result: {result}")
        except Exception as e:
            logger.error(f"Failed to send start notification: {e}")

    async def on_task_complete(self, task: "Task", result: "ExecutionResult") -> None:
        """Async callback called when a task completes execution.

        Args:
            task: The task that completed
            result: The execution result
        """
        logger.debug(f"Task completed: {task.name}, status={result.status}")

        # Check if task has notifications configured
        if not task.notifications:
            logger.debug(f"No notifications configured for {task.name}")
            return

        # Determine specific event based on status
        event = NotificationEvent.TASK_COMPLETE
        if result.is_success:
            event = NotificationEvent.TASK_SUCCESS
        else:
            event = NotificationEvent.TASK_FAILURE

        try:
            notify_result = await self._service.notify(
                event=event,
                task=task,
                result=result,
            )
            logger.debug(f"Completion notification result: {notify_result}")
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")

    async def on_plan_approval(self, task: "Task", result: "ExecutionResult") -> None:
        """Async callback called when a plan mode task needs approval.

        This is called after a plan mode task completes its planning phase.
        Instead of executing, we:
        1. Create a pending approval
        2. Send an interactive message with Approve/Discuss/Cancel buttons
        3. Wait for user action via Telegram callback

        Args:
            task: The task that generated the plan
            result: The execution result containing the plan
        """
        logger.info(f"Plan approval needed: {task.name}")

        # Check if task has notifications configured
        if not task.notifications:
            logger.warning(
                f"Plan mode task {task.name} has no notifications - cannot send approval request"
            )
            return

        # Check if we have the required repositories
        if not self._approval_repo or not self._channel_repo:
            logger.error("Approval or channel repository not configured for plan approval")
            return

        try:
            # Parse session_id and plan from result output
            parsed = parse_stream_json(result.output)
            session_id = parsed.session_id
            plan_text = parsed.text

            if not session_id:
                logger.error("Could not extract session_id from plan mode output")
                # Fall back to task completion notification
                await self.on_task_complete(task, result)
                return

            # Create pending approval
            from codegeass.execution.plan_approval import MessageRef, PendingApproval

            # Get worktree_path from result metadata (for isolated execution)
            worktree_path = None
            if result.metadata and "worktree_path" in result.metadata:
                worktree_path = result.metadata["worktree_path"]
                logger.debug(f"Using worktree for isolation: {worktree_path}")

            # Get notification channels to store in approval
            config = NotificationConfig.from_dict(task.notifications)
            channel_ids = config.channels if config else []

            approval = PendingApproval.create(
                task_id=task.id,
                task_name=task.name,
                session_id=session_id,
                plan_text=plan_text,
                working_dir=str(task.working_dir),
                timeout_seconds=task.plan_timeout,
                max_iterations=task.plan_max_iterations,
                worktree_path=worktree_path,
                task_timeout=task.timeout,  # Store original task execution timeout
                notification_channels=channel_ids,  # Store channel IDs for discuss flow
            )

            logger.info(f"Created approval: {approval.id}")

            # Save approval
            self._approval_repo.save(approval)

            # Create interactive message with buttons
            message = create_plan_approval_message(
                approval_id=approval.id,
                task_name=task.name,
                plan_text=plan_text,
                iteration=0,
                max_iterations=task.plan_max_iterations,
            )

            # Send to all configured channels
            if not channel_ids:
                logger.warning("No channels in notification config")
                return

            for channel_id in channel_ids:
                logger.debug(f"Sending approval to channel: {channel_id}")
                try:
                    msg_result = await send_interactive_to_channel(
                        channel_repo=self._channel_repo,
                        channel_id=channel_id,
                        message=message,
                    )
                    logger.debug(f"send_interactive_to_channel result: {msg_result}")

                    if msg_result.get("success"):
                        # Store message reference for later editing (only if we got a message_id)
                        # Teams webhooks don't return message IDs, so we skip storing refs for them
                        msg_id = msg_result.get("message_id")
                        if msg_id is not None:
                            msg_ref = MessageRef(
                                message_id=msg_id,
                                chat_id=msg_result.get("chat_id", ""),
                                provider=msg_result.get("provider", "telegram"),
                            )
                            approval.add_message_ref(msg_ref)
                            logger.info(f"Sent approval to {channel_id}: msg={msg_id}")
                        else:
                            # Provider doesn't support message editing (e.g., Teams)
                            logger.info(f"Sent approval to {channel_id} (no message_id returned)")
                    else:
                        logger.warning(
                            f"send_interactive returned success=False for {channel_id}: "
                            f"{msg_result.get('error', 'unknown')}"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to send approval request to {channel_id}: {e}", exc_info=True
                    )

            # Update approval with message refs
            self._approval_repo.save(approval)
            logger.info(f"Approval {approval.id} saved with {len(approval.channel_messages)} refs")

            # Set execution to waiting_approval state
            # This keeps it visible in the dashboard with "Waiting for Approval" status
            execution_id = result.metadata.get("execution_id") if result.metadata else None
            if execution_id:
                tracker = get_execution_tracker()
                tracker.set_waiting_approval(
                    execution_id=execution_id,
                    approval_id=approval.id,
                    plan_text=plan_text[:500] if plan_text else None,
                )
                logger.debug(f"Execution {execution_id} set to waiting_approval")
            else:
                logger.warning("No execution_id - cannot set waiting_approval")

        except Exception as e:
            logger.error(f"Failed to create plan approval: {e}", exc_info=True)

    def register_with_scheduler(self, scheduler: "Scheduler") -> None:
        """Register this handler's callbacks with a Scheduler.

        Args:
            scheduler: The scheduler to register with
        """
        scheduler.set_callbacks(
            on_start=self.on_task_start,
            on_complete=self.on_task_complete,
            on_plan_approval=self.on_plan_approval,
        )
        logger.debug("Handler registered with scheduler (with plan approval support)")


def create_notification_handler(service: NotificationService) -> NotificationHandler:
    """Create a notification handler.

    Args:
        service: The notification service to use

    Returns:
        NotificationHandler instance
    """
    return NotificationHandler(service)
