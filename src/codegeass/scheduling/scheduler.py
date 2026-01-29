"""Main scheduler for managing and executing due tasks."""

from datetime import datetime
from pathlib import Path
from typing import Callable

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.executor import ClaudeExecutor
from codegeass.execution.session import SessionManager
from codegeass.factory.registry import SkillRegistry
from codegeass.scheduling.cron_parser import CronParser
from codegeass.scheduling.job import DryRunJob, TaskJob
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.task_repository import TaskRepository


class Scheduler:
    """Main scheduler for executing due tasks.

    Responsible for:
    - Finding tasks due for execution
    - Managing execution concurrency
    - Coordinating with executor
    - Tracking execution history
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        skill_registry: SkillRegistry,
        session_manager: SessionManager,
        log_repository: LogRepository,
        max_concurrent: int = 1,
    ):
        """Initialize scheduler with dependencies."""
        self._task_repo = task_repository
        self._skill_registry = skill_registry
        self._session_manager = session_manager
        self._log_repo = log_repository
        self._max_concurrent = max_concurrent

        # Create executor
        self._executor = ClaudeExecutor(
            skill_registry=skill_registry,
            session_manager=session_manager,
            log_repository=log_repository,
        )

        # Callbacks
        self._on_task_start: Callable[[Task], None] | None = None
        self._on_task_complete: Callable[[Task, ExecutionResult], None] | None = None

    def set_callbacks(
        self,
        on_start: Callable[[Task], None] | None = None,
        on_complete: Callable[[Task, ExecutionResult], None] | None = None,
    ) -> None:
        """Set execution callbacks."""
        self._on_task_start = on_start
        self._on_task_complete = on_complete

    def find_due_tasks(self, window_seconds: int = 60) -> list[Task]:
        """Find tasks due for execution."""
        return self._task_repo.find_due(window_seconds)

    def run_task(self, task: Task, dry_run: bool = False) -> ExecutionResult:
        """Run a single task."""
        if self._on_task_start:
            self._on_task_start(task)

        if dry_run:
            job = DryRunJob(task, self._executor)
        else:
            job = TaskJob(task, self._executor)

        result = job.run()

        # Update task state in repository
        task.update_last_run(result.status.value)
        self._task_repo.update(task)

        if self._on_task_complete:
            self._on_task_complete(task, result)

        return result

    def run_due(self, window_seconds: int = 60, dry_run: bool = False) -> list[ExecutionResult]:
        """Run all tasks due for execution.

        Args:
            window_seconds: Time window to check for due tasks
            dry_run: If True, only show what would run

        Returns:
            List of execution results
        """
        due_tasks = self.find_due_tasks(window_seconds)
        results = []

        for task in due_tasks:
            result = self.run_task(task, dry_run=dry_run)
            results.append(result)

        return results

    def run_all(self, dry_run: bool = False) -> list[ExecutionResult]:
        """Run all enabled tasks regardless of schedule.

        Args:
            dry_run: If True, only show what would run

        Returns:
            List of execution results
        """
        tasks = self._task_repo.find_enabled()
        results = []

        for task in tasks:
            result = self.run_task(task, dry_run=dry_run)
            results.append(result)

        return results

    def run_by_name(self, name: str, dry_run: bool = False) -> ExecutionResult | None:
        """Run a task by name.

        Args:
            name: Task name
            dry_run: If True, only show what would run

        Returns:
            Execution result or None if task not found
        """
        task = self._task_repo.find_by_name(name)
        if not task:
            return None

        return self.run_task(task, dry_run=dry_run)

    def status(self) -> dict:
        """Get scheduler status.

        Returns dict with:
        - enabled_tasks: Count of enabled tasks
        - disabled_tasks: Count of disabled tasks
        - due_tasks: List of currently due task names
        - next_runs: Dict of task names to next run times
        """
        all_tasks = self._task_repo.find_all()
        enabled = [t for t in all_tasks if t.enabled]
        disabled = [t for t in all_tasks if not t.enabled]
        due = self.find_due_tasks()

        next_runs = {}
        for task in enabled:
            next_time = CronParser.get_next(task.schedule)
            next_runs[task.name] = next_time.isoformat()

        return {
            "enabled_tasks": len(enabled),
            "disabled_tasks": len(disabled),
            "due_tasks": [t.name for t in due],
            "next_runs": next_runs,
            "current_time": datetime.now().isoformat(),
        }

    def get_upcoming(self, hours: int = 24) -> list[dict]:
        """Get tasks scheduled to run in the next N hours.

        Returns list of dicts with task name and scheduled time.
        """
        from datetime import timedelta

        tasks = self._task_repo.find_enabled()
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)

        upcoming = []
        for task in tasks:
            next_runs = CronParser.get_next_n(task.schedule, 10, now)
            for run_time in next_runs:
                if run_time <= cutoff:
                    upcoming.append(
                        {
                            "task_name": task.name,
                            "task_id": task.id,
                            "scheduled_at": run_time.isoformat(),
                            "schedule": task.schedule,
                            "schedule_desc": CronParser.describe(task.schedule),
                        }
                    )

        # Sort by scheduled time
        upcoming.sort(key=lambda x: x["scheduled_at"])
        return upcoming

    def generate_crontab_entry(self, runner_script: Path) -> str:
        """Generate crontab entry for the scheduler.

        Args:
            runner_script: Path to cron-runner.sh

        Returns:
            Crontab entry string
        """
        # Check every 15 minutes
        return f"*/15 * * * * {runner_script}"

    def install_crontab(self, runner_script: Path) -> bool:
        """Install crontab entry for scheduler.

        Args:
            runner_script: Path to cron-runner.sh

        Returns:
            True if successful
        """
        import subprocess

        entry = self.generate_crontab_entry(runner_script)

        # Get current crontab
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            current = result.stdout if result.returncode == 0 else ""
        except FileNotFoundError:
            current = ""

        # Check if entry already exists
        if str(runner_script) in current:
            return True  # Already installed

        # Add new entry
        new_crontab = current.rstrip() + "\n" + entry + "\n"

        # Install
        process = subprocess.Popen(
            ["crontab", "-"], stdin=subprocess.PIPE, text=True
        )
        process.communicate(input=new_crontab)

        return process.returncode == 0
