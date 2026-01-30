"""WebSocket connection manager for real-time execution monitoring."""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time execution updates.

    Thread-safe manager that handles:
    - Multiple concurrent WebSocket connections
    - Broadcasting events to all connected clients
    - Filtering events by task ID for targeted streams
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # All active connections (for broadcast)
        self._connections: list[WebSocket] = []
        # Task-specific connections (task_id -> list of websockets)
        self._task_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str | None = None) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
            task_id: Optional task ID for filtered updates
        """
        await websocket.accept()

        async with self._lock:
            self._connections.append(websocket)
            if task_id:
                if task_id not in self._task_connections:
                    self._task_connections[task_id] = []
                self._task_connections[task_id].append(websocket)

        logger.info(f"WebSocket connected (task_id={task_id}, total={len(self._connections)})")

    async def disconnect(self, websocket: WebSocket, task_id: str | None = None) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            task_id: Optional task ID for filtered updates
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
            if task_id and task_id in self._task_connections:
                if websocket in self._task_connections[task_id]:
                    self._task_connections[task_id].remove(websocket)
                if not self._task_connections[task_id]:
                    del self._task_connections[task_id]

        logger.info(f"WebSocket disconnected (task_id={task_id}, total={len(self._connections)})")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast (will be JSON encoded)
        """
        data = json.dumps(message)

        async with self._lock:
            connections = list(self._connections)

        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self._connections:
                        self._connections.remove(conn)

    async def send_to_task(self, task_id: str, message: dict[str, Any]) -> None:
        """Send a message to clients subscribed to a specific task.

        Args:
            task_id: The task ID to send to
            message: The message to send (will be JSON encoded)
        """
        async with self._lock:
            task_connections = self._task_connections.get(task_id, [])
            connections = list(task_connections)

        if not connections:
            return

        data = json.dumps(message)
        disconnected: list[WebSocket] = []

        for connection in connections:
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send to task WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if task_id in self._task_connections:
                        if conn in self._task_connections[task_id]:
                            self._task_connections[task_id].remove(conn)
                    if conn in self._connections:
                        self._connections.remove(conn)

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


# Global connection manager instance
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global ConnectionManager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
