"""Execution environment management."""

import logging
from dataclasses import dataclass
from pathlib import Path

from codegeass.core.entities import Task
from codegeass.execution.worktree import WorktreeInfo, WorktreeManager

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


def create_execution_environment(task: Task) -> ExecutionEnvironment:
    """Create an isolated execution environment for a task.

    Attempts to create a git worktree for isolation. If the project
    is not a git repo or worktree creation fails, falls back to
    using the original working directory.
    """
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

    logger.debug(f"Using original directory for {task.name}: {task.working_dir}")
    return ExecutionEnvironment(
        working_dir=task.working_dir,
        worktree_info=None,
    )
