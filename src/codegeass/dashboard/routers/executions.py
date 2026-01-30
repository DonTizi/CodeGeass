"""Executions router for real-time monitoring API."""

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.execution_service import get_execution_manager
from ..websocket import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("")
async def list_active_executions() -> list[dict[str, Any]]:
    """Get all currently active executions.

    Returns a list of executions that are currently running or starting.
    """
    manager = get_execution_manager()
    return manager.get_active_executions()


@router.get("/{execution_id}")
async def get_execution(execution_id: str) -> dict[str, Any] | None:
    """Get details of a specific execution.

    Args:
        execution_id: The execution ID to look up

    Returns:
        Execution details or None if not found
    """
    manager = get_execution_manager()
    return manager.get_execution(execution_id)


@router.get("/task/{task_id}")
async def get_execution_by_task(task_id: str) -> dict[str, Any] | None:
    """Get the active execution for a specific task.

    Args:
        task_id: The task ID to look up

    Returns:
        Active execution for this task or None if not running
    """
    manager = get_execution_manager()
    return manager.get_by_task(task_id)


@router.websocket("/ws")
async def websocket_all_executions(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming all execution events.

    Clients receive real-time updates for all running executions.
    Events are JSON-encoded and include:
    - execution.started
    - execution.output
    - execution.progress
    - execution.completed
    - execution.failed
    """
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive, handle any incoming messages
            try:
                data = await websocket.receive_text()
                # Could handle ping/pong or other client messages here
                logger.debug(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                break
    finally:
        await connection_manager.disconnect(websocket)


@router.websocket("/ws/{task_id}")
async def websocket_task_executions(websocket: WebSocket, task_id: str) -> None:
    """WebSocket endpoint for streaming execution events for a specific task.

    Clients receive real-time updates only for the specified task.

    Args:
        task_id: The task ID to subscribe to
    """
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, task_id=task_id)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message for task {task_id}: {data}")
            except WebSocketDisconnect:
                break
    finally:
        await connection_manager.disconnect(websocket, task_id=task_id)
