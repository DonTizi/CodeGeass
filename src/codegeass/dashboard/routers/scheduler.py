"""Scheduler API router."""

from fastapi import APIRouter, Query

from ..dependencies import get_scheduler_service
from ..models import ExecutionResult, SchedulerStatus, UpcomingRun

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """Get scheduler status."""
    service = get_scheduler_service()
    return service.get_status()


@router.get("/upcoming", response_model=list[UpcomingRun])
async def get_upcoming_runs(
    hours: int = Query(24, ge=1, le=168, description="Hours to look ahead"),
):
    """Get upcoming scheduled runs."""
    service = get_scheduler_service()
    return service.get_upcoming_runs(hours=hours)


@router.post("/run-due", response_model=list[ExecutionResult])
async def run_due_tasks(
    window_seconds: int = Query(60, ge=30, le=3600),
    dry_run: bool = Query(False, description="Simulate execution"),
):
    """Run all due tasks."""
    service = get_scheduler_service()
    return service.run_due_tasks(window_seconds=window_seconds, dry_run=dry_run)


@router.get("/due")
async def get_due_tasks(
    window_seconds: int = Query(60, ge=30, le=3600),
):
    """Get tasks that are currently due for execution."""
    service = get_scheduler_service()
    return service.get_due_tasks(window_seconds=window_seconds)
