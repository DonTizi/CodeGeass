"""Build execution context for tasks."""

from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Skill, Task
from codegeass.core.exceptions import ExecutionError, SkillNotFoundError
from codegeass.execution.executor.environment import ExecutionEnvironment
from codegeass.execution.strategies import ExecutionContext

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker
    from codegeass.factory.registry import SkillRegistry


def build_context(
    task: Task,
    env: ExecutionEnvironment,
    skill_registry: "SkillRegistry",
    session_id: str | None = None,
    execution_id: str | None = None,
    tracker: "ExecutionTracker | None" = None,
) -> ExecutionContext:
    """Build execution context for a task.

    Args:
        task: The task to build context for
        env: The execution environment (with worktree if isolated)
        skill_registry: Registry for loading skills
        session_id: Optional session ID
        execution_id: Optional execution ID for real-time tracking
        tracker: Optional execution tracker

    Returns:
        ExecutionContext for strategy execution
    """
    skill = _load_skill(task, skill_registry)
    prompt = task.prompt or ""

    return ExecutionContext(
        task=task,
        skill=skill,
        prompt=prompt,
        working_dir=env.working_dir,
        session_id=session_id,
        execution_id=execution_id,
        tracker=tracker,
    )


def build_resume_context(
    task: Task,
    session_id: str,
    feedback: str,
    worktree_path: str | None,
) -> ExecutionContext:
    """Build context for resuming a Claude session.

    Args:
        task: The task (for context)
        session_id: Claude session ID to resume
        feedback: Feedback prompt for discussion
        worktree_path: Optional worktree path to use

    Returns:
        ExecutionContext for strategy execution
    """
    working_dir = _resolve_working_dir(task, worktree_path)

    return ExecutionContext(
        task=task,
        skill=None,
        prompt=feedback,
        working_dir=working_dir,
        session_id=session_id,
    )


def _load_skill(task: Task, skill_registry: "SkillRegistry") -> Skill | None:
    """Load skill if specified in task."""
    if not task.skill:
        return None

    try:
        return skill_registry.get(task.skill)
    except SkillNotFoundError:
        raise ExecutionError(
            f"Skill not found: {task.skill}",
            task_id=task.id,
        )


def _resolve_working_dir(task: Task, worktree_path: str | None) -> Path:
    """Resolve the working directory for execution."""
    import logging

    logger = logging.getLogger(__name__)

    if worktree_path:
        working_dir = Path(worktree_path)
        if not working_dir.exists():
            logger.warning(f"Worktree no longer exists: {worktree_path}")
            return task.working_dir
        return working_dir
    return task.working_dir
