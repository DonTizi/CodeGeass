"""Build execution context for tasks."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from codegeass.core.entities import Skill, Task
from codegeass.core.exceptions import ExecutionError, SkillNotFoundError
from codegeass.execution.executor.environment import ExecutionEnvironment
from codegeass.execution.strategies import ExecutionContext

if TYPE_CHECKING:
    from codegeass.execution.tracker import ExecutionTracker
    from codegeass.factory.registry import SkillRegistry
    from codegeass.hooks.repository import HookRepository

logger = logging.getLogger(__name__)


def build_context(
    task: Task,
    env: ExecutionEnvironment,
    skill_registry: "SkillRegistry",
    session_id: str | None = None,
    execution_id: str | None = None,
    tracker: "ExecutionTracker | None" = None,
    hook_repo: "HookRepository | None" = None,
) -> ExecutionContext:
    """Build execution context for a task.

    Args:
        task: The task to build context for
        env: The execution environment (with worktree if isolated)
        skill_registry: Registry for loading skills
        session_id: Optional session ID
        execution_id: Optional execution ID for real-time tracking
        tracker: Optional execution tracker
        hook_repo: Optional hook repository for resolving tag hooks

    Returns:
        ExecutionContext for strategy execution
    """
    skill = _load_skill(task, skill_registry)
    prompt = task.prompt or ""

    # Resolve hooks for task tags
    hook_settings_path = _resolve_hooks(task, env.working_dir, hook_repo)

    return ExecutionContext(
        task=task,
        skill=skill,
        prompt=prompt,
        working_dir=env.working_dir,
        session_id=session_id,
        execution_id=execution_id,
        tracker=tracker,
        hook_settings_path=hook_settings_path,
    )


def build_resume_context(
    task: Task,
    session_id: str,
    feedback: str,
    worktree_path: str | None,
    hook_repo: "HookRepository | None" = None,
) -> ExecutionContext:
    """Build context for resuming a Claude session.

    Args:
        task: The task (for context)
        session_id: Claude session ID to resume
        feedback: Feedback prompt for discussion
        worktree_path: Optional worktree path to use
        hook_repo: Optional hook repository for resolving tag hooks

    Returns:
        ExecutionContext for strategy execution
    """
    working_dir = _resolve_working_dir(task, worktree_path)

    # Resolve hooks for task tags
    hook_settings_path = _resolve_hooks(task, working_dir, hook_repo)

    return ExecutionContext(
        task=task,
        skill=None,
        prompt=feedback,
        working_dir=working_dir,
        session_id=session_id,
        hook_settings_path=hook_settings_path,
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
    if worktree_path:
        working_dir = Path(worktree_path)
        if not working_dir.exists():
            logger.warning(f"Worktree no longer exists: {worktree_path}")
            return task.working_dir
        return working_dir
    return task.working_dir


def _resolve_hooks(
    task: Task,
    working_dir: Path,
    hook_repo: "HookRepository | None",
) -> Path | None:
    """Resolve hooks for task tags.

    Args:
        task: The task with tags
        working_dir: Task's working directory
        hook_repo: Hook repository (optional)

    Returns:
        Path to temp settings file, or None if no hooks configured.
    """
    if not hook_repo or not task.tags:
        return None

    try:
        from codegeass.hooks.resolver import HookResolver

        resolver = HookResolver(hook_repo)
        settings = resolver.resolve_for_task(task.tags, working_dir)

        if not settings or "hooks" not in settings:
            return None

        # Write to temp file
        settings_path = resolver.write_temp_settings(settings)
        logger.debug(f"Created hook settings at {settings_path} for tags: {task.tags}")
        return settings_path

    except Exception as e:
        logger.warning(f"Failed to resolve hooks for task {task.id}: {e}")
        return None
