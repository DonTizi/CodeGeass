"""Notification handler for scheduler integration."""

import logging
from typing import TYPE_CHECKING, Coroutine, Any

from codegeass.notifications.models import NotificationConfig, NotificationEvent
from codegeass.notifications.service import NotificationService

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult
    from codegeass.scheduling.scheduler import Scheduler

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handler that connects the Scheduler to the NotificationService.

    This class provides async callback methods that the Scheduler calls
    when task events occur. The Scheduler handles running the async callbacks
    properly whether in sync or async context.
    """

    def __init__(self, service: NotificationService):
        self._service = service

    async def on_task_start(self, task: "Task") -> None:
        """Async callback called when a task starts execution.

        Args:
            task: The task being started
        """
        print(f"[Notifications] Task starting: {task.name}")

        # Check if task has notifications configured
        if not task.notifications:
            print(f"[Notifications] No notifications configured for {task.name}")
            return

        try:
            result = await self._service.notify(
                event=NotificationEvent.TASK_START,
                task=task,
                result=None,
            )
            print(f"[Notifications] Start notification result: {result}")
        except Exception as e:
            print(f"[Notifications] Failed to send start notification: {e}")
            logger.error(f"Failed to send start notification: {e}")

    async def on_task_complete(self, task: "Task", result: "ExecutionResult") -> None:
        """Async callback called when a task completes execution.

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

        try:
            notify_result = await self._service.notify(
                event=event,
                task=task,
                result=result,
            )
            print(f"[Notifications] Completion notification result: {notify_result}")
        except Exception as e:
            print(f"[Notifications] Failed to send completion notification: {e}")
            logger.error(f"Failed to send completion notification: {e}")

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
