"""Logs API router."""

from fastapi import APIRouter, HTTPException, Query

from models import ExecutionResult, ExecutionStatus, LogStats, LogFilter
from dependencies import get_log_service

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get(
    "",
    response_model=list[ExecutionResult],
    summary="List execution logs",
    description="Retrieve execution logs with optional filtering by status, task, and date range.",
)
async def list_logs(
    status: ExecutionStatus | None = None,
    task_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(100, ge=1, le=1000, description="Maximum results (1-1000)"),
    offset: int = Query(0, ge=0, description="Skip this many results for pagination"),
):
    """List execution logs with optional filtering.

    Args:
        status: Filter by execution status (success, failure, etc.).
        task_id: Filter by specific task.
        start_date: Filter logs after this date (ISO format).
        end_date: Filter logs before this date (ISO format).
        limit: Maximum number of results (1-1000).
        offset: Number of results to skip for pagination.

    Returns:
        List of ExecutionResult matching the filters.
    """
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


@router.get(
    "/task/{task_id}",
    response_model=list[ExecutionResult],
    summary="Get logs for a task",
    description="Retrieve execution logs for a specific task, ordered by most recent first.",
)
async def get_task_logs(
    task_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum results (1-100)"),
):
    """Get logs for a specific task.

    Args:
        task_id: The unique task identifier.
        limit: Maximum number of logs to return (1-100).

    Returns:
        List of ExecutionResult for the task, newest first.
    """
    service = get_log_service()
    return service.get_task_logs(task_id, limit=limit)


@router.get(
    "/task/{task_id}/latest",
    response_model=ExecutionResult,
    summary="Get latest log for a task",
    description="Retrieve the most recent execution log for a specific task.",
    responses={404: {"description": "No logs found for task"}},
)
async def get_latest_task_log(task_id: str):
    """Get the latest execution log for a task.

    Args:
        task_id: The unique task identifier.

    Returns:
        The most recent ExecutionResult for the task.

    Raises:
        HTTPException: 404 if no logs exist for the task.
    """
    service = get_log_service()
    log = service.get_latest_log(task_id)
    if not log:
        raise HTTPException(status_code=404, detail="No logs found for task")
    return log


@router.get(
    "/stats",
    response_model=LogStats,
    summary="Get log statistics",
    description="Retrieve overall execution statistics across all tasks.",
)
async def get_log_stats():
    """Get overall execution statistics.

    Returns:
        LogStats with total runs, success/failure counts, and timing metrics.
    """
    service = get_log_service()
    return service.get_overall_stats()


@router.delete(
    "/task/{task_id}",
    summary="Clear logs for a task",
    description="Delete all execution logs for a specific task. This action is irreversible.",
    responses={404: {"description": "Task not found or no logs to clear"}},
)
async def clear_task_logs(task_id: str):
    """Clear all logs for a specific task.

    Args:
        task_id: The unique task identifier.

    Returns:
        Success message confirming logs were cleared.

    Raises:
        HTTPException: 404 if task not found or no logs exist.
    """
    service = get_log_service()
    if not service.clear_task_logs(task_id):
        raise HTTPException(status_code=404, detail="Task not found or no logs to clear")
    return {"status": "success", "message": f"Logs for task {task_id} cleared"}
