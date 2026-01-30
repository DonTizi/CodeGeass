"""Event emission for execution tracking."""

import logging
import threading
from collections.abc import Callable

from codegeass.execution.events import ExecutionEvent

logger = logging.getLogger(__name__)

EventCallback = Callable[[ExecutionEvent], None]


class EventEmitter:
    """Handles event emission to registered callbacks."""

    def __init__(self) -> None:
        """Initialize the event emitter."""
        self._callbacks: list[EventCallback] = []
        self._lock = threading.RLock()

    def register(self, callback: EventCallback) -> Callable[[], None]:
        """Register an event callback.

        Returns a function to unregister the callback.
        """
        with self._lock:
            self._callbacks.append(callback)

        def unregister() -> None:
            with self._lock:
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        return unregister

    def emit(self, event: ExecutionEvent) -> None:
        """Emit an event to all registered callbacks."""
        with self._lock:
            callbacks = list(self._callbacks)

        logger.info(f"Emitting event {event.type.value} to {len(callbacks)} callbacks")

        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
