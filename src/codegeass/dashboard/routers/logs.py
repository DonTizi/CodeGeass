"""Logs API router."""

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_log_service
from ..models import ExecutionResult, ExecutionStatus, LogFilter, LogStats

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=list[ExecutionResult])
async def list_logs(
    status: ExecutionStatus | None = None,
    task_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List execution logs with optional filtering."""
    service = get_log_service()
    filter = LogFilter(
        status=status,
        task_id=task_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return service.get_logs(filter)


@router.get("/task/{task_id}", response_model=list[ExecutionResult])
async def get_task_logs(
    task_id: str,
    limit: int = Query(10, ge=1, le=100),
):
    """Get logs for a specific task."""
    service = get_log_service()
    return service.get_task_logs(task_id, limit=limit)


@router.get("/task/{task_id}/latest", response_model=ExecutionResult)
async def get_latest_task_log(task_id: str):
    """Get the latest log for a task."""
    service = get_log_service()
    log = service.get_latest_log(task_id)
    if not log:
        raise HTTPException(status_code=404, detail="No logs found for task")
    return log


@router.get("/stats", response_model=LogStats)
async def get_log_stats():
    """Get overall log statistics."""
    service = get_log_service()
    return service.get_overall_stats()


@router.delete("/task/{task_id}")
async def clear_task_logs(task_id: str):
    """Clear logs for a specific task."""
    service = get_log_service()
    if not service.clear_task_logs(task_id):
        raise HTTPException(status_code=404, detail="Task not found or no logs to clear")
    return {"status": "success", "message": f"Logs for task {task_id} cleared"}
