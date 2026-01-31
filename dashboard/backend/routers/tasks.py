"""Task API router."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query

from models import Task, TaskCreate, TaskUpdate, TaskSummary, TaskStats, ExecutionResult
from dependencies import get_task_service, get_scheduler_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Thread pool for running blocking tasks
_executor = ThreadPoolExecutor(max_workers=4)


@router.get(
    "",
    response_model=list[Task],
    summary="List all tasks",
    description="Retrieve all scheduled tasks. Use summary_only=true for lightweight listing.",
)
async def list_tasks(
    summary_only: bool = Query(False, description="Return only summary fields"),
):
    """List all scheduled tasks.

    Args:
        summary_only: If True, returns only essential fields (id, name, enabled, schedule).

    Returns:
        List of Task objects with full or summary details.
    """
    service = get_task_service()
    if summary_only:
        return service.list_task_summaries()
    return service.list_tasks()


@router.get(
    "/{task_id}",
    response_model=Task,
    summary="Get a task by ID",
    description="Retrieve full details for a specific task including schedule, configuration, and last run info.",
    responses={404: {"description": "Task not found"}},
)
async def get_task(task_id: str):
    """Get a task by its unique identifier.

    Args:
        task_id: The unique task identifier (name or UUID).

    Returns:
        Task object with full configuration details.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "",
    response_model=Task,
    status_code=201,
    summary="Create a new task",
    description="Create a new scheduled task with the provided configuration.",
    responses={400: {"description": "Invalid task configuration or CRON expression"}},
)
async def create_task(data: TaskCreate):
    """Create a new scheduled task.

    Args:
        data: Task creation payload with name, schedule, prompt, and optional settings.

    Returns:
        The newly created Task object.

    Raises:
        HTTPException: 400 if validation fails (invalid CRON, duplicate name, etc.).
    """
    service = get_task_service()
    try:
        return service.create_task(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{task_id}",
    response_model=Task,
    summary="Update a task",
    description="Update an existing task's configuration. Only provided fields are updated.",
    responses={
        400: {"description": "Invalid configuration"},
        404: {"description": "Task not found"},
    },
)
async def update_task(task_id: str, data: TaskUpdate):
    """Update an existing task.

    Args:
        task_id: The unique task identifier.
        data: Partial update payload with fields to modify.

    Returns:
        The updated Task object.

    Raises:
        HTTPException: 400 if validation fails, 404 if task not found.
    """
    service = get_task_service()
    try:
        task = service.update_task(task_id, data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{task_id}",
    summary="Delete a task",
    description="Permanently delete a task and its configuration. Execution logs are preserved.",
    responses={404: {"description": "Task not found"}},
)
async def delete_task(task_id: str):
    """Delete a task permanently.

    Args:
        task_id: The unique task identifier.

    Returns:
        Success message with deleted task ID.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = get_task_service()
    if not service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} deleted"}


@router.post(
    "/{task_id}/enable",
    summary="Enable a task",
    description="Enable a disabled task so it can be scheduled for execution.",
    responses={404: {"description": "Task not found"}},
)
async def enable_task(task_id: str):
    """Enable a disabled task.

    Args:
        task_id: The unique task identifier.

    Returns:
        Success message confirming task is enabled.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = get_task_service()
    if not service.enable_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} enabled"}


@router.post(
    "/{task_id}/disable",
    summary="Disable a task",
    description="Disable a task to prevent it from being scheduled. Does not affect running executions.",
    responses={404: {"description": "Task not found"}},
)
async def disable_task(task_id: str):
    """Disable a task.

    Args:
        task_id: The unique task identifier.

    Returns:
        Success message confirming task is disabled.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = get_task_service()
    if not service.disable_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} disabled"}


@router.post(
    "/{task_id}/run",
    response_model=ExecutionResult,
    summary="Run a task manually",
    description="Execute a task immediately, bypassing its schedule. Use dry_run=true to simulate.",
    responses={404: {"description": "Task not found"}},
)
async def run_task(
    task_id: str,
    dry_run: bool = Query(False, description="Simulate execution without running"),
):
    """Run a task manually, outside of its schedule.

    Uses a thread pool to avoid blocking the async event loop,
    allowing real-time execution events to be broadcast via WebSocket.

    Args:
        task_id: The unique task identifier.
        dry_run: If True, simulates execution without actually running Claude.

    Returns:
        ExecutionResult with status, output, and timing information.

    Raises:
        HTTPException: 404 if task not found.
    """
    scheduler_service = get_scheduler_service()

    # Run in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        lambda: scheduler_service.run_task(task_id, dry_run=dry_run)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.get(
    "/{task_id}/stats",
    response_model=TaskStats,
    summary="Get task execution statistics",
    description="Retrieve execution statistics including success rate, average duration, and run counts.",
    responses={404: {"description": "Task not found"}},
)
async def get_task_stats(task_id: str):
    """Get execution statistics for a task.

    Args:
        task_id: The unique task identifier.

    Returns:
        TaskStats with total runs, success/failure counts, and timing metrics.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = get_task_service()
    stats = service.get_task_stats(task_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Task not found")
    return stats


@router.post(
    "/{task_id}/stop",
    summary="Stop a running task",
    description="Terminate an active task execution. Kills the Claude process and marks execution as stopped.",
    responses={
        404: {"description": "Task not found or no active execution"},
        409: {"description": "Execution already finished"},
    },
)
async def stop_task(task_id: str):
    """Stop a running task execution.

    Kills the process running the task and marks the execution as stopped.

    Args:
        task_id: The unique task identifier.

    Returns:
        Success message with execution ID that was stopped.

    Raises:
        HTTPException: 404 if task or execution not found, 409 if already finished.
    """
    from codegeass.execution.tracker import get_execution_tracker

    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the execution tracker
    from dependencies import get_data_dir
    tracker = get_execution_tracker(get_data_dir())

    # Check if task has an active execution
    execution = tracker.get_by_task(task_id)
    if not execution:
        raise HTTPException(status_code=404, detail="No active execution found for this task")

    # Stop the execution
    stopped = tracker.stop_execution(execution.execution_id)

    if stopped:
        return {
            "status": "success",
            "message": f"Task {task_id} execution stopped",
            "execution_id": execution.execution_id,
        }
    else:
        raise HTTPException(
            status_code=409,
            detail="Could not stop execution (may have already finished)"
        )
