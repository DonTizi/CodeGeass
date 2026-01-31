"""Main scheduler for managing and executing due tasks."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.core.value_objects import ExecutionResult
from codegeass.execution.executor import ClaudeExecutor
from codegeass.execution.session import SessionManager
from codegeass.factory.registry import SkillRegistry
from codegeass.scheduling.cron_parser import CronParser
from codegeass.scheduling.job import DryRunJob, TaskJob
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.task_repository import TaskRepository

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker

# Type for callbacks that can be sync or async
StartCallback = Callable[[Task], None | Awaitable[None]]
CompleteCallback = Callable[[Task, ExecutionResult], None | Awaitable[None]]
PlanApprovalCallback = Callable[[Task, ExecutionResult], None | Awaitable[None]]


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
        tracker: "ExecutionTracker | None" = None,
    ):
        """Initialize scheduler with dependencies.

        Args:
            task_repository: Repository for task storage
            skill_registry: Registry for loading skills
            session_manager: Manager for execution sessions
            log_repository: Repository for storing execution logs
            max_concurrent: Maximum concurrent executions (default 1)
            tracker: Optional execution tracker for real-time monitoring
        """
        self._task_repo = task_repository
        self._skill_registry = skill_registry
        self._session_manager = session_manager
        self._log_repo = log_repository
        self._max_concurrent = max_concurrent

        # Create executor with optional tracker
        self._executor = ClaudeExecutor(
            skill_registry=skill_registry,
            session_manager=session_manager,
            log_repository=log_repository,
            tracker=tracker,
        )

        # Callbacks (can be sync or async)
        self._on_task_start: StartCallback | None = None
        self._on_task_complete: CompleteCallback | None = None
        self._on_plan_approval: PlanApprovalCallback | None = None

    def set_callbacks(
        self,
        on_start: StartCallback | None = None,
        on_complete: CompleteCallback | None = None,
        on_plan_approval: PlanApprovalCallback | None = None,
    ) -> None:
        """Set execution callbacks.

        Args:
            on_start: Called when a task starts execution
            on_complete: Called when a task completes (success or failure)
            on_plan_approval: Called when a plan mode task needs approval
        """
        self._on_task_start = on_start
        self._on_task_complete = on_complete
        self._on_plan_approval = on_plan_approval

    def _run_callback(self, callback_result) -> None:
        """Run a callback result, handling async if needed.

        Ensures async callbacks complete before returning, which is critical
        for notification message editing (message_id must be stored before
        the completion notification is sent).
        """
        if asyncio.iscoroutine(callback_result):
            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                # Already in async context, run in a new thread with its own loop
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, callback_result)
                    future.result(timeout=30)  # Wait for completion
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                asyncio.run(callback_result)

    def find_due_tasks(self, window_seconds: int = 60) -> list[Task]:
        """Find tasks due for execution."""
        return self._task_repo.find_due(window_seconds)

    def run_task(self, task: Task, dry_run: bool = False) -> ExecutionResult:
        """Run a single task.

        For tasks with plan_mode=True:
        - Executes in plan mode (read-only)
        - Calls on_plan_approval callback instead of on_complete
        - Returns the plan result (not the final execution)

        Args:
            task: The task to run
            dry_run: If True, only show what would run

        Returns:
            ExecutionResult from execution or plan mode
        """
        if self._on_task_start:
            result = self._on_task_start(task)
            self._run_callback(result)

        if dry_run:
            job = DryRunJob(task, self._executor)
            result = job.run()
        elif task.plan_mode:
            # Plan mode: execute read-only planning, then trigger approval
            result = self._run_plan_mode_task(task)
        else:
            job = TaskJob(task, self._executor)
            result = job.run()

        # Update task state in repository
        task.update_last_run(result.status.value)
        self._task_repo.update(task)

        # For plan mode tasks, call on_plan_approval instead of on_complete
        if task.plan_mode and not dry_run:
            if self._on_plan_approval:
                callback_result = self._on_plan_approval(task, result)
                self._run_callback(callback_result)
        else:
            if self._on_task_complete:
                callback_result = self._on_task_complete(task, result)
                self._run_callback(callback_result)

        return result

    def _run_plan_mode_task(self, task: Task) -> ExecutionResult:
        """Run a task in plan mode.

        The executor handles worktree isolation automatically.
        For plan mode tasks, the worktree is preserved until approval/cancel.

        Args:
            task: The task to run in plan mode

        Returns:
            ExecutionResult containing the plan and worktree_path in metadata
        """
        return self._executor.execute_plan_mode(task)

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

    def _is_scheduler_running(self) -> bool:
        """Check if scheduler is running (launchd, systemd, or cron)."""
        import platform
        import subprocess

        system = platform.system()
        home = Path.home()

        # macOS: Check launchd
        if system == "Darwin":
            plist_path = home / "Library" / "LaunchAgents" / "com.codegeass.scheduler.plist"
            if plist_path.exists():
                try:
                    result = subprocess.run(
                        ["launchctl", "list"],
                        capture_output=True,
                        text=True,
                    )
                    if "com.codegeass.scheduler" in result.stdout:
                        return True
                except Exception:
                    pass

        # Linux: Check systemd
        elif system == "Linux":
            try:
                result = subprocess.run(
                    ["systemctl", "--user", "is-active", "codegeass-scheduler.timer"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass

        # Fallback: Check cron
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0 and "codegeass" in result.stdout:
                return True
        except Exception:
            pass

        return False

    def status(self) -> dict:
        """Get scheduler status.

        Returns dict with:
        - running: Whether the scheduler cron job is installed
        - enabled_tasks: Count of enabled tasks
        - disabled_tasks: Count of disabled tasks
        - plan_mode_tasks: Count of tasks with plan_mode enabled
        - due_tasks: List of currently due task names
        - next_runs: Dict of task names to next run times
        """
        all_tasks = self._task_repo.find_all()
        enabled = [t for t in all_tasks if t.enabled]
        disabled = [t for t in all_tasks if not t.enabled]
        plan_mode = [t for t in all_tasks if t.plan_mode]
        due = self.find_due_tasks()

        next_runs = {}
        for task in enabled:
            next_time = CronParser.get_next(task.schedule)
            next_runs[task.name] = next_time.isoformat()

        # Check if scheduler is running (launchd, systemd, or cron)
        running = self._is_scheduler_running()

        return {
            "running": running,
            "enabled_tasks": len(enabled),
            "disabled_tasks": len(disabled),
            "plan_mode_tasks": len(plan_mode),
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
        process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)

        return process.returncode == 0
