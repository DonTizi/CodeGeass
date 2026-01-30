"""Approval service for dashboard API."""


from codegeass.execution.plan_approval import ApprovalStatus as CoreApprovalStatus
from codegeass.execution.plan_service import PlanApprovalService
from codegeass.storage.approval_repository import PendingApprovalRepository
from codegeass.storage.channel_repository import ChannelRepository

from ..models import (
    Approval,
    ApprovalActionResult,
    ApprovalStats,
    ApprovalSummary,
)
from ..models import (
    ApprovalStatusModel as ModelApprovalStatus,
)


class ApprovalService:
    """Service for managing plan approvals via dashboard."""

    def __init__(
        self,
        approval_repo: PendingApprovalRepository,
        channel_repo: ChannelRepository,
    ):
        self._approvals = approval_repo
        self._channels = channel_repo
        self._plan_service = PlanApprovalService(approval_repo, channel_repo)

    def _to_model(self, approval) -> Approval:
        """Convert core approval to API model."""
        from ..models.approval import FeedbackEntry, MessageRef

        return Approval(
            id=approval.id,
            task_id=approval.task_id,
            task_name=approval.task_name,
            session_id=approval.session_id,
            plan_text=approval.plan_text,
            working_dir=approval.working_dir,
            status=ModelApprovalStatus(approval.status.value),
            iteration=approval.iteration,
            max_iterations=approval.max_iterations,
            timeout_seconds=approval.timeout_seconds,
            created_at=approval.created_at,
            expires_at=approval.expires_at,
            channel_messages=[
                MessageRef(
                    message_id=m.message_id,
                    chat_id=m.chat_id,
                    provider=m.provider,
                )
                for m in approval.channel_messages
            ],
            feedback_history=[
                FeedbackEntry(
                    feedback=f.feedback,
                    timestamp=f.timestamp,
                    plan_response=f.plan_response,
                )
                for f in approval.feedback_history
            ],
            final_output=approval.final_output,
            error=approval.error,
        )

    def _to_summary(self, approval) -> ApprovalSummary:
        """Convert core approval to summary model."""
        return ApprovalSummary(
            id=approval.id,
            task_id=approval.task_id,
            task_name=approval.task_name,
            status=ModelApprovalStatus(approval.status.value),
            iteration=approval.iteration,
            max_iterations=approval.max_iterations,
            created_at=approval.created_at,
            expires_at=approval.expires_at,
            is_expired=approval.is_expired,
        )

    def list_approvals(self, pending_only: bool = False) -> list[ApprovalSummary]:
        """List all approvals or just pending ones."""
        if pending_only:
            approvals = self._approvals.find_pending()
        else:
            approvals = self._approvals.find_all()

        return [self._to_summary(a) for a in approvals]

    def get_approval(self, approval_id: str) -> Approval | None:
        """Get full approval details."""
        approval = self._approvals.find_by_id(approval_id)
        if not approval:
            return None
        return self._to_model(approval)

    def get_approval_by_task(self, task_id: str) -> Approval | None:
        """Get approval by task ID."""
        approval = self._approvals.find_by_task_id(task_id)
        if not approval:
            return None
        return self._to_model(approval)

    async def approve(self, approval_id: str) -> ApprovalActionResult:
        """Approve a pending plan and execute it."""
        try:
            result = await self._plan_service.handle_approval(approval_id)

            if result and result.is_success:
                approval = self._approvals.find_by_id(approval_id)
                return ApprovalActionResult(
                    success=True,
                    message="Plan approved and executed successfully",
                    approval=self._to_model(approval) if approval else None,
                )
            elif result:
                approval = self._approvals.find_by_id(approval_id)
                return ApprovalActionResult(
                    success=False,
                    message=f"Execution failed: {result.error}",
                    approval=self._to_model(approval) if approval else None,
                )
            else:
                return ApprovalActionResult(
                    success=False,
                    message="Approval not found or already processed",
                    approval=None,
                )

        except Exception as e:
            return ApprovalActionResult(
                success=False,
                message=f"Error: {str(e)}",
                approval=None,
            )

    async def discuss(self, approval_id: str, feedback: str) -> ApprovalActionResult:
        """Provide feedback on a plan for iterative refinement."""
        try:
            updated = await self._plan_service.handle_discuss(approval_id, feedback)

            if updated:
                return ApprovalActionResult(
                    success=True,
                    message="Feedback processed, new plan generated",
                    approval=self._to_model(updated),
                )
            else:
                return ApprovalActionResult(
                    success=False,
                    message="Failed to process feedback",
                    approval=None,
                )

        except Exception as e:
            return ApprovalActionResult(
                success=False,
                message=f"Error: {str(e)}",
                approval=None,
            )

    async def cancel(self, approval_id: str) -> ApprovalActionResult:
        """Cancel a pending plan."""
        try:
            success = await self._plan_service.handle_cancel(approval_id)

            if success:
                approval = self._approvals.find_by_id(approval_id)
                return ApprovalActionResult(
                    success=True,
                    message="Plan cancelled",
                    approval=self._to_model(approval) if approval else None,
                )
            else:
                return ApprovalActionResult(
                    success=False,
                    message="Approval not found or already processed",
                    approval=None,
                )

        except Exception as e:
            return ApprovalActionResult(
                success=False,
                message=f"Error: {str(e)}",
                approval=None,
            )

    def get_stats(self) -> ApprovalStats:
        """Get approval statistics."""
        all_approvals = self._approvals.find_all()

        stats = {
            "total": len(all_approvals),
            "pending": 0,
            "approved": 0,
            "cancelled": 0,
            "expired": 0,
            "failed": 0,
            "completed": 0,
        }

        for approval in all_approvals:
            status = approval.status.value
            if status in stats:
                stats[status] += 1

        # Also count executing as part of approved
        for approval in all_approvals:
            if approval.status == CoreApprovalStatus.EXECUTING:
                stats["approved"] += 1

        return ApprovalStats(**stats)

    def cleanup_expired(self) -> int:
        """Mark expired approvals and return count."""
        return self._approvals.cleanup_expired()

    def cleanup_old(self, days: int = 30) -> int:
        """Remove old completed/cancelled approvals."""
        return self._approvals.cleanup_old(days)

    def delete(self, approval_id: str) -> bool:
        """Delete an approval."""
        return self._approvals.delete(approval_id)
