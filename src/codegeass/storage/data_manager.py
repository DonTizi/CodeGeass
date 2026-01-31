"""Centralized data management and cleanup for CodeGeass.

This module manages execution data stored in ~/.codegeass/data/{project-id}/
including logs, sessions, and approvals with retention-based cleanup.
"""

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import yaml


@dataclass
class DataStats:
    """Statistics for data usage."""

    project_id: str
    logs_count: int
    logs_size_bytes: int
    sessions_count: int
    sessions_size_bytes: int
    approvals_count: int
    approvals_size_bytes: int
    total_size_bytes: int

    @property
    def total_size_mb(self) -> float:
        """Total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "project_id": self.project_id,
            "logs_count": self.logs_count,
            "logs_size_bytes": self.logs_size_bytes,
            "sessions_count": self.sessions_count,
            "sessions_size_bytes": self.sessions_size_bytes,
            "approvals_count": self.approvals_count,
            "approvals_size_bytes": self.approvals_size_bytes,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": round(self.total_size_mb, 2),
        }


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    sessions_removed: int
    logs_removed: int
    approvals_removed: int
    bytes_freed: int

    @property
    def total_removed(self) -> int:
        """Total items removed."""
        return self.sessions_removed + self.logs_removed + self.approvals_removed

    @property
    def bytes_freed_mb(self) -> float:
        """Bytes freed in megabytes."""
        return self.bytes_freed / (1024 * 1024)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sessions_removed": self.sessions_removed,
            "logs_removed": self.logs_removed,
            "approvals_removed": self.approvals_removed,
            "total_removed": self.total_removed,
            "bytes_freed": self.bytes_freed,
            "bytes_freed_mb": round(self.bytes_freed_mb, 2),
        }


class DataManager:
    """Centralized data management and cleanup.

    All execution data is stored in ~/.codegeass/data/{project-id}/ with
    separate directories for logs, sessions, and approvals.

    Directory structure:
        ~/.codegeass/data/
        └── {project-id}/
            ├── logs/
            │   ├── {task_id}.jsonl
            │   └── all.jsonl
            ├── sessions/
            │   └── {uuid}.json
            ├── approvals.yaml
            └── active_executions.json

    Default retention periods (based on industry best practices):
        - Sessions: 7 days (debugging, can regenerate)
        - Logs: 30 days (default industry standard)
        - Approvals: 90 days (audit trail)
    """

    GLOBAL_DATA_DIR = Path.home() / ".codegeass" / "data"

    # Default retention periods in days
    DEFAULT_RETENTION = {
        "sessions": 7,    # Short-term debugging
        "logs": 30,       # Azure default, industry standard
        "approvals": 90,  # Audit trail, security best practices
    }

    def __init__(self, global_data_dir: Path | None = None):
        """Initialize DataManager.

        Args:
            global_data_dir: Override the global data directory (for testing)
        """
        self._data_dir = global_data_dir or self.GLOBAL_DATA_DIR

    @property
    def data_dir(self) -> Path:
        """Get the global data directory."""
        return self._data_dir

    def get_project_data_dir(self, project_id: str) -> Path:
        """Get data directory for a specific project.

        Args:
            project_id: The project ID (from projects.yaml or hash)

        Returns:
            Path to project's data directory
        """
        return self._data_dir / project_id

    @staticmethod
    def hash_path(path: Path) -> str:
        """Generate a short hash for a project path.

        Used for unregistered projects that don't have a project ID.

        Args:
            path: The project path

        Returns:
            8-character hash of the path
        """
        return hashlib.md5(str(path.resolve()).encode()).hexdigest()[:8]

    def get_data_dir_for_path(self, project_path: Path, project_id: str | None = None) -> Path:
        """Get data directory for a project path.

        If project_id is provided, uses that. Otherwise, generates a hash
        from the project path for unregistered projects.

        Args:
            project_path: Path to the project
            project_id: Optional project ID from registry

        Returns:
            Path to project's data directory
        """
        if project_id:
            return self.get_project_data_dir(project_id)
        return self.get_project_data_dir(self.hash_path(project_path))

    def ensure_project_dirs(self, project_id: str) -> Path:
        """Ensure project data directories exist.

        Creates:
            - {data_dir}/logs/
            - {data_dir}/sessions/

        Args:
            project_id: The project ID

        Returns:
            Path to project data directory
        """
        project_dir = self.get_project_data_dir(project_id)
        (project_dir / "logs").mkdir(parents=True, exist_ok=True)
        (project_dir / "sessions").mkdir(parents=True, exist_ok=True)
        return project_dir

    def list_project_ids(self) -> list[str]:
        """List all project IDs with data.

        Returns:
            List of project IDs (directory names under ~/.codegeass/data/)
        """
        if not self._data_dir.exists():
            return []
        return [
            d.name for d in self._data_dir.iterdir()
            if d.is_dir()
        ]

    def get_stats(self, project_id: str | None = None) -> DataStats | list[DataStats]:
        """Get data usage statistics.

        Args:
            project_id: Specific project ID, or None for all projects

        Returns:
            DataStats for one project, or list of DataStats for all projects
        """
        if project_id:
            return self._get_project_stats(project_id)

        return [
            self._get_project_stats(pid)
            for pid in self.list_project_ids()
        ]

    def _get_project_stats(self, project_id: str) -> DataStats:
        """Get stats for a single project."""
        project_dir = self.get_project_data_dir(project_id)

        logs_dir = project_dir / "logs"
        sessions_dir = project_dir / "sessions"
        approvals_file = project_dir / "approvals.yaml"

        # Count and size logs
        logs_count = 0
        logs_size = 0
        if logs_dir.exists():
            for f in logs_dir.glob("*.jsonl"):
                logs_count += 1
                logs_size += f.stat().st_size

        # Count and size sessions
        sessions_count = 0
        sessions_size = 0
        if sessions_dir.exists():
            for f in sessions_dir.glob("*.json"):
                sessions_count += 1
                sessions_size += f.stat().st_size

        # Count and size approvals
        approvals_count = 0
        approvals_size = 0
        if approvals_file.exists():
            approvals_size = approvals_file.stat().st_size
            try:
                with open(approvals_file) as f:
                    data = yaml.safe_load(f)
                    approvals_count = len(data.get("approvals", []))
            except (yaml.YAMLError, OSError):
                pass

        return DataStats(
            project_id=project_id,
            logs_count=logs_count,
            logs_size_bytes=logs_size,
            sessions_count=sessions_count,
            sessions_size_bytes=sessions_size,
            approvals_count=approvals_count,
            approvals_size_bytes=approvals_size,
            total_size_bytes=logs_size + sessions_size + approvals_size,
        )

    def cleanup(
        self,
        project_id: str | None = None,
        sessions_days: int | None = None,
        logs_days: int | None = None,
        approvals_days: int | None = None,
        dry_run: bool = False,
    ) -> CleanupResult | list[CleanupResult]:
        """Clean up old data based on retention periods.

        Args:
            project_id: Specific project ID, or None for all projects
            sessions_days: Keep sessions for this many days (default: 7)
            logs_days: Keep logs for this many days (default: 30)
            approvals_days: Keep approvals for this many days (default: 90)
            dry_run: If True, don't actually delete, just count

        Returns:
            CleanupResult for one project, or list for all projects
        """
        # Use defaults if not specified
        sessions_days = sessions_days or self.DEFAULT_RETENTION["sessions"]
        logs_days = logs_days or self.DEFAULT_RETENTION["logs"]
        approvals_days = approvals_days or self.DEFAULT_RETENTION["approvals"]

        if project_id:
            return self._cleanup_project(
                project_id, sessions_days, logs_days, approvals_days, dry_run
            )

        results = []
        for pid in self.list_project_ids():
            result = self._cleanup_project(
                pid, sessions_days, logs_days, approvals_days, dry_run
            )
            results.append(result)
        return results

    def _cleanup_project(
        self,
        project_id: str,
        sessions_days: int,
        logs_days: int,
        approvals_days: int,
        dry_run: bool,
    ) -> CleanupResult:
        """Clean up data for a single project."""
        project_dir = self.get_project_data_dir(project_id)
        now = datetime.now()

        sessions_removed = 0
        logs_removed = 0
        approvals_removed = 0
        bytes_freed = 0

        # Clean sessions
        sessions_dir = project_dir / "sessions"
        sessions_cutoff = now - timedelta(days=sessions_days)
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file) as f:
                        data = json.load(f)
                        started_at = datetime.fromisoformat(data["started_at"])
                        if started_at < sessions_cutoff:
                            if not dry_run:
                                bytes_freed += session_file.stat().st_size
                                session_file.unlink()
                            else:
                                bytes_freed += session_file.stat().st_size
                            sessions_removed += 1
                except (json.JSONDecodeError, KeyError, OSError):
                    continue

        # Clean logs - only remove entries older than cutoff
        logs_dir = project_dir / "logs"
        logs_cutoff = now - timedelta(days=logs_days)
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.jsonl"):
                entries_removed, bytes_saved = self._cleanup_log_file(
                    log_file, logs_cutoff, dry_run
                )
                logs_removed += entries_removed
                bytes_freed += bytes_saved

        # Clean approvals
        approvals_file = project_dir / "approvals.yaml"
        approvals_cutoff = now - timedelta(days=approvals_days)
        if approvals_file.exists():
            removed, bytes_saved = self._cleanup_approvals(
                approvals_file, approvals_cutoff, dry_run
            )
            approvals_removed = removed
            bytes_freed += bytes_saved

        return CleanupResult(
            sessions_removed=sessions_removed,
            logs_removed=logs_removed,
            approvals_removed=approvals_removed,
            bytes_freed=bytes_freed,
        )

    def _cleanup_log_file(
        self, log_file: Path, cutoff: datetime, dry_run: bool
    ) -> tuple[int, int]:
        """Clean up entries in a log file older than cutoff.

        Returns (entries_removed, bytes_saved).
        """
        if not log_file.exists():
            return 0, 0

        original_size = log_file.stat().st_size
        kept_entries = []
        removed_count = 0

        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    started_at = datetime.fromisoformat(data.get("started_at", ""))
                    if started_at >= cutoff:
                        kept_entries.append(line)
                    else:
                        removed_count += 1
                except (json.JSONDecodeError, ValueError):
                    # Keep malformed entries
                    kept_entries.append(line)

        if removed_count > 0 and not dry_run:
            with open(log_file, "w") as f:
                for entry in kept_entries:
                    f.write(entry + "\n")

        new_size = sum(len(e) + 1 for e in kept_entries)  # +1 for newline
        bytes_saved = original_size - new_size if removed_count > 0 else 0

        return removed_count, bytes_saved

    def _cleanup_approvals(
        self, approvals_file: Path, cutoff: datetime, dry_run: bool
    ) -> tuple[int, int]:
        """Clean up terminal approvals older than cutoff.

        Returns (entries_removed, bytes_saved).
        """
        if not approvals_file.exists():
            return 0, 0

        original_size = approvals_file.stat().st_size

        try:
            with open(approvals_file) as f:
                data = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError):
            return 0, 0

        approvals = data.get("approvals", [])
        original_count = len(approvals)

        # Terminal statuses that can be cleaned up
        terminal_statuses = {"completed", "cancelled", "expired", "failed"}

        kept_approvals = []
        for approval in approvals:
            status = approval.get("status", "")
            created_at_str = approval.get("created_at", "")

            # Keep non-terminal approvals
            if status not in terminal_statuses:
                kept_approvals.append(approval)
                continue

            # Keep terminal approvals newer than cutoff
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at >= cutoff:
                        kept_approvals.append(approval)
                except ValueError:
                    # Invalid date, keep it
                    kept_approvals.append(approval)
            else:
                # No date, keep it
                kept_approvals.append(approval)

        removed_count = original_count - len(kept_approvals)

        if removed_count > 0 and not dry_run:
            data["approvals"] = kept_approvals
            with open(approvals_file, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        # Estimate bytes saved
        new_size = approvals_file.stat().st_size if removed_count > 0 and not dry_run else 0
        bytes_saved = original_size - new_size if removed_count > 0 and not dry_run else 0

        # For dry run, estimate
        if dry_run and removed_count > 0:
            avg_entry_size = original_size / max(original_count, 1)
            bytes_saved = int(avg_entry_size * removed_count)

        return removed_count, bytes_saved

    def purge(self, project_id: str) -> bool:
        """Delete all data for a project.

        Args:
            project_id: The project ID to purge

        Returns:
            True if data was deleted, False if project had no data
        """
        project_dir = self.get_project_data_dir(project_id)
        if not project_dir.exists():
            return False

        shutil.rmtree(project_dir)
        return True

    def migrate_project_data(
        self,
        project_path: Path,
        project_id: str,
        remove_old: bool = False,
    ) -> bool:
        """Migrate data from project-local to global storage.

        Migrates data from {project}/data/ to ~/.codegeass/data/{project_id}/

        Args:
            project_path: Path to the project
            project_id: The project ID
            remove_old: If True, remove old data after migration

        Returns:
            True if migration was performed, False if no data to migrate
        """
        old_data_dir = project_path / "data"
        if not old_data_dir.exists():
            return False

        new_data_dir = self.get_project_data_dir(project_id)

        # Migrate logs
        old_logs = old_data_dir / "logs"
        new_logs = new_data_dir / "logs"
        if old_logs.exists():
            new_logs.mkdir(parents=True, exist_ok=True)
            for log_file in old_logs.glob("*.jsonl"):
                dest = new_logs / log_file.name
                if dest.exists():
                    # Merge log files
                    with open(dest, "a") as f_dest:
                        with open(log_file) as f_src:
                            f_dest.write(f_src.read())
                else:
                    shutil.copy2(log_file, dest)

        # Migrate sessions
        old_sessions = old_data_dir / "sessions"
        new_sessions = new_data_dir / "sessions"
        if old_sessions.exists():
            new_sessions.mkdir(parents=True, exist_ok=True)
            for session_file in old_sessions.glob("*.json"):
                dest = new_sessions / session_file.name
                if not dest.exists():
                    shutil.copy2(session_file, dest)

        # Migrate approvals
        old_approvals = old_data_dir / "approvals.yaml"
        new_approvals = new_data_dir / "approvals.yaml"
        if old_approvals.exists():
            if new_approvals.exists():
                # Merge approvals
                try:
                    with open(old_approvals) as f:
                        old_data = yaml.safe_load(f) or {}
                    with open(new_approvals) as f:
                        new_data = yaml.safe_load(f) or {}

                    old_list = old_data.get("approvals", [])
                    new_list = new_data.get("approvals", [])

                    # Merge by ID
                    existing_ids = {a.get("id") for a in new_list}
                    for approval in old_list:
                        if approval.get("id") not in existing_ids:
                            new_list.append(approval)

                    new_data["approvals"] = new_list
                    with open(new_approvals, "w") as f:
                        yaml.dump(new_data, f, default_flow_style=False, sort_keys=False)
                except (yaml.YAMLError, OSError):
                    pass
            else:
                new_approvals.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_approvals, new_approvals)

        # Migrate active_executions.json
        old_active = old_data_dir / "active_executions.json"
        new_active = new_data_dir / "active_executions.json"
        if old_active.exists() and not new_active.exists():
            shutil.copy2(old_active, new_active)

        # Remove old data if requested
        if remove_old:
            shutil.rmtree(old_data_dir)

        return True
