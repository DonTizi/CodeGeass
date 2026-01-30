"""Task service wrapping TaskRepository."""

from pathlib import Path

from codegeass.core.entities import Task as CoreTask
from codegeass.scheduling.cron_parser import CronParser
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.task_repository import TaskRepository

from ..models import Task, TaskCreate, TaskNotificationConfig, TaskStats, TaskSummary, TaskUpdate


class TaskService:
    """Service for managing tasks."""

    def __init__(self, task_repo: TaskRepository, log_repo: LogRepository):
        self.task_repo = task_repo
        self.log_repo = log_repo

    def _core_to_api(self, task: CoreTask) -> Task:
        """Convert core Task to API Task model."""
        # Calculate next run
        next_run = None
        schedule_description = None
        try:
            next_dt = CronParser.get_next(task.schedule)
            next_run = next_dt.isoformat() if next_dt else None
            schedule_description = CronParser.describe(task.schedule)
        except Exception:
            pass

        # Convert notifications
        notifications = None
        if task.notifications:
            notifications = TaskNotificationConfig(
                channels=task.notifications.get("channels", []),
                events=task.notifications.get("events", []),
                include_output=task.notifications.get("include_output", False),
            )

        return Task(
            id=task.id,
            name=task.name,
            schedule=task.schedule,
            working_dir=str(task.working_dir),
            skill=task.skill,
            prompt=task.prompt,
            allowed_tools=task.allowed_tools or [],
            model=task.model,
            autonomous=task.autonomous,
            max_turns=task.max_turns,
            timeout=task.timeout,
            enabled=task.enabled,
            variables=task.variables or {},
            notifications=notifications,
            last_run=task.last_run,
            last_status=task.last_status,
            plan_mode=task.plan_mode,
            plan_timeout=task.plan_timeout,
            plan_max_iterations=task.plan_max_iterations,
            next_run=next_run,
            schedule_description=schedule_description,
        )

    def _api_to_core(self, task_create: TaskCreate) -> CoreTask:
        """Convert API TaskCreate to core Task."""
        # Convert notifications to dict format expected by core
        notifications = None
        if task_create.notifications:
            notifications = {
                "channels": task_create.notifications.channels,
                "events": task_create.notifications.events,
                "include_output": task_create.notifications.include_output,
            }

        # Use Task.create() to get a proper generated ID
        return CoreTask.create(
            name=task_create.name,
            schedule=task_create.schedule,
            working_dir=Path(task_create.working_dir),
            skill=task_create.skill,
            prompt=task_create.prompt,
            allowed_tools=task_create.allowed_tools,
            model=task_create.model,
            autonomous=task_create.autonomous,
            max_turns=task_create.max_turns,
            timeout=task_create.timeout,
            enabled=task_create.enabled,
            variables=task_create.variables,
            notifications=notifications,
            plan_mode=task_create.plan_mode,
            plan_timeout=task_create.plan_timeout,
            plan_max_iterations=task_create.plan_max_iterations,
        )

    def list_tasks(self) -> list[Task]:
        """Get all tasks."""
        tasks = self.task_repo.find_all()
        return [self._core_to_api(t) for t in tasks]

    def list_task_summaries(self) -> list[TaskSummary]:
        """Get task summaries (lighter weight)."""
        tasks = self.task_repo.find_all()
        summaries = []
        for task in tasks:
            next_run = None
            try:
                next_dt = CronParser.get_next(task.schedule)
                next_run = next_dt.isoformat() if next_dt else None
            except Exception:
                pass

            summaries.append(TaskSummary(
                id=task.id,
                name=task.name,
                schedule=task.schedule,
                skill=task.skill,
                enabled=task.enabled,
                last_run=task.last_run,
                last_status=task.last_status,
                next_run=next_run,
            ))
        return summaries

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        task = self.task_repo.find_by_id(task_id)
        if task:
            return self._core_to_api(task)
        return None

    def get_task_by_name(self, name: str) -> Task | None:
        """Get a task by name."""
        task = self.task_repo.find_by_name(name)
        if task:
            return self._core_to_api(task)
        return None

    def create_task(self, data: TaskCreate) -> Task:
        """Create a new task."""
        # Validate CRON expression
        if not CronParser.validate(data.schedule):
            raise ValueError(f"Invalid CRON expression: {data.schedule}")

        # Check for duplicate name
        existing = self.task_repo.find_by_name(data.name)
        if existing:
            raise ValueError(f"Task with name '{data.name}' already exists")

        # Create and save
        core_task = self._api_to_core(data)
        self.task_repo.save(core_task)

        # Refresh to get generated ID
        saved = self.task_repo.find_by_name(data.name)
        if saved:
            return self._core_to_api(saved)
        raise ValueError("Failed to create task")

    def update_task(self, task_id: str, data: TaskUpdate) -> Task | None:
        """Update a task."""
        task = self.task_repo.find_by_id(task_id)
        if not task:
            return None

        # Validate CRON if provided
        if data.schedule and not CronParser.validate(data.schedule):
            raise ValueError(f"Invalid CRON expression: {data.schedule}")

        # Check for name conflict
        if data.name and data.name != task.name:
            existing = self.task_repo.find_by_name(data.name)
            if existing:
                raise ValueError(f"Task with name '{data.name}' already exists")

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if key == "working_dir":
                    setattr(task, key, Path(value))
                elif key == "notifications":
                    # Convert Pydantic model to dict for core
                    if isinstance(value, dict):
                        task.notifications = value
                    else:
                        task.notifications = {
                            "channels": value.get("channels", []),
                            "events": value.get("events", []),
                            "include_output": value.get("include_output", False),
                        }
                else:
                    setattr(task, key, value)

        self.task_repo.update(task)
        return self._core_to_api(task)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        return self.task_repo.delete(task_id)

    def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        return self.task_repo.enable(task_id)

    def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        return self.task_repo.disable(task_id)

    def get_task_stats(self, task_id: str) -> TaskStats | None:
        """Get execution statistics for a task."""
        task = self.task_repo.find_by_id(task_id)
        if not task:
            return None

        stats = self.log_repo.get_task_stats(task_id)
        return TaskStats(
            task_id=task_id,
            total_runs=stats.get("total", 0),
            successful_runs=stats.get("success", 0),
            failed_runs=stats.get("failure", 0),
            timeout_runs=stats.get("timeout", 0),
            success_rate=stats.get("success_rate", 0.0),
            avg_duration_seconds=stats.get("avg_duration", 0.0),
            last_run=task.last_run,
            last_status=task.last_status,
        )
