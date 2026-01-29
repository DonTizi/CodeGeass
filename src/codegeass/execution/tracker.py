"""Execution tracker for real-time monitoring of active executions."""

import json
import logging
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal

from codegeass.execution.events import ExecutionEvent, ExecutionEventType

logger = logging.getLogger(__name__)


@dataclass
class ActiveExecution:
    """Represents an active execution being tracked.

    Contains state and metadata for a running task execution.
    """

    execution_id: str
    task_id: str
    task_name: str
    session_id: str | None
    started_at: datetime
    status: Literal["starting", "running", "finishing"] = "starting"
    output_lines: list[str] = field(default_factory=list)
    current_phase: str = "initializing"

    # Buffer for output lines (keep last 1000)
    _max_output_lines: int = 1000

    def append_output(self, line: str) -> None:
        """Append output line to buffer, keeping only the last N lines."""
        self.output_lines.append(line)
        if len(self.output_lines) > self._max_output_lines:
            self.output_lines = self.output_lines[-self._max_output_lines:]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
            "output_lines": self.output_lines[-20:],  # Only serialize last 20 lines
            "current_phase": self.current_phase,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActiveExecution":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            task_id=data["task_id"],
            task_name=data["task_name"],
            session_id=data.get("session_id"),
            started_at=datetime.fromisoformat(data["started_at"]),
            status=data.get("status", "running"),
            output_lines=data.get("output_lines", []),
            current_phase=data.get("current_phase", "unknown"),
        )


# Type for event callbacks
EventCallback = Callable[[ExecutionEvent], None]


