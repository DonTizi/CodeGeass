"""Task API router."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_scheduler_service, get_task_service
from ..models import ExecutionResult, Task, TaskCreate, TaskStats, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Thread pool for running blocking tasks
_executor = ThreadPoolExecutor(max_workers=4)


@router.get("", response_model=list[Task])
async def list_tasks(
    summary_only: bool = Query(False, description="Return only summary fields"),
):
    """List all tasks."""
    service = get_task_service()
    if summary_only:
        return service.list_task_summaries()
    return service.list_tasks()


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a task by ID."""
    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=Task, status_code=201)
async def create_task(data: TaskCreate):
    """Create a new task."""
    service = get_task_service()
    try:
        return service.create_task(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, data: TaskUpdate):
    """Update a task."""
    service = get_task_service()
    try:
        task = service.update_task(task_id, data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    service = get_task_service()
    if not service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} deleted"}


@router.post("/{task_id}/enable")
async def enable_task(task_id: str):
    """Enable a task."""
    service = get_task_service()
    if not service.enable_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} enabled"}


@router.post("/{task_id}/disable")
async def disable_task(task_id: str):
    """Disable a task."""
    service = get_task_service()
    if not service.disable_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task {task_id} disabled"}


@router.post("/{task_id}/run", response_model=ExecutionResult)
async def run_task(
    task_id: str,
    dry_run: bool = Query(False, description="Simulate execution without running"),
):
    """Run a task manually.

    Uses a thread pool to avoid blocking the async event loop,
    allowing real-time execution events to be broadcast via WebSocket.
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


@router.get("/{task_id}/stats", response_model=TaskStats)
async def get_task_stats(task_id: str):
    """Get execution statistics for a task."""
    service = get_task_service()
    stats = service.get_task_stats(task_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Task not found")
    return stats


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """Stop a running task execution.

    Kills the process running the task and marks the execution as stopped.
    """
    from codegeass.execution.tracker import get_execution_tracker

    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the execution tracker
    from ..config import get_data_dir
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
