"""Approval action handlers for plan mode."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult
from codegeass.execution.output_parser import parse_stream_json
from codegeass.execution.plan_approval import ApprovalStatus, PendingApproval
from codegeass.execution.plan_service.message_sender import ApprovalMessageSender
from codegeass.execution.strategies import (
    ExecutionContext,
    ResumeWithApprovalStrategy,
    ResumeWithFeedbackStrategy,
)
from codegeass.execution.tracker import ExecutionTracker, get_execution_tracker
from codegeass.execution.worktree import WorktreeManager

if TYPE_CHECKING:
    from codegeass.storage.approval_repository import PendingApprovalRepository

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Handles approval, discuss, and cancel actions."""

    def __init__(
        self,
        approval_repo: PendingApprovalRepository,
        message_sender: ApprovalMessageSender,
    ):
        """Initialize with repositories."""
        self._approvals = approval_repo
        self._messenger = message_sender

    async def handle_approval(self, approval_id: str) -> ExecutionResult | None:
        """Handle user approving a plan."""
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return None

        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval {approval_id} is not pending: {approval.status}")
            return None

        approval.mark_approved()
        self._approvals.update(approval)

        await self._messenger.update_approval_messages(
            approval, status="Approved", details="Executing approved plan..."
        )

        approval.mark_executing()
        self._approvals.update(approval)

        execution_dir = self._get_execution_dir(approval)
        logger.info(f"Executing approved plan in: {execution_dir}")

        tracker = get_execution_tracker()
        execution_id = self._get_or_create_execution(tracker, approval, "Approval")

        try:
            result = await self._execute_approved_plan(
                approval, execution_dir, execution_id, tracker
            )
            await self._finalize_approval(tracker, execution_id, approval, result)
            self._cleanup_worktree(approval)
            return result

        except Exception as e:
            tracker.finish_execution(execution_id=execution_id, success=False, error=str(e))
            approval.mark_failed(str(e))
            self._approvals.update(approval)
            await self._messenger.update_approval_messages(
                approval, status="Failed", details=f"Error: {e}"
            )
            self._cleanup_worktree(approval)
            raise

    async def _execute_approved_plan(
        self,
        approval: PendingApproval,
        execution_dir: Path,
        execution_id: str,
        tracker: ExecutionTracker,
    ) -> ExecutionResult:
        """Execute the approved plan."""
        strategy = ResumeWithApprovalStrategy(timeout=approval.task_timeout)
        task = Task(
            id=approval.task_id,
            name=approval.task_name,
            schedule="* * * * *",
            working_dir=execution_dir,
            prompt="Execute approved plan",
            timeout=approval.task_timeout,
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

        return strategy.execute(context)

    async def _finalize_approval(
        self,
        tracker: ExecutionTracker,
        execution_id: str,
        approval: PendingApproval,
        result: ExecutionResult,
    ) -> None:
        """Finalize tracking and update approval status."""
        tracker.finish_execution(
            execution_id=execution_id,
            success=result.is_success,
            exit_code=result.exit_code,
            error=result.error,
        )

        if result.is_success:
            await self._handle_success(approval, result)
        else:
            approval.mark_failed(result.error or "Unknown error")

        self._approvals.update(approval)

    async def _handle_success(self, approval: PendingApproval, result: ExecutionResult) -> None:
        """Handle successful execution."""
        parsed = parse_stream_json(result.output)
        result_text = self._extract_result_text(parsed.text, result.output)
        approval.mark_completed(result.output)

        details = f"Execution completed in {result.duration_seconds:.1f}s\n\n"
        if len(result_text) > 3000:
            result_text = result_text[:3000] + "\n\n[Output truncated...]"
        details += f"<b>Output:</b>\n<code>{result_text}</code>"

        await self._messenger.update_approval_messages(
            approval, status="Completed", details=details
        )

    def _extract_result_text(self, parsed_text: str, raw_output: str) -> str:
        """Extract result text with fallback."""
        if parsed_text:
            return parsed_text

        try:
            import json

            for line in reversed(raw_output.strip().split("\n")):
                if line.strip():
                    data = json.loads(line.strip())
                    if isinstance(data.get("result"), str) and data["result"]:
                        return data["result"]
        except Exception:
            pass

        return "(Execution completed - no output captured)"

    async def handle_discuss(
        self, approval_id: str, feedback: str
    ) -> PendingApproval | None:
        """Handle user providing feedback on a plan."""
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

        await self._messenger.update_approval_messages(
            approval,
            status="Processing",
            details=f"Processing feedback (iteration {approval.iteration + 1})...",
        )

        execution_dir = self._get_execution_dir(approval)
        tracker = get_execution_tracker()
        execution_id = self._get_or_create_execution(
            tracker, approval, f"Discuss #{approval.iteration + 1}"
        )

        try:
            return await self._execute_feedback(
                approval, feedback, execution_dir, execution_id, tracker
            )
        except Exception as e:
            logger.error(f"Error handling discuss: {e}")
            tracker.set_waiting_approval(
                execution_id=execution_id,
                approval_id=approval.id,
                plan_text=f"Error: {str(e)}",
            )
            return None

    async def _execute_feedback(
        self,
        approval: PendingApproval,
        feedback: str,
        execution_dir: Path,
        execution_id: str,
        tracker: ExecutionTracker,
    ) -> PendingApproval | None:
        """Execute feedback strategy."""
        strategy = ResumeWithFeedbackStrategy(feedback=feedback, timeout=approval.task_timeout)
        task = Task(
            id=approval.task_id,
            name=approval.task_name,
            schedule="* * * * *",
            working_dir=execution_dir,
            prompt=feedback,
            timeout=approval.task_timeout,
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
            return await self._process_feedback_result(
                approval, feedback, result, execution_id, tracker
            )
        else:
            logger.error(f"Discuss failed: {result.error}")
            tracker.set_waiting_approval(
                execution_id=execution_id,
                approval_id=approval.id,
                plan_text=f"Discuss failed: {result.error}",
            )
            return None

    async def _process_feedback_result(
        self,
        approval: PendingApproval,
        feedback: str,
        result: ExecutionResult,
        execution_id: str,
        tracker: ExecutionTracker,
    ) -> PendingApproval:
        """Process successful feedback result."""
        parsed = parse_stream_json(result.output)
        new_session_id = parsed.session_id
        new_plan = parsed.text

        approval.add_feedback(feedback, new_plan)
        approval.plan_text = new_plan
        if new_session_id:
            approval.session_id = new_session_id

        self._approvals.update(approval)

        await self._messenger.remove_old_message_buttons(approval)

        tracker.set_waiting_approval(
            execution_id=execution_id,
            approval_id=approval.id,
            plan_text=new_plan[:500] if new_plan else None,
        )
        logger.info(f"Execution {execution_id} back to waiting_approval after discuss")

        return approval

    async def handle_cancel(self, approval_id: str) -> bool:
        """Handle user cancelling a plan."""
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return False

        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval {approval_id} is not pending: {approval.status}")
            return False

        approval.mark_cancelled()
        self._approvals.update(approval)

        await self._messenger.update_approval_messages(
            approval, status="Cancelled", details="Plan was cancelled by user."
        )

        tracker = get_execution_tracker()
        existing_execution = tracker.get_by_approval(approval.id)
        if existing_execution:
            tracker.finish_execution(
                execution_id=existing_execution.execution_id,
                success=False,
                error="Plan cancelled by user",
            )
            logger.info(f"Finished execution {existing_execution.execution_id} (cancelled)")

        self._cleanup_worktree(approval)
        return True

    def _get_execution_dir(self, approval: PendingApproval) -> Path:
        """Get the execution directory for an approval."""
        if approval.worktree_path:
            return Path(approval.worktree_path)
        return Path(approval.working_dir)

    def _get_or_create_execution(
        self, tracker: ExecutionTracker, approval: PendingApproval, suffix: str
    ) -> str:
        """Get existing execution or create a new one."""
        existing = tracker.get_by_approval(approval.id)
        if existing:
            tracker.update_execution(
                existing.execution_id, status="running", phase=f"executing {suffix.lower()}"
            )
            logger.info(f"Resuming existing execution {existing.execution_id}")
            return existing.execution_id

        execution_id = tracker.start_execution(
            task_id=approval.task_id,
            task_name=f"{approval.task_name} ({suffix})",
            session_id=approval.session_id,
        )
        logger.info(f"Created new execution {execution_id}")
        return execution_id

    def _cleanup_worktree(self, approval: PendingApproval) -> None:
        """Cleanup the worktree associated with an approval."""
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
