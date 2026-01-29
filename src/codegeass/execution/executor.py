"""Main executor for Claude Code tasks.

All tasks are executed in isolated git worktrees to ensure fresh Claude Code
sessions without context pollution from other conversations.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Task
from codegeass.core.exceptions import ExecutionError, SkillNotFoundError
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.session import SessionManager
from codegeass.execution.strategies import (
    AutonomousStrategy,
    ExecutionContext,
    ExecutionStrategy,
    HeadlessStrategy,
    PlanModeStrategy,
    ResumeWithApprovalStrategy,
    ResumeWithFeedbackStrategy,
    SkillStrategy,
)
from codegeass.execution.worktree import WorktreeInfo, WorktreeManager
from codegeass.factory.registry import SkillRegistry
from codegeass.storage.log_repository import LogRepository

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEnvironment:
    """Environment for task execution, potentially in an isolated worktree."""

    working_dir: Path
    worktree_info: WorktreeInfo | None = None

    @property
    def is_isolated(self) -> bool:
        """Check if execution is in an isolated worktree."""
        return self.worktree_info is not None

    @property
    def worktree_path(self) -> str | None:
        """Get the worktree path if isolated."""
        return str(self.worktree_info.path) if self.worktree_info else None

    def cleanup(self) -> None:
        """Cleanup the worktree if one was created."""
        if self.worktree_info:
            try:
                self.worktree_info.cleanup()
                logger.info(f"Cleaned up worktree: {self.worktree_info.path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree: {e}")


class ClaudeExecutor:
    """Main executor for Claude Code tasks.

    All tasks are executed in isolated git worktrees to ensure:
    1. Fresh Claude Code sessions (no context pollution)
    2. Parallel task execution without interference
    3. Clean separation between scheduled runs

    For plan mode tasks, the worktree is preserved until approval/cancel.
    For other tasks, the worktree is cleaned up after execution.
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        session_manager: SessionManager,
        log_repository: LogRepository,
        tracker: "ExecutionTracker | None" = None,
    ):
        """Initialize executor with dependencies.

        Args:
            skill_registry: Registry for loading skills
            session_manager: Manager for execution sessions
            log_repository: Repository for storing execution logs
            tracker: Optional execution tracker for real-time monitoring
        """
        self._skill_registry = skill_registry
        self._session_manager = session_manager
        self._log_repository = log_repository
        self._tracker = tracker

        # Strategy instances
        self._headless = HeadlessStrategy()
        self._autonomous = AutonomousStrategy()
        self._skill_strategy = SkillStrategy()
        self._plan_mode = PlanModeStrategy()
        self._resume_approval = ResumeWithApprovalStrategy()

    def _create_execution_environment(self, task: Task) -> ExecutionEnvironment:
        """Create an isolated execution environment for a task.

        Attempts to create a git worktree for isolation. If the project
        is not a git repo or worktree creation fails, falls back to
        using the original working directory.

        Args:
            task: The task to create environment for

        Returns:
            ExecutionEnvironment with working directory and optional worktree info
        """
        # Try to create an isolated worktree
        worktree_info = WorktreeManager.create_worktree(
            project_dir=task.working_dir,
            task_id=task.id,
        )

        if worktree_info:
            logger.info(f"Created isolated worktree for {task.name}: {worktree_info.path}")
            return ExecutionEnvironment(
                working_dir=worktree_info.path,
                worktree_info=worktree_info,
            )
        else:
            logger.debug(f"Using original directory for {task.name}: {task.working_dir}")
            return ExecutionEnvironment(
                working_dir=task.working_dir,
                worktree_info=None,
            )

    def _select_strategy(self, task: Task, force_plan_mode: bool = False) -> ExecutionStrategy:
        """Select appropriate execution strategy based on task configuration.

        Args:
            task: The task to select strategy for
            force_plan_mode: If True, use plan mode regardless of task.plan_mode

        Returns:
            The appropriate execution strategy
        """
        # Plan mode takes precedence when enabled
        if force_plan_mode or task.plan_mode:
            return self._plan_mode

        if task.skill:
            return self._skill_strategy
        elif task.autonomous:
            return self._autonomous
        else:
            return self._headless

    def _build_context(
        self,
        task: Task,
        env: ExecutionEnvironment,
        session_id: str | None = None,
        execution_id: str | None = None,
    ) -> ExecutionContext:
        """Build execution context for a task.

        Args:
            task: The task to build context for
            env: The execution environment (with worktree if isolated)
            session_id: Optional session ID
            execution_id: Optional execution ID for real-time tracking

        Returns:
            ExecutionContext for strategy execution
        """
        skill = None
        prompt = task.prompt or ""

        # Load skill if specified
        if task.skill:
            try:
                skill = self._skill_registry.get(task.skill)
                # Use task.prompt as arguments for skill
                prompt = task.prompt or ""
            except SkillNotFoundError:
                raise ExecutionError(
                    f"Skill not found: {task.skill}",
                    task_id=task.id,
                )

        return ExecutionContext(
            task=task,
            skill=skill,
            prompt=prompt,
            working_dir=env.working_dir,  # Use environment's working dir (possibly worktree)
            session_id=session_id,
            execution_id=execution_id,
            tracker=self._tracker,
        )

    def execute(
        self,
        task: Task,
        dry_run: bool = False,
        force_plan_mode: bool = False,
    ) -> ExecutionResult:
        """Execute a task in an isolated environment.

        Creates a git worktree for isolation, executes the task, and handles cleanup.
        For plan mode tasks, the worktree is preserved (path returned in metadata).
        For other tasks, the worktree is cleaned up after execution.

        If a tracker is configured, emits real-time execution events.

        Args:
            task: The task to execute
            dry_run: If True, only build command without executing
            force_plan_mode: If True, use plan mode strategy

        Returns:
            ExecutionResult with execution details
        """
        # Validate working directory
        if not task.working_dir.exists():
            raise ExecutionError(
                f"Working directory does not exist: {task.working_dir}",
                task_id=task.id,
            )

        # Determine if this is a plan mode execution
        is_plan_mode = force_plan_mode or task.plan_mode

        # Create isolated execution environment
        env = self._create_execution_environment(task)

        # Create session
        session = self._session_manager.create_session(
            task_id=task.id,
            metadata={
                "task_name": task.name,
                "dry_run": dry_run,
                "isolated": env.is_isolated,
                "worktree_path": env.worktree_path,
            },
        )

        # Start tracking if tracker is available
        execution_id = None
        if self._tracker and not dry_run:
            execution_id = self._tracker.start_execution(
                task_id=task.id,
                task_name=task.name,
                session_id=session.id,
            )

        try:
            # Build context with isolated environment
            context = self._build_context(
                task, env, session_id=session.id, execution_id=execution_id
            )

            # Select strategy
            strategy = self._select_strategy(task, force_plan_mode=force_plan_mode)

            if dry_run:
                # Return command without executing
                command = strategy.build_command(context)
                from datetime import datetime

                result = ExecutionResult(
                    task_id=task.id,
                    session_id=session.id,
                    status=ExecutionStatus.SKIPPED,
                    output=f"Dry run - command: {' '.join(command)}",
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                )
            else:
                # Execute
                result = strategy.execute(context)

                # For plan mode, include worktree path and execution_id in metadata
                # so the approval handler can call set_waiting_approval
                if is_plan_mode:
                    metadata = result.metadata or {}
                    if env.is_isolated:
                        metadata["worktree_path"] = env.worktree_path
                    if execution_id:
                        metadata["execution_id"] = execution_id
                    result = ExecutionResult(
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

            # Update task state
            task.update_last_run(result.status.value)

            # Complete session
            self._session_manager.complete_session(
                session.id,
                status=result.status.value,
                output=result.output,
                error=result.error,
            )

            # Save to logs
            self._log_repository.save(result)

            # Finish tracking - but NOT for plan mode (waiting for approval)
            # Plan mode tasks will be finished by the approval handler
            if self._tracker and execution_id:
                if is_plan_mode and result.is_success:
                    # Don't finish - will be set to waiting_approval by handler
                    logger.info(f"Plan mode execution {execution_id} awaiting approval handler")
                else:
                    self._tracker.finish_execution(
                        execution_id=execution_id,
                        success=result.is_success,
                        exit_code=result.exit_code,
                        error=result.error,
                    )

            return result

        except Exception as e:
            # Handle unexpected errors
            from datetime import datetime

            result = ExecutionResult(
                task_id=task.id,
                session_id=session.id,
                status=ExecutionStatus.FAILURE,
                output="",
                started_at=datetime.now(),
                finished_at=datetime.now(),
                error=str(e),
            )

            self._session_manager.complete_session(
                session.id,
                status="failure",
                error=str(e),
            )

            self._log_repository.save(result)

            # Finish tracking with failure
            if self._tracker and execution_id:
                self._tracker.finish_execution(
                    execution_id=execution_id,
                    success=False,
                    error=str(e),
                )

            raise ExecutionError(str(e), task_id=task.id, cause=e) from e

        finally:
            # Cleanup worktree for non-plan-mode tasks
            # Plan mode tasks keep the worktree until approval/cancel
            if not is_plan_mode:
                env.cleanup()

    def execute_plan_mode(self, task: Task) -> ExecutionResult:
        """Execute a task in plan mode (read-only planning).

        This is used for the first phase of plan mode tasks.
        The result includes worktree_path in metadata for later resumption.

        Args:
            task: The task to execute in plan mode

        Returns:
            ExecutionResult with plan output and worktree_path in metadata
        """
        return self.execute(task, dry_run=False, force_plan_mode=True)

    def execute_resume(
        self,
        task: Task,
        session_id: str,
        feedback: str | None = None,
        worktree_path: str | None = None,
    ) -> ExecutionResult:
        """Execute a task by resuming a Claude session.

        Used for plan mode approval/discuss. Executes in the original
        worktree if provided to maintain session continuity.

        Args:
            task: The task (for context)
            session_id: Claude session ID to resume
            feedback: If provided, use feedback strategy (plan mode)
                     If None, use approval strategy (full permissions)
            worktree_path: If provided, execute in this worktree

        Returns:
            ExecutionResult from resumed session
        """
        # Determine working directory
        if worktree_path:
            working_dir = Path(worktree_path)
            if not working_dir.exists():
                logger.warning(f"Worktree no longer exists: {worktree_path}")
                working_dir = task.working_dir
        else:
            working_dir = task.working_dir

        if not working_dir.exists():
            raise ExecutionError(
                f"Working directory does not exist: {working_dir}",
                task_id=task.id,
            )

        # Create execution session
        exec_session = self._session_manager.create_session(
            task_id=task.id,
            metadata={
                "task_name": task.name,
                "resume_session": session_id,
                "has_feedback": feedback is not None,
                "worktree_path": worktree_path,
            },
        )

        try:
            # Build context with the Claude session ID
            context = ExecutionContext(
                task=task,
                skill=None,
                prompt=feedback or "",
                working_dir=working_dir,
                session_id=session_id,  # This is the Claude session to resume
            )

            # Select appropriate resume strategy
            if feedback:
                strategy = ResumeWithFeedbackStrategy(feedback)
            else:
                strategy = self._resume_approval

            # Execute
            result = strategy.execute(context)

            # Update task state
            task.update_last_run(result.status.value)

            # Complete session
            self._session_manager.complete_session(
                exec_session.id,
                status=result.status.value,
                output=result.output,
                error=result.error,
            )

            # Save to logs
            self._log_repository.save(result)

            return result

        except Exception as e:
            from datetime import datetime

            result = ExecutionResult(
                task_id=task.id,
                session_id=exec_session.id,
                status=ExecutionStatus.FAILURE,
                output="",
                started_at=datetime.now(),
                finished_at=datetime.now(),
                error=str(e),
            )

            self._session_manager.complete_session(
                exec_session.id,
                status="failure",
                error=str(e),
            )

            self._log_repository.save(result)
            raise ExecutionError(str(e), task_id=task.id, cause=e) from e

    def get_command(self, task: Task) -> list[str]:
        """Get the command that would be executed for a task (for debugging)."""
        env = ExecutionEnvironment(working_dir=task.working_dir)
        context = self._build_context(task, env)
        strategy = self._select_strategy(task)
        return strategy.build_command(context)
