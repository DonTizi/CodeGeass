"""Main executor for Claude Code tasks."""

from pathlib import Path

from codegeass.core.entities import Task
from codegeass.core.exceptions import ExecutionError, SkillNotFoundError
from codegeass.core.value_objects import ExecutionResult, ExecutionStatus
from codegeass.execution.session import SessionManager
from codegeass.execution.strategies import (
    AutonomousStrategy,
    ExecutionContext,
    ExecutionStrategy,
    HeadlessStrategy,
    SkillStrategy,
)
from codegeass.factory.registry import SkillRegistry
from codegeass.storage.log_repository import LogRepository


class ClaudeExecutor:
    """Main executor for Claude Code tasks.

    Coordinates strategy selection, session management, and logging.
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        session_manager: SessionManager,
        log_repository: LogRepository,
    ):
        """Initialize executor with dependencies."""
        self._skill_registry = skill_registry
        self._session_manager = session_manager
        self._log_repository = log_repository

        # Strategy instances
        self._headless = HeadlessStrategy()
        self._autonomous = AutonomousStrategy()
        self._skill_strategy = SkillStrategy()

    def _select_strategy(self, task: Task) -> ExecutionStrategy:
        """Select appropriate execution strategy based on task configuration."""
        if task.skill:
            return self._skill_strategy
        elif task.autonomous:
            return self._autonomous
        else:
            return self._headless

    def _build_context(self, task: Task) -> ExecutionContext:
        """Build execution context for a task."""
        skill = None
        prompt = task.prompt or ""

        # Load skill if specified
        if task.skill:
            try:
                skill = self._skill_registry.get(task.skill)
                # Use task.prompt as arguments for skill (replaces $ARGUMENTS in skill content)
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
            working_dir=task.working_dir,
        )

    def execute(self, task: Task, dry_run: bool = False) -> ExecutionResult:
        """Execute a task.

        Args:
            task: The task to execute
            dry_run: If True, only build command without executing

        Returns:
            ExecutionResult with execution details
        """
        # Validate working directory
        if not task.working_dir.exists():
            raise ExecutionError(
                f"Working directory does not exist: {task.working_dir}",
                task_id=task.id,
            )

        # Create session
        session = self._session_manager.create_session(
            task_id=task.id,
            metadata={"task_name": task.name, "dry_run": dry_run},
        )

        try:
            # Build context
            context = self._build_context(task)
            context.session_id = session.id

            # Select strategy
            strategy = self._select_strategy(task)

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
            raise ExecutionError(str(e), task_id=task.id, cause=e) from e

    def get_command(self, task: Task) -> list[str]:
        """Get the command that would be executed for a task (for debugging)."""
        context = self._build_context(task)
        strategy = self._select_strategy(task)
        return strategy.build_command(context)
