"""Core execution tracker singleton."""

import logging
import os
import signal
import threading
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from codegeass.execution.events import ExecutionEvent
from codegeass.execution.tracker.event_emitter import EventCallback, EventEmitter
from codegeass.execution.tracker.execution import ActiveExecution
from codegeass.execution.tracker.persistence import ExecutionPersistence

logger = logging.getLogger(__name__)


class ExecutionTracker:
    """Singleton tracker for active executions.

    Thread-safe tracking of all active Claude Code executions.
    Emits events for real-time monitoring via WebSocket.
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
        """Initialize the tracker."""
        if getattr(self, "_initialized", False):
            return

        self._active: dict[str, ActiveExecution] = {}
        self._emitter = EventEmitter()
        self._data_lock = threading.RLock()
        self._persistence = ExecutionPersistence(data_dir or Path.cwd() / "data")
        self._active = self._persistence.load()
        self._initialized = True

    def on_event(self, callback: EventCallback) -> Callable[[], None]:
        """Register an event callback."""
        return self._emitter.register(callback)

    def start_execution(
        self,
        task_id: str,
        task_name: str,
        session_id: str | None = None,
    ) -> str:
        """Start tracking a new execution. Returns execution_id."""
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
            self._persistence.save(self._active)

        event = ExecutionEvent.started(
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            session_id=session_id,
        )
        self._emitter.emit(event)

        logger.info(f"Started tracking execution {execution_id} for task {task_name}")
        print(f"[Tracker] Started execution {execution_id} for {task_name}")
        return execution_id

    def update_execution(
        self,
        execution_id: str,
        status: Literal["starting", "running", "finishing"] | None = None,
        phase: str | None = None,
    ) -> None:
        """Update execution status or phase."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return

            if status:
                execution.status = status
            if phase:
                execution.current_phase = phase

            self._persistence.save(self._active)

        if phase:
            event = ExecutionEvent.progress(
                execution_id=execution_id,
                task_id=execution.task_id,
                task_name=execution.task_name,
                phase=phase,
            )
            self._emitter.emit(event)

    def append_output(self, execution_id: str, line: str) -> None:
        """Append output line to an execution."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                return
            execution.append_output(line)

        event = ExecutionEvent.output(
            execution_id=execution_id,
            task_id=execution.task_id,
            task_name=execution.task_name,
            line=line,
        )
        self._emitter.emit(event)

    def set_pid(self, execution_id: str, pid: int) -> None:
        """Set the process ID for an execution."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found when setting PID")
                return
            execution.pid = pid
            self._persistence.save(self._active)
        logger.info(f"Set PID {pid} for execution {execution_id}")

    def stop_execution(self, execution_id: str) -> bool:
        """Stop a running execution by killing its process."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return False

            if execution.status in ("finishing", "stopped"):
                logger.info(f"Execution {execution_id} already finishing/stopped")
                return False

            pid = execution.pid
            task_id = execution.task_id
            task_name = execution.task_name

        if not pid:
            logger.warning(f"No PID found for execution {execution_id}")
            self._mark_stopped(execution_id, task_id, task_name, "No process to stop")
            return True

        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid} for execution {execution_id}")
            time.sleep(0.5)

            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
                logger.info(f"Sent SIGKILL to PID {pid}")
            except OSError:
                pass

        except OSError as e:
            logger.warning(f"Failed to kill PID {pid}: {e}")

        self._mark_stopped(execution_id, task_id, task_name, "Stopped by user")
        return True

    def _mark_stopped(
        self, execution_id: str, task_id: str, task_name: str, reason: str
    ) -> None:
        """Mark an execution as stopped and emit event."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if execution:
                duration = (datetime.now() - execution.started_at).total_seconds()
                del self._active[execution_id]
                self._persistence.save(self._active)
            else:
                duration = 0.0

        event = ExecutionEvent.stopped(
            execution_id=execution_id,
            task_id=task_id,
            task_name=task_name,
            reason=reason,
            duration_seconds=duration,
        )
        self._emitter.emit(event)
        logger.info(f"Execution {execution_id} marked as stopped: {reason}")

    def stop_by_task(self, task_id: str) -> bool:
        """Stop any active execution for a task."""
        execution = self.get_by_task(task_id)
        if not execution:
            logger.info(f"No active execution found for task {task_id}")
            return False
        return self.stop_execution(execution.execution_id)

    def finish_execution(
        self,
        execution_id: str,
        success: bool,
        exit_code: int | None = None,
        error: str | None = None,
    ) -> None:
        """Mark an execution as finished."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return

            duration = (datetime.now() - execution.started_at).total_seconds()
            del self._active[execution_id]
            self._persistence.save(self._active)

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

        self._emitter.emit(event)
        logger.info(f"Finished execution {execution_id} (success={success})")

    def set_waiting_approval(
        self,
        execution_id: str,
        approval_id: str,
        plan_text: str | None = None,
    ) -> None:
        """Set execution to waiting_approval state for plan mode tasks."""
        with self._data_lock:
            execution = self._active.get(execution_id)
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return

            execution.status = "waiting_approval"
            execution.approval_id = approval_id
            execution.current_phase = "waiting for approval"
            self._persistence.save(self._active)

        event = ExecutionEvent.waiting_approval(
            execution_id=execution_id,
            task_id=execution.task_id,
            task_name=execution.task_name,
            approval_id=approval_id,
            plan_text=plan_text,
        )
        self._emitter.emit(event)
        logger.info(f"Execution {execution_id} waiting for approval: {approval_id}")

    def get_by_approval(self, approval_id: str) -> ActiveExecution | None:
        """Get execution by approval ID."""
        with self._data_lock:
            for execution in self._active.values():
                if execution.approval_id == approval_id:
                    return execution
        return None

    def get_active(self) -> list[ActiveExecution]:
        """Get all active executions."""
        with self._data_lock:
            return list(self._active.values())

    def get_execution(self, execution_id: str) -> ActiveExecution | None:
        """Get a specific execution by ID."""
        with self._data_lock:
            return self._active.get(execution_id)

    def get_by_task(self, task_id: str) -> ActiveExecution | None:
        """Get active execution for a task."""
        with self._data_lock:
            for execution in self._active.values():
                if execution.task_id == task_id:
                    return execution
        return None

    def clear_all(self) -> None:
        """Clear all active executions (for testing)."""
        with self._data_lock:
            self._active.clear()
            self._persistence.clear()

    def cleanup_stale_executions(self, valid_approval_ids: set[str] | None = None) -> int:
        """Clean up stale executions waiting for expired approvals."""
        removed = 0
        with self._data_lock:
            to_remove = []
            for exec_id, execution in self._active.items():
                if execution.status == "waiting_approval":
                    if valid_approval_ids is None:
                        to_remove.append(exec_id)
                    elif execution.approval_id and execution.approval_id not in valid_approval_ids:
                        to_remove.append(exec_id)
                        logger.info(
                            f"Removing stale execution {exec_id} "
                            f"(approval {execution.approval_id} stale)"
                        )

            for exec_id in to_remove:
                del self._active[exec_id]
                removed += 1

            if removed > 0:
                self._persistence.save(self._active)

        return removed


def get_execution_tracker(data_dir: Path | None = None) -> ExecutionTracker:
    """Get the global ExecutionTracker instance."""
    return ExecutionTracker(data_dir)
