"""Execution service for real-time monitoring of task executions."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from codegeass.execution.events import ExecutionEvent
from codegeass.execution.tracker import ExecutionTracker, get_execution_tracker

from ..config import settings
from ..websocket import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Service for managing execution monitoring.

    Bridges the core ExecutionTracker with the WebSocket ConnectionManager
    to provide real-time execution updates to dashboard clients.
    """

    def __init__(
        self,
        tracker: ExecutionTracker,
        connection_manager: ConnectionManager,
    ) -> None:
        """Initialize the execution manager.

        Args:
            tracker: The execution tracker singleton
            connection_manager: The WebSocket connection manager
        """
        self._tracker = tracker
        self._connection_manager = connection_manager
        self._event_queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue()
        self._running = False
        self._unregister_callback: Callable[[], None] | None = None

    def start(self) -> None:
        """Start listening to execution events."""
        if self._running:
            return

        # Register callback with tracker
        def on_event(event: ExecutionEvent) -> None:
            # Queue event for async processing
            try:
                self._event_queue.put_nowait(event)
                print(f"[Execution Monitor] Event queued: {event.type.value} for {event.task_name}")
            except asyncio.QueueFull:
                logger.warning("Event queue full, dropping event")

        self._unregister_callback = self._tracker.on_event(on_event)
        self._running = True
        logger.info("ExecutionManager started listening to events")

    def stop(self) -> None:
        """Stop listening to execution events."""
        if self._unregister_callback:
            self._unregister_callback()
            self._unregister_callback = None
        self._running = False
        logger.info("ExecutionManager stopped")

    async def broadcast_loop(self) -> None:
        """Continuously broadcast events to WebSocket clients.

        This should be run as an asyncio task.
        """
        logger.info("Starting execution broadcast loop")
        self.start()

        while self._running:
            try:
                # Wait for next event with timeout
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(), timeout=1.0
                    )
                except TimeoutError:
                    continue

                # Convert event to dict for JSON serialization
                event_data = event.to_dict()

                conn_count = self._connection_manager.connection_count
                print(f"[Execution Monitor] Broadcasting: {event.type.value} to {conn_count}")

                # Broadcast to all clients
                await self._connection_manager.broadcast(event_data)

                # Also send to task-specific clients
                await self._connection_manager.send_to_task(
                    event.task_id, event_data
                )

                logger.debug(f"Broadcasted event: {event.type.value}")

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(0.1)

        logger.info("Broadcast loop stopped")

    def get_active_executions(self) -> list[dict[str, Any]]:
        """Get all currently active executions.

        Returns:
            List of active executions as dictionaries
        """
        executions = self._tracker.get_active()
        return [ex.to_dict() for ex in executions]

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        """Get a specific execution by ID.

        Args:
            execution_id: The execution ID

        Returns:
            The execution as a dictionary, or None
        """
        execution = self._tracker.get_execution(execution_id)
        return execution.to_dict() if execution else None

    def get_by_task(self, task_id: str) -> dict[str, Any] | None:
        """Get active execution for a task.

        Args:
            task_id: The task ID

        Returns:
            The active execution as a dictionary, or None
        """
        execution = self._tracker.get_by_task(task_id)
        return execution.to_dict() if execution else None


# Global execution manager instance
_execution_manager: ExecutionManager | None = None


def get_execution_manager() -> ExecutionManager:
    """Get or create the global ExecutionManager instance."""
    global _execution_manager
    if _execution_manager is None:
        tracker = get_execution_tracker(settings.data_dir)
        connection_manager = get_connection_manager()
        _execution_manager = ExecutionManager(tracker, connection_manager)
    return _execution_manager
