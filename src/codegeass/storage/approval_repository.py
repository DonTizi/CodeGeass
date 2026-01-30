"""Repository for pending plan approvals using YAML storage."""

from datetime import datetime
from pathlib import Path

from codegeass.execution.plan_approval import ApprovalStatus, PendingApproval
from codegeass.storage.yaml_backend import YAMLListBackend


class PendingApprovalRepository:
    """Repository for pending approval persistence using YAML files.

    Stores approvals in data/approvals.yaml with the structure:
    approvals:
      - id: abc123
        task_id: xyz789
        ...
    """

    def __init__(self, approvals_file: Path):
        """Initialize with path to approvals.yaml."""
        self._backend = YAMLListBackend(approvals_file, list_key="approvals")

    def save(self, approval: PendingApproval) -> None:
        """Save a new approval or update existing one."""
        existing = self.find_by_id(approval.id)
        if existing:
            self.update(approval)
        else:
            self._backend.append(approval.to_dict())

    def find_by_id(self, approval_id: str) -> PendingApproval | None:
        """Find approval by ID."""
        data = self._backend.find_by_key("id", approval_id)
        return PendingApproval.from_dict(data) if data else None

    def find_by_task_id(self, task_id: str) -> PendingApproval | None:
        """Find approval by task ID.

        Returns the most recent pending approval for a task.
        """
        all_approvals = self.find_all()
        task_approvals = [a for a in all_approvals if a.task_id == task_id]
        if not task_approvals:
            return None
        # Return most recent
        task_approvals.sort(key=lambda a: a.created_at, reverse=True)
        return task_approvals[0]

    def find_by_session_id(self, session_id: str) -> PendingApproval | None:
        """Find approval by Claude session ID."""
        data = self._backend.find_by_key("session_id", session_id)
        return PendingApproval.from_dict(data) if data else None

    def find_all(self) -> list[PendingApproval]:
        """Find all approvals."""
        items = self._backend.read_all()
        return [PendingApproval.from_dict(item) for item in items]

    def find_pending(self) -> list[PendingApproval]:
        """Find all pending approvals (not expired, not approved, etc.)."""
        all_approvals = self.find_all()
        pending = []
        for approval in all_approvals:
            if approval.status == ApprovalStatus.PENDING:
                if not approval.is_expired:
                    pending.append(approval)
        return pending

    def find_by_status(self, status: ApprovalStatus) -> list[PendingApproval]:
        """Find approvals by status."""
        return [a for a in self.find_all() if a.status == status]

    def update(self, approval: PendingApproval) -> None:
        """Update an existing approval."""
        if not self._backend.update_by_key("id", approval.id, approval.to_dict()):
            raise ValueError(f"Approval not found: {approval.id}")

    def delete(self, approval_id: str) -> bool:
        """Delete an approval by ID. Returns True if deleted."""
        return self._backend.delete_by_key("id", approval_id)

    def delete_by_task_id(self, task_id: str) -> int:
        """Delete all approvals for a task. Returns count deleted."""
        items = self._backend.read_all()
        original_len = len(items)
        items = [item for item in items if item.get("task_id") != task_id]
        deleted = original_len - len(items)
        if deleted > 0:
            self._backend.write_all(items)
        return deleted

    def cleanup_expired(self) -> int:
        """Mark expired approvals and return count of newly expired.

        This checks all pending approvals and marks them as expired if past timeout.
        """
        expired_count = 0
        pending = self.find_pending()

        for approval in pending:
            if approval.is_expired:
                approval.mark_expired()
                self.update(approval)
                expired_count += 1

        return expired_count

    def cleanup_old(self, days: int = 30) -> int:
        """Remove completed/cancelled/expired approvals older than days.

        Returns count of removed approvals.
        """
        cutoff = datetime.now()
        from datetime import timedelta

        cutoff = cutoff - timedelta(days=days)

        items = self._backend.read_all()
        original_len = len(items)

        # Keep items that are either:
        # 1. Still pending (not completed/cancelled/expired)
        # 2. Newer than cutoff
        terminal_statuses = {
            ApprovalStatus.COMPLETED.value,
            ApprovalStatus.CANCELLED.value,
            ApprovalStatus.EXPIRED.value,
            ApprovalStatus.FAILED.value,
        }

        kept_items = []
        for item in items:
            status = item.get("status", "")
            created_at = item.get("created_at", "")

            if status not in terminal_statuses:
                # Keep pending/approved/executing items
                kept_items.append(item)
            elif created_at:
                # Keep terminal items newer than cutoff
                try:
                    created = datetime.fromisoformat(created_at)
                    if created >= cutoff:
                        kept_items.append(item)
                except ValueError:
                    # Invalid date, keep it
                    kept_items.append(item)
            else:
                # No date, keep it
                kept_items.append(item)

        removed = original_len - len(kept_items)
        if removed > 0:
            self._backend.write_all(kept_items)

        return removed

    def find_pending_for_message(
        self, provider: str, chat_id: str, message_id: int | str
    ) -> PendingApproval | None:
        """Find pending approval by message reference.

        Used to match callback buttons to their approval.
        """
        for approval in self.find_pending():
            for msg_ref in approval.channel_messages:
                if (
                    msg_ref.provider == provider
                    and str(msg_ref.chat_id) == str(chat_id)
                    and str(msg_ref.message_id) == str(message_id)
                ):
                    return approval
        return None
