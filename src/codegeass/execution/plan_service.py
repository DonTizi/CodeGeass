"""Plan approval service for orchestrating interactive plan mode workflows."""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.output_parser import parse_stream_json
from codegeass.execution.plan_approval import (
    ApprovalStatus,
    MessageRef,
    PendingApproval,
)
from codegeass.execution.strategies import (
    ExecutionContext,
    PlanModeStrategy,
    ResumeWithApprovalStrategy,
    ResumeWithFeedbackStrategy,
)
from codegeass.execution.tracker import get_execution_tracker
from codegeass.execution.worktree import WorktreeManager
from codegeass.notifications.interactive import (
    InteractiveMessage,
    create_approval_status_message,
    create_plan_approval_message,
)
from codegeass.storage.approval_repository import PendingApprovalRepository

if TYPE_CHECKING:
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
        approval_repo: PendingApprovalRepository,
        channel_repo: "ChannelRepository",
    ):
        self._approvals = approval_repo
        self._channels = channel_repo
        self._plan_strategy = PlanModeStrategy()

    async def create_approval_from_result(
        self,
        task: Task,
        result: ExecutionResult,
    ) -> PendingApproval | None:
        """Create a pending approval from a plan mode execution result.

        Args:
            task: The task that was executed
            result: The execution result from plan mode

        Returns:
            PendingApproval if successful, None if failed to extract plan
        """
        if result.status != ExecutionStatus.SUCCESS:
            logger.error(f"Plan mode execution failed: {result.error}")
            return None

        # Parse the output to get session ID and plan
        parsed = parse_stream_json(result.output)
        session_id = parsed.session_id
        plan_text = parsed.text

        if not session_id:
            logger.error("Could not extract session_id from plan mode output")
            # Generate a placeholder - the approval will fail on resume
            session_id = f"unknown-{task.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create the pending approval
        approval = PendingApproval.create(
            task_id=task.id,
            task_name=task.name,
            session_id=session_id,
            plan_text=plan_text,
            working_dir=str(task.working_dir),
            timeout_seconds=task.plan_timeout,
            max_iterations=task.plan_max_iterations,
            task_timeout=task.timeout,  # Store original task execution timeout
        )

        # Save to repository
        self._approvals.save(approval)

        return approval

    async def send_approval_request(
        self,
        approval: PendingApproval,
        task: Task,
    ) -> bool:
        """Send interactive approval request to notification channels.

        Args:
            approval: The pending approval
            task: The task (for notification config)

        Returns:
            True if at least one message was sent successfully
        """
        from codegeass.notifications.models import NotificationConfig

        # Get notification config from task
        notification_config = NotificationConfig.from_dict(task.notifications)
        if not notification_config or not notification_config.channels:
            logger.warning(f"No notification channels configured for task {task.name}")
            return False

        # Create the interactive message
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
                result = await self._send_interactive_to_channel(
                    channel_id=channel_id,
                    message=message,
                )

                if result.get("success"):
                    # Store message reference for later editing
                    msg_ref = MessageRef(
                        message_id=result["message_id"],
                        chat_id=result.get("chat_id", ""),
                        provider=result.get("provider", "telegram"),
                    )
                    approval.add_message_ref(msg_ref)
                    success_count += 1

            except Exception as e:
                logger.error(f"Failed to send approval request to {channel_id}: {e}")

        # Update approval with message refs
        if success_count > 0:
            self._approvals.update(approval)

        return success_count > 0

    async def _send_interactive_to_channel(
        self,
        channel_id: str,
        message: InteractiveMessage,
    ) -> dict[str, Any]:
        """Send interactive message to a specific channel.

        Args:
            channel_id: The channel ID
            message: The interactive message

        Returns:
            Result dict with 'success', 'message_id', 'chat_id', 'provider'
        """
        from codegeass.notifications.registry import get_provider_registry

        # Get channel and credentials
        channel, credentials = self._channels.get_channel_with_credentials(channel_id)

        if not channel.enabled:
            return {"success": False, "error": "Channel disabled"}

        # Get provider
        registry = get_provider_registry()
        provider = registry.get(channel.provider)

        # Check if provider supports interactive messages
        if not hasattr(provider, "send_interactive"):
            logger.warning(f"Provider {channel.provider} does not support interactive messages")
            return {"success": False, "error": "Provider does not support interactive messages"}

        # Send the message
        result = await provider.send_interactive(channel, credentials, message)
        result["provider"] = channel.provider

        return result

    async def handle_approval(self, approval_id: str) -> ExecutionResult | None:
        """Handle user approving a plan.

        This resumes the Claude session with full permissions to execute the plan.

        Args:
            approval_id: The approval ID

        Returns:
            ExecutionResult if executed, None if approval not found
        """
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return None

        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval {approval_id} is not pending: {approval.status}")
            return None

        # Mark as approved and executing
        approval.mark_approved()
        self._approvals.update(approval)

        # Update notification messages
        await self._update_approval_messages(
            approval,
            status="Approved",
            details="Executing approved plan...",
        )

        approval.mark_executing()
        self._approvals.update(approval)

        # Create a minimal task for execution context
        from codegeass.core.entities import Task

        # Use worktree path if available, otherwise original working_dir
        execution_dir = (
            Path(approval.worktree_path) if approval.worktree_path else Path(approval.working_dir)
        )
        logger.info(f"Executing approved plan in: {execution_dir}")

        # Get tracker and find the existing execution (waiting_approval)
        tracker = get_execution_tracker()
        existing_execution = tracker.get_by_approval(approval.id)

        if existing_execution:
            # Resume the existing execution
            execution_id = existing_execution.execution_id
            tracker.update_execution(
                execution_id, status="running", phase="executing approved plan"
            )
            logger.info(f"Resuming existing execution {execution_id} for approval")
        else:
            # Fallback: create new execution if not found
            execution_id = tracker.start_execution(
                task_id=approval.task_id,
                task_name=f"{approval.task_name} (Approval)",
                session_id=approval.session_id,
            )
            logger.info(f"Created new execution {execution_id} (no existing found)")

        try:
            # Execute with resume strategy using original task timeout
            strategy = ResumeWithApprovalStrategy(timeout=approval.task_timeout)
            task = Task(
                id=approval.task_id,
                name=approval.task_name,
                schedule="* * * * *",  # Dummy schedule
                working_dir=execution_dir,
                prompt="Execute approved plan",  # Placeholder (required by Task)
                timeout=approval.task_timeout,  # Use original task timeout
            )
            context = ExecutionContext(
                task=task,
                skill=None,
                prompt="",
                working_dir=execution_dir,
                session_id=approval.session_id,
                execution_id=execution_id,
                tracker=tracker,
            )

            result = strategy.execute(context)

            # Finish tracking
            tracker.finish_execution(
                execution_id=execution_id,
                success=result.is_success,
                exit_code=result.exit_code,
                error=result.error,
            )

            # Update approval status
            if result.is_success:
                # Parse output to get the actual result text
                logger.info(f"[DEBUG] Raw output length: {len(result.output)}")
                logger.info(f"[DEBUG] Raw output first 200 chars: {result.output[:200]}")
                parsed_result = parse_stream_json(result.output)
                result_text = parsed_result.text
                logger.info(f"[DEBUG] Parsed text length: {len(result_text)}")
                preview = result_text[:200] if result_text else "(empty)"
                logger.info(f"[DEBUG] Parsed text first 200 chars: {preview}")

                # Fallback if parsing returned empty text
                if not result_text and result.output:
                    try:
                        # Try extracting result field directly from last line
                        import json as json_mod

                        for line in reversed(result.output.strip().split("\n")):
                            if line.strip():
                                data = json_mod.loads(line.strip())
                                if isinstance(data.get("result"), str) and data["result"]:
                                    result_text = data["result"]
                                    break
                    except Exception:
                        pass
                if not result_text:
                    result_text = "(Execution completed - no output captured)"

                approval.mark_completed(result.output)

                # Build details with the actual output
                details = f"Execution completed in {result.duration_seconds:.1f}s\n\n"
                # Truncate if too long (Telegram limit)
                if len(result_text) > 3000:
                    result_text = result_text[:3000] + "\n\n[Output truncated...]"
                details += f"<b>Output:</b>\n<code>{result_text}</code>"

                await self._update_approval_messages(
                    approval,
                    status="Completed",
                    details=details,
                )
            else:
                approval.mark_failed(result.error or "Unknown error")
                await self._update_approval_messages(
                    approval,
                    status="Failed",
                    details=f"Error: {result.error}",
                )

            self._approvals.update(approval)

            # Cleanup worktree after execution is done
            self._cleanup_worktree(approval)

            return result

        except Exception as e:
            # Finish tracking with failure
            tracker.finish_execution(
                execution_id=execution_id,
                success=False,
                error=str(e),
            )
            approval.mark_failed(str(e))
            self._approvals.update(approval)
            await self._update_approval_messages(
                approval,
                status="Failed",
                details=f"Error: {e}",
            )
            # Cleanup worktree even on failure
            self._cleanup_worktree(approval)
            raise

    async def handle_discuss(
        self,
        approval_id: str,
        feedback: str,
    ) -> PendingApproval | None:
        """Handle user providing feedback on a plan.

        This resumes the Claude session with the feedback, still in plan mode,
        to get an updated plan.

        Args:
            approval_id: The approval ID
            feedback: User's feedback on the plan

        Returns:
            Updated PendingApproval with new plan, or None if failed
        """
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return None

        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval {approval_id} is not pending: {approval.status}")
            return None

        if not approval.can_discuss:
            logger.warning(f"Approval {approval_id} has reached max iterations")
            return None

        # Update messages to show "Processing feedback..."
        await self._update_approval_messages(
            approval,
            status="Processing",
            details=f"Processing feedback (iteration {approval.iteration + 1})...",
        )

        # Use worktree path if available, otherwise original working_dir
        execution_dir = (
            Path(approval.worktree_path) if approval.worktree_path else Path(approval.working_dir)
        )
        logger.info(f"Processing feedback in: {execution_dir}")

        # Get tracker and find the existing execution (waiting_approval)
        tracker = get_execution_tracker()
        existing_execution = tracker.get_by_approval(approval.id)

        if existing_execution:
            # Resume the existing execution
            execution_id = existing_execution.execution_id
            tracker.update_execution(
                execution_id,
                status="running",
                phase=f"discussing (iteration {approval.iteration + 1})",
            )
            logger.info(f"Resuming existing execution {execution_id} for discuss")
        else:
            # Fallback: create new execution if not found
            execution_id = tracker.start_execution(
                task_id=approval.task_id,
                task_name=f"{approval.task_name} (Discuss #{approval.iteration + 1})",
                session_id=approval.session_id,
            )
            logger.info(f"Created new execution {execution_id} (no existing found)")

        try:
            # Execute with feedback strategy using original task timeout
            strategy = ResumeWithFeedbackStrategy(feedback=feedback, timeout=approval.task_timeout)
            task = Task(
                id=approval.task_id,
                name=approval.task_name,
                schedule="* * * * *",
                working_dir=execution_dir,
                prompt=feedback,  # Use feedback as prompt (required by Task)
                timeout=approval.task_timeout,  # Use original task timeout
            )
            context = ExecutionContext(
                task=task,
                skill=None,
                prompt=feedback,
                working_dir=execution_dir,
                session_id=approval.session_id,
                execution_id=execution_id,
                tracker=tracker,
            )

            result = strategy.execute(context)

            if result.is_success:
                # Parse new plan
                parsed_feedback = parse_stream_json(result.output)
                new_session_id = parsed_feedback.session_id
                new_plan = parsed_feedback.text

                # Update approval with new plan
                approval.add_feedback(feedback, new_plan)
                approval.plan_text = new_plan
                if new_session_id:
                    approval.session_id = new_session_id

                self._approvals.update(approval)

                # Send new approval message with updated plan
                # First, remove buttons from old messages
                await self._remove_old_message_buttons(approval)

                # Create new message with updated plan
                from codegeass.core.entities import Task as TaskEntity

                task = TaskEntity(
                    id=approval.task_id,
                    name=approval.task_name,
                    schedule="* * * * *",
                    working_dir=Path(approval.working_dir),
                    prompt="Updated plan",  # Placeholder (required by Task)
                    plan_mode=True,
                    plan_timeout=approval.timeout_seconds,
                    plan_max_iterations=approval.max_iterations,
                )
                task.notifications = {"channels": self._get_channel_ids(approval)}

                # Clear old message refs and send new message
                approval.channel_messages = []
                await self.send_approval_request(approval, task)

                # Set execution back to waiting_approval with the new plan
                tracker.set_waiting_approval(
                    execution_id=execution_id,
                    approval_id=approval.id,
                    plan_text=new_plan[:500] if new_plan else None,
                )
                logger.info(f"Execution {execution_id} back to waiting_approval after discuss")

                return approval
            else:
                # Discuss failed - keep waiting for approval, just log the error
                logger.error(f"Discuss failed: {result.error}")
                tracker.set_waiting_approval(
                    execution_id=execution_id,
                    approval_id=approval.id,
                    plan_text=f"Discuss failed: {result.error}",
                )
                return None

        except Exception as e:
            # Error during discuss - keep waiting for approval
            logger.error(f"Error handling discuss: {e}")
            tracker.set_waiting_approval(
                execution_id=execution_id,
                approval_id=approval.id,
                plan_text=f"Error: {str(e)}",
            )
            return None

    async def handle_cancel(self, approval_id: str) -> bool:
        """Handle user cancelling a plan.

        Args:
            approval_id: The approval ID

        Returns:
            True if cancelled successfully
        """
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return False

        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval {approval_id} is not pending: {approval.status}")
            return False

        approval.mark_cancelled()
        self._approvals.update(approval)

        await self._update_approval_messages(
            approval,
            status="Cancelled",
            details="Plan was cancelled by user.",
        )

        # Finish the execution as cancelled
        tracker = get_execution_tracker()
        existing_execution = tracker.get_by_approval(approval.id)
        if existing_execution:
            tracker.finish_execution(
                execution_id=existing_execution.execution_id,
                success=False,
                error="Plan cancelled by user",
            )
            logger.info(f"Finished execution {existing_execution.execution_id} (cancelled)")

        # Cleanup worktree on cancel
        self._cleanup_worktree(approval)

        return True

    def _cleanup_worktree(self, approval: PendingApproval) -> None:
        """Cleanup the worktree associated with an approval.

        Args:
            approval: The approval whose worktree should be cleaned up
        """
        if not approval.worktree_path:
            return

        try:
            worktree_path = Path(approval.worktree_path)
            original_dir = Path(approval.working_dir)

            if worktree_path.exists():
                success = WorktreeManager.remove_worktree(original_dir, worktree_path)
                if success:
                    logger.info(f"Cleaned up worktree: {worktree_path}")
                else:
                    logger.warning(f"Failed to cleanup worktree: {worktree_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up worktree: {e}")

    async def _update_approval_messages(
        self,
        approval: PendingApproval,
        status: str,
        details: str = "",
    ) -> None:
        """Update all notification messages for an approval.

        Removes buttons and updates text to show current status.
        """
        from codegeass.notifications.registry import get_provider_registry

        message_text = create_approval_status_message(
            task_name=approval.task_name,
            status=status,
            details=details,
        )

        registry = get_provider_registry()

        for msg_ref in approval.channel_messages:
            try:
                # Get channel info from the provider
                provider = registry.get(msg_ref.provider)

                # Find channel by chat_id
                all_channels = self._channels.find_all()
                channel = None
                for ch in all_channels:
                    if str(ch.config.get("chat_id")) == str(msg_ref.chat_id):
                        channel = ch
                        break

                if not channel:
                    continue

                _, credentials = self._channels.get_channel_with_credentials(channel.id)

                if hasattr(provider, "remove_buttons"):
                    await provider.remove_buttons(
                        channel=channel,
                        credentials=credentials,
                        message_id=msg_ref.message_id,
                        new_text=message_text,
                    )

            except Exception as e:
                logger.warning(f"Failed to update message {msg_ref.message_id}: {e}")

    async def _remove_old_message_buttons(self, approval: PendingApproval) -> None:
        """Remove buttons from old messages without changing text."""
        from codegeass.notifications.registry import get_provider_registry

        registry = get_provider_registry()

        for msg_ref in approval.channel_messages:
            try:
                provider = registry.get(msg_ref.provider)

                all_channels = self._channels.find_all()
                channel = None
                for ch in all_channels:
                    if str(ch.config.get("chat_id")) == str(msg_ref.chat_id):
                        channel = ch
                        break

                if not channel:
                    continue

                _, credentials = self._channels.get_channel_with_credentials(channel.id)

                if hasattr(provider, "remove_buttons"):
                    await provider.remove_buttons(
                        channel=channel,
                        credentials=credentials,
                        message_id=msg_ref.message_id,
                    )

            except Exception as e:
                logger.warning(f"Failed to remove buttons from {msg_ref.message_id}: {e}")

    def _get_channel_ids(self, approval: PendingApproval) -> list[str]:
        """Get channel IDs from approval message refs."""
        channel_ids = []
        all_channels = self._channels.find_all()

        for msg_ref in approval.channel_messages:
            for ch in all_channels:
                if str(ch.config.get("chat_id")) == str(msg_ref.chat_id):
                    if ch.id not in channel_ids:
                        channel_ids.append(ch.id)
                    break

        return channel_ids

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
        # First, find pending approvals that have expired
        pending = self._approvals.find_pending()
        expired_approvals = [a for a in pending if a.is_expired]

        # Cleanup worktrees for expired approvals
        for approval in expired_approvals:
            self._cleanup_worktree(approval)

        # Then let the repository mark them as expired
        return self._approvals.cleanup_expired()


# Global service instance
_plan_service: PlanApprovalService | None = None


def get_plan_approval_service(
    approval_repo: PendingApprovalRepository | None = None,
    channel_repo: "ChannelRepository | None" = None,
) -> PlanApprovalService:
    """Get the plan approval service instance.

    Args:
        approval_repo: Approval repository. Required on first call.
        channel_repo: Channel repository. Required on first call.

    Returns:
        PlanApprovalService instance
    """
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
