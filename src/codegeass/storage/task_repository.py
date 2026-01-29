"""Task repository implementation using YAML backend."""

from pathlib import Path

from codegeass.core.entities import Task
from codegeass.storage.yaml_backend import YAMLListBackend


class TaskRepository:
    """Repository for task persistence using YAML files."""

    def __init__(self, schedules_file: Path):
        """Initialize with path to schedules.yaml."""
        self._backend = YAMLListBackend(schedules_file, list_key="tasks")

    def save(self, task: Task) -> None:
        """Save a new task or update existing one."""
        existing = self.find_by_id(task.id)
        if existing:
            self.update(task)
        else:
            self._backend.append(task.to_dict())

    def find_by_id(self, task_id: str) -> Task | None:
        """Find task by ID."""
        data = self._backend.find_by_key("id", task_id)
        return Task.from_dict(data) if data else None

    def find_by_name(self, name: str) -> Task | None:
        """Find task by name."""
        data = self._backend.find_by_key("name", name)
        return Task.from_dict(data) if data else None

    def find_all(self) -> list[Task]:
        """Find all tasks."""
        items = self._backend.read_all()
        return [Task.from_dict(item) for item in items]

    def find_enabled(self) -> list[Task]:
        """Find all enabled tasks."""
        return [task for task in self.find_all() if task.enabled]

    def find_due(self, window_seconds: int = 60) -> list[Task]:
        """Find tasks due for execution within the time window."""
        return [task for task in self.find_enabled() if task.is_due(window_seconds)]

    def delete(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted."""
        return self._backend.delete_by_key("id", task_id)

    def delete_by_name(self, name: str) -> bool:
        """Delete a task by name. Returns True if deleted."""
        return self._backend.delete_by_key("name", name)

    def update(self, task: Task) -> None:
        """Update an existing task."""
        if not self._backend.update_by_key("id", task.id, task.to_dict()):
            raise ValueError(f"Task not found: {task.id}")

    def enable(self, task_id: str) -> bool:
        """Enable a task. Returns True if successful."""
        task = self.find_by_id(task_id)
        if task:
            task.enabled = True
            self.update(task)
            return True
        return False

    def disable(self, task_id: str) -> bool:
        """Disable a task. Returns True if successful."""
        task = self.find_by_id(task_id)
        if task:
            task.enabled = False
            self.update(task)
            return True
        return False
