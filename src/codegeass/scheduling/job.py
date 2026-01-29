"""Job abstraction for scheduled task execution."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.executor import ClaudeExecutor


class Job(ABC):
    """Abstract base class for scheduled jobs.

    Implements Template Method pattern for job execution lifecycle.
    """

    def __init__(self, task: Task):
        """Initialize job with task."""
        self.task = task
        self._metadata: dict[str, Any] = {}

    def run(self) -> ExecutionResult:
        """Run the job through its lifecycle.

        Template method that defines the execution sequence.
        """
        self._prepare()
        try:
            result = self._execute()
            self._on_success(result)
        except Exception as e:
            result = self._on_error(e)
        finally:
            self._cleanup(result)

        return result

    def _prepare(self) -> None:
        """Prepare for execution. Override for custom preparation."""
        self._metadata["started_at"] = datetime.now().isoformat()

    @abstractmethod
    def _execute(self) -> ExecutionResult:
        """Execute the job. Must be implemented by subclasses."""
        ...

    def _on_success(self, result: ExecutionResult) -> None:
        """Called on successful execution. Override for custom handling."""
        self._metadata["completed_at"] = datetime.now().isoformat()
        self._metadata["status"] = "success"

    def _on_error(self, error: Exception) -> ExecutionResult:
        """Handle execution error. Returns failure result."""
        self._metadata["completed_at"] = datetime.now().isoformat()
        self._metadata["status"] = "failure"
        self._metadata["error"] = str(error)

        return ExecutionResult(
            task_id=self.task.id,
            session_id=None,
            status=ExecutionStatus.FAILURE,
            output="",
            started_at=datetime.fromisoformat(self._metadata["started_at"]),
            finished_at=datetime.now(),
            error=str(error),
        )

    def _cleanup(self, result: ExecutionResult) -> None:
        """Cleanup after execution. Override for custom cleanup."""
        pass


class TaskJob(Job):
    """Job implementation for executing Task entities via ClaudeExecutor."""

    def __init__(self, task: Task, executor: ClaudeExecutor):
        """Initialize with task and executor."""
        super().__init__(task)
        self._executor = executor

    def _execute(self) -> ExecutionResult:
        """Execute the task using ClaudeExecutor."""
        return self._executor.execute(self.task)

    def _prepare(self) -> None:
        """Prepare for execution - validate task."""
        super()._prepare()

        # Validate task is enabled
        if not self.task.enabled:
            raise ValueError(f"Task {self.task.name} is disabled")

        # Validate working directory exists
        if not self.task.working_dir.exists():
            raise ValueError(f"Working directory does not exist: {self.task.working_dir}")


class DryRunJob(Job):
    """Job that only shows what would be executed without actually running."""

    def __init__(self, task: Task, executor: ClaudeExecutor):
        """Initialize with task and executor."""
        super().__init__(task)
        self._executor = executor

    def _execute(self) -> ExecutionResult:
        """Get command without executing."""
        command = self._executor.get_command(self.task)
        return ExecutionResult(
            task_id=self.task.id,
            session_id=None,
            status=ExecutionStatus.SKIPPED,
            output=f"Would execute: {' '.join(command)}",
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
