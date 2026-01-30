"""Scheduler service wrapping Scheduler."""

from typing import Any

from codegeass.core.value_objects import ExecutionResult as CoreResult
from codegeass.scheduling.scheduler import Scheduler
from codegeass.storage.task_repository import TaskRepository

from ..models import ExecutionResult, ExecutionStatus, SchedulerStatus, UpcomingRun


class SchedulerService:
    """Service for scheduler operations."""

    def __init__(self, scheduler: Scheduler, task_repo: TaskRepository):
        self.scheduler = scheduler
        self.task_repo = task_repo

    def _core_to_api_result(
        self, result: CoreResult, task_name: str | None = None
    ) -> ExecutionResult:
        """Convert core ExecutionResult to API model."""
        return ExecutionResult(
            task_id=result.task_id,
            task_name=task_name,
            session_id=result.session_id,
            status=ExecutionStatus(result.status.value),
            output=result.output,
            clean_output=result.clean_output,
            error=result.error,
            exit_code=result.exit_code,
            started_at=result.started_at.isoformat(),
            finished_at=result.finished_at.isoformat() if result.finished_at else None,
            duration_seconds=result.duration_seconds,
        )

    def get_status(self) -> SchedulerStatus:
        """Get scheduler status."""
        status_data = self.scheduler.status()
        tasks = self.task_repo.find_all()
        enabled_tasks = [t for t in tasks if t.enabled]
        due_tasks = self.scheduler.find_due_tasks(window_seconds=60)

        return SchedulerStatus(
            running=status_data.get("running", False),
            check_interval=status_data.get("check_interval", 60),
            max_concurrent=status_data.get("max_concurrent", 1),
            total_tasks=len(tasks),
            enabled_tasks=len(enabled_tasks),
            due_tasks=len(due_tasks),
            last_check=status_data.get("last_check"),
            next_check=status_data.get("next_check"),
        )

    def get_upcoming_runs(self, hours: int = 24) -> list[UpcomingRun]:
        """Get upcoming scheduled runs."""
        upcoming_data = self.scheduler.get_upcoming(hours=hours)
        upcoming = []

        for item in upcoming_data:
            task = self.task_repo.find_by_id(item["task_id"])
            if task:
                upcoming.append(UpcomingRun(
                    task_id=task.id,
                    task_name=task.name,
                    schedule=task.schedule,
                    next_run=item["scheduled_at"],
                    skill=task.skill,
                    enabled=task.enabled,
                ))

        return upcoming

    def run_due_tasks(
        self, window_seconds: int = 60, dry_run: bool = False
    ) -> list[ExecutionResult]:
        """Run all due tasks."""
        results = self.scheduler.run_due(window_seconds=window_seconds, dry_run=dry_run)

        api_results = []
        for result in results:
            task = self.task_repo.find_by_id(result.task_id)
            task_name = task.name if task else None
            api_results.append(self._core_to_api_result(result, task_name))

        return api_results

    def run_task(self, task_id: str, dry_run: bool = False) -> ExecutionResult | None:
        """Run a specific task manually."""
        task = self.task_repo.find_by_id(task_id)
        if not task:
            return None

        result = self.scheduler.run_task(task, dry_run=dry_run)
        return self._core_to_api_result(result, task.name)

    def run_task_by_name(self, name: str, dry_run: bool = False) -> ExecutionResult | None:
        """Run a task by name."""
        result = self.scheduler.run_by_name(name, dry_run=dry_run)
        if result:
            task = self.task_repo.find_by_id(result.task_id)
            task_name = task.name if task else None
            return self._core_to_api_result(result, task_name)
        return None

    def get_due_tasks(self, window_seconds: int = 60) -> list[dict[str, Any]]:
        """Get tasks that are due for execution."""
        due = self.scheduler.find_due_tasks(window_seconds=window_seconds)
        return [
            {
                "id": task.id,
                "name": task.name,
                "schedule": task.schedule,
                "skill": task.skill,
            }
            for task in due
        ]
