"""Core executor logic for Claude Code tasks."""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.core.exceptions import ExecutionError
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.executor.context_builder import build_context, build_resume_context
from codegeass.execution.executor.environment import (
    ExecutionEnvironment,
    create_execution_environment,
)
from codegeass.execution.executor.strategy_selector import StrategySelector
from codegeass.execution.executor.validation import (
    validate_provider_capabilities,
    validate_working_dir,
)
from codegeass.execution.session import SessionManager
from codegeass.execution.strategies import ResumeWithFeedbackStrategy
from codegeass.factory.registry import SkillRegistry
from codegeass.providers import get_provider_registry
from codegeass.storage.log_repository import LogRepository

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker

logger = logging.getLogger(__name__)


class ClaudeExecutor:
    """Main executor for Claude Code tasks.

    All tasks are executed in isolated git worktrees to ensure:
    1. Fresh Claude Code sessions (no context pollution)
    2. Parallel task execution without interference
    3. Clean separation between scheduled runs

    Supports multiple code execution providers through the universal provider
    architecture.
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        session_manager: SessionManager,
        log_repository: LogRepository,
        tracker: "ExecutionTracker | None" = None,
    ):
        self._skill_registry = skill_registry
        self._session_manager = session_manager
        self._log_repository = log_repository
        self._tracker = tracker
        self._provider_registry = get_provider_registry()
        self._strategy_selector = StrategySelector(self._provider_registry)

    def execute(
        self,
        task: Task,
        dry_run: bool = False,
        force_plan_mode: bool = False,
    ) -> ExecutionResult:
        """Execute a task in an isolated environment."""
        validate_working_dir(task)
        validate_provider_capabilities(
            task, self._provider_registry, force_plan_mode
        )

        is_plan_mode = force_plan_mode or task.plan_mode
        env = create_execution_environment(task)
        session = self._create_session(task, dry_run, env)

        execution_id = self._start_tracking(task, session.id, dry_run)

        try:
            result = self._execute_task(
                task, env, session.id, execution_id, dry_run, force_plan_mode
            )
            result = self._enrich_plan_mode_result(result, env, execution_id, is_plan_mode)

            task.update_last_run(result.status.value)
            self._complete_session(session.id, result)
            self._log_repository.save(result)
            self._finish_tracking(execution_id, result, is_plan_mode)

            return result

        except Exception as e:
            result = self._handle_execution_error(task, session.id, e)
            self._finish_tracking_error(execution_id, e)
            raise ExecutionError(str(e), task_id=task.id, cause=e) from e

        finally:
            if not is_plan_mode:
                env.cleanup()

    def execute_plan_mode(self, task: Task) -> ExecutionResult:
        """Execute a task in plan mode (read-only planning)."""
        return self.execute(task, dry_run=False, force_plan_mode=True)

    def execute_resume(
        self,
        task: Task,
        session_id: str,
        feedback: str | None = None,
        worktree_path: str | None = None,
    ) -> ExecutionResult:
        """Execute a task by resuming a Claude session."""
        working_dir = self._resolve_resume_working_dir(task, worktree_path)
        validate_working_dir_path(working_dir, task.id)

        exec_session = self._create_resume_session(task, session_id, feedback, worktree_path)

        try:
            context = build_resume_context(task, session_id, feedback or "", worktree_path)
            strategy = self._select_resume_strategy(feedback)

            result = strategy.execute(context)

            task.update_last_run(result.status.value)
            self._complete_session(exec_session.id, result)
            self._log_repository.save(result)

            return result

        except Exception as e:
            result = self._handle_execution_error(task, exec_session.id, e)
            raise ExecutionError(str(e), task_id=task.id, cause=e) from e

    def get_command(self, task: Task) -> list[str]:
        """Get the command that would be executed for a task (for debugging)."""
        env = ExecutionEnvironment(working_dir=task.working_dir)
        context = build_context(task, env, self._skill_registry)
        strategy = self._strategy_selector.select(task)
        return strategy.build_command(context)

    # --- Private methods ---

    def _create_session(self, task: Task, dry_run: bool, env: ExecutionEnvironment):
        """Create a new execution session."""
        return self._session_manager.create_session(
            task_id=task.id,
            metadata={
                "task_name": task.name,
                "dry_run": dry_run,
                "isolated": env.is_isolated,
                "worktree_path": env.worktree_path,
            },
        )

    def _create_resume_session(
        self, task: Task, session_id: str, feedback: str | None, worktree_path: str | None
    ):
        """Create a session for resuming execution."""
        return self._session_manager.create_session(
            task_id=task.id,
            metadata={
                "task_name": task.name,
                "resume_session": session_id,
                "has_feedback": feedback is not None,
                "worktree_path": worktree_path,
            },
        )

    def _start_tracking(self, task: Task, session_id: str, dry_run: bool) -> str | None:
        """Start execution tracking if tracker is available."""
        if self._tracker and not dry_run:
            return self._tracker.start_execution(
                task_id=task.id,
                task_name=task.name,
                session_id=session_id,
            )
        return None

    def _execute_task(
        self,
        task: Task,
        env: ExecutionEnvironment,
        session_id: str,
        execution_id: str | None,
        dry_run: bool,
        force_plan_mode: bool,
    ) -> ExecutionResult:
        """Execute the task and return result."""
        context = build_context(
            task, env, self._skill_registry, session_id, execution_id, self._tracker
        )
        strategy = self._strategy_selector.select(task, force_plan_mode)

        if dry_run:
            command = strategy.build_command(context)
            return ExecutionResult(
                task_id=task.id,
                session_id=session_id,
                status=ExecutionStatus.SKIPPED,
                output=f"Dry run - command: {' '.join(command)}",
                started_at=datetime.now(),
                finished_at=datetime.now(),
            )

        return strategy.execute(context)

    def _enrich_plan_mode_result(
        self,
        result: ExecutionResult,
        env: ExecutionEnvironment,
        execution_id: str | None,
        is_plan_mode: bool,
    ) -> ExecutionResult:
        """Add plan mode metadata to result if applicable."""
        if not is_plan_mode:
            return result

        metadata = result.metadata or {}
        if env.is_isolated:
            metadata["worktree_path"] = env.worktree_path
        if execution_id:
            metadata["execution_id"] = execution_id

        return ExecutionResult(
            task_id=result.task_id,
            session_id=result.session_id,
            status=result.status,
            output=result.output,
            started_at=result.started_at,
            finished_at=result.finished_at,
            error=result.error,
            exit_code=result.exit_code,
            metadata=metadata,
        )

    def _complete_session(self, session_id: str, result: ExecutionResult) -> None:
        """Complete the execution session."""
        self._session_manager.complete_session(
            session_id,
            status=result.status.value,
            output=result.output,
            error=result.error,
        )

    def _finish_tracking(
        self, execution_id: str | None, result: ExecutionResult, is_plan_mode: bool
    ) -> None:
        """Finish execution tracking."""
        if not self._tracker or not execution_id:
            return

        if is_plan_mode and result.is_success:
            logger.info(f"Plan mode execution {execution_id} awaiting approval handler")
            return

        self._tracker.finish_execution(
            execution_id=execution_id,
            success=result.is_success,
            exit_code=result.exit_code,
            error=result.error,
        )

    def _finish_tracking_error(self, execution_id: str | None, error: Exception) -> None:
        """Finish tracking with error."""
        if self._tracker and execution_id:
            self._tracker.finish_execution(
                execution_id=execution_id,
                success=False,
                error=str(error),
            )

    def _handle_execution_error(
        self, task: Task, session_id: str, error: Exception
    ) -> ExecutionResult:
        """Handle execution error and create failure result."""
        result = ExecutionResult(
            task_id=task.id,
            session_id=session_id,
            status=ExecutionStatus.FAILURE,
            output="",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            error=str(error),
        )

        self._session_manager.complete_session(
            session_id,
            status="failure",
            error=str(error),
        )

        self._log_repository.save(result)
        return result

    def _resolve_resume_working_dir(self, task: Task, worktree_path: str | None) -> Path:
        """Resolve working directory for resume execution."""
        if worktree_path:
            working_dir = Path(worktree_path)
            if not working_dir.exists():
                logger.warning(f"Worktree no longer exists: {worktree_path}")
                return task.working_dir
            return working_dir
        return task.working_dir

    def _select_resume_strategy(self, feedback: str | None):
        """Select strategy for resume execution."""
        if feedback:
            return ResumeWithFeedbackStrategy(feedback)
        return self._strategy_selector.resume_approval_strategy


def validate_working_dir_path(working_dir: Path, task_id: str) -> None:
    """Validate that a path exists."""
    if not working_dir.exists():
        raise ExecutionError(
            f"Working directory does not exist: {working_dir}",
            task_id=task_id,
        )
