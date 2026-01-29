"""Repository protocol definitions (interfaces)."""

from typing import Protocol

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult


class TaskRepositoryProtocol(Protocol):
    """Interface for task persistence."""

    def save(self, task: Task) -> None:
        """Save a task."""
        ...

    def find_by_id(self, task_id: str) -> Task | None:
        """Find task by ID."""
        ...

    def find_by_name(self, name: str) -> Task | None:
        """Find task by name."""
        ...

    def find_all(self) -> list[Task]:
        """Find all tasks."""
        ...

    def find_enabled(self) -> list[Task]:
        """Find all enabled tasks."""
        ...

    def find_due(self, window_seconds: int = 60) -> list[Task]:
        """Find tasks due for execution."""
        ...

    def delete(self, task_id: str) -> bool:
        """Delete a task. Returns True if deleted."""
        ...

    def update(self, task: Task) -> None:
        """Update an existing task."""
        ...


class LogRepositoryProtocol(Protocol):
    """Interface for execution log persistence."""

    def save(self, result: ExecutionResult) -> None:
        """Save an execution result."""
        ...

    def find_by_task_id(self, task_id: str, limit: int = 10) -> list[ExecutionResult]:
        """Find execution results for a task."""
        ...

    def find_latest(self, task_id: str) -> ExecutionResult | None:
        """Find the latest execution result for a task."""
        ...

    def find_all(self, limit: int = 100) -> list[ExecutionResult]:
        """Find all execution results, most recent first."""
        ...

    def find_by_status(self, status: str, limit: int = 100) -> list[ExecutionResult]:
        """Find execution results by status."""
        ...
