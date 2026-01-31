"""Scheduler API router."""

from fastapi import APIRouter, HTTPException, Query

from models import SchedulerStatus, UpcomingRun, ExecutionResult
from dependencies import get_scheduler_service

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get(
    "/status",
    response_model=SchedulerStatus,
    summary="Get scheduler status",
    description="Retrieve the current scheduler state including enabled tasks and next run times.",
)
async def get_scheduler_status():
    """Get the current scheduler status.

    Returns:
        SchedulerStatus with active task count, next scheduled run, and system info.
    """
    service = get_scheduler_service()
    return service.get_status()


@router.get(
    "/upcoming",
    response_model=list[UpcomingRun],
    summary="Get upcoming scheduled runs",
    description="List tasks scheduled to run within the specified time window.",
)
async def get_upcoming_runs(
    hours: int = Query(24, ge=1, le=168, description="Hours to look ahead (1-168)"),
):
    """Get upcoming scheduled task runs.

    Args:
        hours: Number of hours to look ahead (1-168, default 24).

    Returns:
        List of UpcomingRun with task info and scheduled time.
    """
    service = get_scheduler_service()
    return service.get_upcoming_runs(hours=hours)


@router.post(
    "/run-due",
    response_model=list[ExecutionResult],
    summary="Run all due tasks",
    description="Execute all tasks that are currently due within the time window.",
)
async def run_due_tasks(
    window_seconds: int = Query(60, ge=30, le=3600, description="Time window in seconds (30-3600)"),
    dry_run: bool = Query(False, description="Simulate execution without running"),
):
    """Run all tasks that are currently due for execution.

    Args:
        window_seconds: Time window for considering tasks due (30-3600 seconds).
        dry_run: If True, simulates without actual execution.

    Returns:
        List of ExecutionResult for each task that was run.
    """
    service = get_scheduler_service()
    return service.run_due_tasks(window_seconds=window_seconds, dry_run=dry_run)


@router.get(
    "/due",
    summary="Get due tasks",
    description="List tasks that are currently due for execution without running them.",
)
async def get_due_tasks(
    window_seconds: int = Query(60, ge=30, le=3600, description="Time window in seconds (30-3600)"),
):
    """Get tasks that are currently due for execution.

    Args:
        window_seconds: Time window for considering tasks due (30-3600 seconds).

    Returns:
        List of tasks that are within the due window.
    """
    service = get_scheduler_service()
    return service.get_due_tasks(window_seconds=window_seconds)
