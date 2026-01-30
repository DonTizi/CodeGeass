"""Approvals API router for plan mode."""

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_approval_service
from ..models import (
    Approval,
    ApprovalAction,
    ApprovalActionResult,
    ApprovalStats,
    ApprovalSummary,
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalSummary])
async def list_approvals(
    pending_only: bool = Query(False, description="Only return pending approvals"),
):
    """List all plan approvals."""
    service = get_approval_service()
    return service.list_approvals(pending_only=pending_only)


@router.get("/stats", response_model=ApprovalStats)
async def get_approval_stats():
    """Get approval statistics."""
    service = get_approval_service()
    return service.get_stats()


@router.get("/{approval_id}", response_model=Approval)
async def get_approval(approval_id: str):
    """Get a specific approval by ID."""
    service = get_approval_service()
    approval = service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.get("/task/{task_id}", response_model=Approval)
async def get_approval_by_task(task_id: str):
    """Get approval by task ID."""
    service = get_approval_service()
    approval = service.get_approval_by_task(task_id)
    if not approval:
        raise HTTPException(status_code=404, detail="No approval found for this task")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalActionResult)
async def approve_plan(approval_id: str):
    """Approve a pending plan and execute it."""
    service = get_approval_service()
    result = await service.approve(approval_id)
    if not result.success:
        # Still return the result, let client handle the error
        pass
    return result


@router.post("/{approval_id}/discuss", response_model=ApprovalActionResult)
async def discuss_plan(approval_id: str, action: ApprovalAction):
    """Provide feedback on a plan for iterative refinement."""
    service = get_approval_service()
    result = await service.discuss(approval_id, action.feedback)
    return result


@router.post("/{approval_id}/cancel", response_model=ApprovalActionResult)
async def cancel_plan(approval_id: str):
    """Cancel a pending plan."""
    service = get_approval_service()
    result = await service.cancel(approval_id)
    return result


@router.delete("/{approval_id}")
async def delete_approval(approval_id: str):
    """Delete an approval (admin action)."""
    service = get_approval_service()
    if not service.delete(approval_id):
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"status": "success", "message": f"Approval {approval_id} deleted"}


@router.post("/cleanup/expired")
async def cleanup_expired():
    """Mark expired approvals."""
    service = get_approval_service()
    count = service.cleanup_expired()
    return {"status": "success", "expired_count": count}


@router.post("/cleanup/old")
async def cleanup_old(days: int = Query(30, ge=1, le=365)):
    """Remove old completed/cancelled approvals."""
    service = get_approval_service()
    count = service.cleanup_old(days)
    return {"status": "success", "removed_count": count}