class ExecutionTracker:
    """Singleton tracker for active executions.

    Thread-safe tracking of all active Claude Code executions.
    Emits events for real-time monitoring via WebSocket.

    Persists active executions to a file for crash recovery.
    """

    _instance: "ExecutionTracker | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ExecutionTracker":
        """Singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the tracker.

        Args:
            data_dir: Directory for persistence file
        """
        # Only initialize once
        if getattr(self, "_initialized", False):
            return

        self._active: dict[str, ActiveExecution] = {}
        self._callbacks: list[EventCallback] = []
        self._data_lock = threading.RLock()

        # Persistence file for crash recovery
        self._data_dir = data_dir or Path.cwd() / "data"
        self._persistence_file = self._data_dir / "active_executions.json"

        # Load any previously active executions (for crash recovery)
        self._load_active()

        self._initialized = True

    def _load_active(self) -> None:
        """Load active executions from persistence file."""
        if not self._persistence_file.exists():
            return

        try:
            with open(self._persistence_file) as f:
                data = json.load(f)

            for exec_data in data.get("executions", []):
                execution = ActiveExecution.from_dict(exec_data)
                self._active[execution.execution_id] = execution
                logger.info(f"Recovered active execution: {execution.execution_id}")

        except Exception as e:
            logger.warning(f"Failed to load active executions: {e}")

    def _save_active(self) -> None:
        """Persist active executions to file."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "executions": [ex.to_dict() for ex in self._active.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self._persistence_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save active executions: {e}")

    def on_event(self, callback: EventCallback) -> Callable[[], None]:
        """Register an event callback.

        Args:
            callback: Function to call with each event

        Returns:
            Function to unregister the callback
        """
        with self._data_lock:
            self._callbacks.append(callback)

        def unregister() -> None:
            with self._data_lock:
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        return unregister

    def _emit(self, event: ExecutionEvent) -> None:
        """Emit an event to all registered callbacks."""
        with self._data_lock:
            callbacks = list(self._callbacks)

        logger.info(f"Emitting event {event.type.value} to {len(callbacks)} callbacks")

        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def start_execution(
        self,
        task_id: str,
        task_name: str,
        session_id: str | None = None,
    ) -> str:
        """Start tracking a new execution.

        Args:
            task_id: The task being executed
            task_name: Human-readable task name
            session_id: Optional session ID

        Returns:
            The generated execution_id
        """
        execution_id = str(uuid.uuid4())[:12]

        execution = ActiveExecution(
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            session_id=session_id,
            started_at=datetime.now(),
            status="starting",
        )

        with self._data_lock:
            self._active[execution_id] = execution
            self._save_active()

        # Emit STARTED event
        event = ExecutionEvent.started(
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            session_id=session_id,
        )
        self._emit(event)

        logger.info(f"Started tracking execution {execution_id} for task {task_name}")
        print(f"[Tracker] Started execution {execution_id} for {task_name}")
        return execution_id

    def update_execution(
        self,
        execution_id: str,
        status: Literal["starting", "running", "finishing"] | None = None,
        phase: str | None = None,
    ) -> None:
        """Update execution status or phase.

        Args:
            execution_id: The execution to update
            status: New status
            phase: New phase description
        """
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return

            if status:
                execution.status = status
            if phase:
                execution.current_phase = phase

            self._save_active()

        # Emit PROGRESS event
        if phase:
            event = ExecutionEvent.progress(
                execution_id=execution_id,
                task_id=execution.task_id,
                task_name=execution.task_name,
                phase=phase,
            )
            self._emit(event)

    def append_output(self, execution_id: str, line: str) -> None:
        """Append output line to an execution.

        Args:
            execution_id: The execution to update
            line: Output line to append
        """
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                return

            execution.append_output(line)

        # Emit OUTPUT event
        event = ExecutionEvent.output(
            execution_id=execution_id,
            task_id=execution.task_id,
            task_name=execution.task_name,
            line=line,
        )
        self._emit(event)

    def finish_execution(
        self,
        execution_id: str,
        success: bool,
        exit_code: int | None = None,
        error: str | None = None,
    ) -> None:
        """Mark an execution as finished.

        Args:
            execution_id: The execution to finish
            success: Whether execution succeeded
            exit_code: Process exit code
            error: Error message if failed
        """
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return

            # Calculate duration
            duration = (datetime.now() - execution.started_at).total_seconds()

            # Remove from active
            del self._active[execution_id]
            self._save_active()

        # Emit completion event
        if success:
            event = ExecutionEvent.completed(
                execution_id=execution_id,
                task_id=execution.task_id,
                task_name=execution.task_name,
                exit_code=exit_code or 0,
                duration_seconds=duration,
            )
        else:
            event = ExecutionEvent.failed(
                execution_id=execution_id,
                task_id=execution.task_id,
                task_name=execution.task_name,
                error=error or "Unknown error",
                exit_code=exit_code,
            )

        self._emit(event)
        logger.info(f"Finished execution {execution_id} (success={success})")

    def get_active(self) -> list[ActiveExecution]:
        """Get all active executions.

        Returns:
            List of active executions
        """
        with self._data_lock:
            return list(self._active.values())

    def get_execution(self, execution_id: str) -> ActiveExecution | None:
        """Get a specific execution by ID.

        Args:
            execution_id: The execution ID

        Returns:
            The execution or None if not found
        """
        with self._data_lock:
            return self._active.get(execution_id)

    def get_by_task(self, task_id: str) -> ActiveExecution | None:
        """Get active execution for a task.

        Args:
            task_id: The task ID

        Returns:
            The active execution for this task, or None
        """
        with self._data_lock:
            for execution in self._active.values():
                if execution.task_id == task_id:
                    return execution
        return None

    def clear_all(self) -> None:
        """Clear all active executions (for testing)."""
        with self._data_lock:
            self._active.clear()
            if self._persistence_file.exists():
                self._persistence_file.unlink()


# Global accessor function
def get_execution_tracker(data_dir: Path | None = None) -> ExecutionTracker:
    """Get the global ExecutionTracker instance.

    Args:
        data_dir: Data directory for persistence

    Returns:
        The singleton ExecutionTracker instance
    """
    return ExecutionTracker(data_dir)
