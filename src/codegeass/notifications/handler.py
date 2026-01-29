"""Notification handler for scheduler integration."""

import asyncio
import logging
from typing import TYPE_CHECKING

from codegeass.notifications.models import NotificationConfig, NotificationEvent
from codegeass.notifications.service import NotificationService

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult
    from codegeass.scheduling.scheduler import Scheduler

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handler that connects the Scheduler to the NotificationService.

    This class provides callback methods that the Scheduler calls
    when task events occur. It determines the appropriate notification
    event type and delegates to the NotificationService.
    """

    def __init__(self, service: NotificationService):
        self._service = service
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop for async operations."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create one
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
            return self._loop

    def _run_async(self, coro) -> None:
        """Run an async coroutine from sync context."""
        try:
            loop = asyncio.get_running_loop()
            # Already in async context, create task
            asyncio.create_task(coro)
        except RuntimeError:
            # No running loop, run in new loop
            loop = self._get_event_loop()
            try:
                loop.run_until_complete(coro)
            except Exception as e:
                logger.error(f"Error running notification async task: {e}")

    def on_task_start(self, task: "Task") -> None:
        """Callback called when a task starts execution.

        Args:
            task: The task being started
        """
        print(f"[Notifications] Task starting: {task.name}")

        # Check if task has notifications configured
        if not task.notifications:
            print(f"[Notifications] No notifications configured for {task.name}")
            return

        async def _notify():
            try:
                result = await self._service.notify(
                    event=NotificationEvent.TASK_START,
                    task=task,
                    result=None,
                )
                print(f"[Notifications] Start notification result: {result}")
            except Exception as e:
                print(f"[Notifications] Failed to send start notification: {e}")

        self._run_async(_notify())

    def on_task_complete(self, task: "Task", result: "ExecutionResult") -> None:
        """Callback called when a task completes execution.

        Args:
            task: The task that completed
            result: The execution result
        """
        print(f"[Notifications] Task completed: {task.name}, status={result.status}")

        # Check if task has notifications configured
        if not task.notifications:
            print(f"[Notifications] No notifications configured for {task.name}")
            return

        # Determine specific event based on status
        event = NotificationEvent.TASK_COMPLETE
        if result.is_success:
            event = NotificationEvent.TASK_SUCCESS
        else:
            event = NotificationEvent.TASK_FAILURE

        async def _notify():
            try:
                notify_result = await self._service.notify(
                    event=event,
                    task=task,
                    result=result,
                )
                print(f"[Notifications] Completion notification result: {notify_result}")
            except Exception as e:
                print(f"[Notifications] Failed to send completion notification: {e}")

        self._run_async(_notify())

    def register_with_scheduler(self, scheduler: "Scheduler") -> None:
        """Register this handler's callbacks with a Scheduler.

        Args:
            scheduler: The scheduler to register with
        """
        scheduler.set_callbacks(
            on_start=self.on_task_start,
            on_complete=self.on_task_complete,
        )
        print("[Notifications] Handler registered with scheduler")


def create_notification_handler(service: NotificationService) -> NotificationHandler:
    """Create a notification handler.

    Args:
        service: The notification service to use

    Returns:
        NotificationHandler instance
    """
    return NotificationHandler(service)
