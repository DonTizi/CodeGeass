"""Git worktree manager for isolated task execution.

Each task execution gets its own git worktree to prevent Claude Code
sessions from interfering with each other.
"""

import logging
import shutil
import subprocess
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WorktreeInfo:
    """Information about a created worktree."""

    path: Path
    original_dir: Path
    branch_name: str
    task_id: str
    created_at: datetime

    def cleanup(self) -> bool:
        """Remove this worktree."""
        return WorktreeManager.remove_worktree(self.original_dir, self.path)


class WorktreeManager:
    """Manages git worktrees for isolated task execution.

    When a task runs, we create a temporary worktree so that:
    1. Claude Code starts with a fresh session (no context pollution)
    2. Multiple tasks can run in parallel without interference
    3. Each task has its own isolated environment

    Worktrees are created in a `.codegeass-worktrees/` directory
    inside the project, or in a system temp directory if that fails.
    """

    WORKTREE_DIR_NAME = ".codegeass-worktrees"

    @classmethod
    def get_worktree_base_dir(cls, project_dir: Path) -> Path:
        """Get the base directory for worktrees.

        Tries to use a directory inside the project first,
        falls back to system temp if that's not writable.
        """
        # Try project-local directory first
        local_dir = project_dir / cls.WORKTREE_DIR_NAME
        try:
            local_dir.mkdir(parents=True, exist_ok=True)
            # Test if writable
            test_file = local_dir / ".test"
            test_file.touch()
            test_file.unlink()
            return local_dir
        except (PermissionError, OSError):
            pass

        # Fall back to temp directory
        import tempfile

        temp_base = Path(tempfile.gettempdir()) / "codegeass-worktrees"
        temp_base.mkdir(parents=True, exist_ok=True)
        return temp_base

    @classmethod
    def is_git_repo(cls, path: Path) -> bool:
        """Check if path is inside a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    @classmethod
    def get_current_branch(cls, repo_dir: Path) -> str:
        """Get the current branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "HEAD"

    @classmethod
    def create_worktree(
        cls,
        project_dir: Path,
        task_id: str,
        branch: str | None = None,
    ) -> WorktreeInfo | None:
        """Create a new worktree for task execution.

        Args:
            project_dir: The original project directory
            task_id: Task ID for naming the worktree
            branch: Branch to checkout (defaults to current branch)

        Returns:
            WorktreeInfo if successful, None if failed or not a git repo
        """
        if not cls.is_git_repo(project_dir):
            logger.debug(f"Not a git repo: {project_dir}")
            return None

        # Get branch
        if not branch:
            branch = cls.get_current_branch(project_dir)

        # Generate unique worktree name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        worktree_name = f"{task_id}-{timestamp}-{unique_id}"

        # Get worktree base directory
        base_dir = cls.get_worktree_base_dir(project_dir)
        worktree_path = base_dir / worktree_name

        try:
            # Create worktree (detached to avoid branch conflicts)
            result = subprocess.run(
                ["git", "worktree", "add", "--detach", str(worktree_path), branch],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(f"Failed to create worktree: {result.stderr}")
                return None

            logger.info(f"Created worktree at {worktree_path}")

            return WorktreeInfo(
                path=worktree_path,
                original_dir=project_dir,
                branch_name=branch,
                task_id=task_id,
                created_at=datetime.now(),
            )

        except subprocess.TimeoutExpired:
            logger.error("Timeout creating worktree")
            return None
        except Exception as e:
            logger.error(f"Error creating worktree: {e}")
            return None

    @classmethod
    def remove_worktree(cls, project_dir: Path, worktree_path: Path) -> bool:
        """Remove a worktree.

        Args:
            project_dir: The original project directory
            worktree_path: Path to the worktree to remove

        Returns:
            True if successful
        """
        try:
            # First try git worktree remove
            result = subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"Removed worktree: {worktree_path}")
                return True

            # If git remove failed, try manual cleanup
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

            # Prune worktree list
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=project_dir,
                capture_output=True,
                timeout=10,
            )

            return True

        except Exception as e:
            logger.error(f"Error removing worktree: {e}")
            # Try manual cleanup anyway
            try:
                if worktree_path.exists():
                    shutil.rmtree(worktree_path, ignore_errors=True)
            except Exception:
                pass
            return False

    @classmethod
    def cleanup_old_worktrees(cls, project_dir: Path, max_age_hours: int = 24) -> int:
        """Clean up worktrees older than max_age_hours.

        Args:
            project_dir: The project directory
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of worktrees cleaned up
        """
        base_dir = cls.get_worktree_base_dir(project_dir)
        if not base_dir.exists():
            return 0

        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0

        for path in base_dir.iterdir():
            if not path.is_dir():
                continue

            # Check modification time
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                if mtime < cutoff:
                    cls.remove_worktree(project_dir, path)
                    cleaned += 1
            except Exception:
                continue

        return cleaned

    @classmethod
    @contextmanager
    def worktree_context(
        cls,
        project_dir: Path,
        task_id: str,
        keep_on_success: bool = False,
    ) -> Generator[Path, None, None]:
        """Context manager for worktree-based execution.

        Creates a worktree, yields the path, and cleans up on exit
        (unless keep_on_success is True and no exception occurred).

        Args:
            project_dir: The original project directory
            task_id: Task ID for naming
            keep_on_success: If True, don't cleanup on successful exit

        Yields:
            Path to use for execution (worktree path or original if not a git repo)
        """
        worktree = cls.create_worktree(project_dir, task_id)

        if worktree is None:
            # Not a git repo or failed to create - use original directory
            yield project_dir
            return

        success = False
        try:
            yield worktree.path
            success = True
        finally:
            if not (keep_on_success and success):
                worktree.cleanup()
