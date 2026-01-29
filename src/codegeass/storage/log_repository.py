"""Execution log repository using JSON files."""

import json
from datetime import datetime
from pathlib import Path

from codegeass.core.value_objects import ExecutionResult, ExecutionStatus


class LogRepository:
    """Repository for execution logs using JSON files.

    Stores logs in JSON Lines format (one JSON object per line).
    Each task has its own log file: {task_id}.jsonl
    """

    def __init__(self, logs_dir: Path):
        """Initialize with path to logs directory."""
        self._logs_dir = logs_dir
        self._logs_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self, task_id: str) -> Path:
        """Get log file path for a task."""
        return self._logs_dir / f"{task_id}.jsonl"

    def _get_all_log_file(self) -> Path:
        """Get the aggregated log file path."""
        return self._logs_dir / "all.jsonl"

    def save(self, result: ExecutionResult) -> None:
        """Save an execution result."""
        # Save to task-specific file
        task_log = self._get_log_file(result.task_id)
        with open(task_log, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

        # Also save to aggregated file
        all_log = self._get_all_log_file()
        with open(all_log, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    def find_by_task_id(self, task_id: str, limit: int = 10) -> list[ExecutionResult]:
        """Find execution results for a task, most recent first."""
        log_file = self._get_log_file(task_id)
        if not log_file.exists():
            return []

        results = []
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        results.append(ExecutionResult.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Sort by started_at descending and limit
        results.sort(key=lambda r: r.started_at, reverse=True)
        return results[:limit]

    def find_latest(self, task_id: str) -> ExecutionResult | None:
        """Find the latest execution result for a task."""
        results = self.find_by_task_id(task_id, limit=1)
        return results[0] if results else None

    def find_all(self, limit: int = 100) -> list[ExecutionResult]:
        """Find all execution results, most recent first."""
        all_log = self._get_all_log_file()
        if not all_log.exists():
            return []

        results = []
        with open(all_log) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        results.append(ExecutionResult.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Sort by started_at descending and limit
        results.sort(key=lambda r: r.started_at, reverse=True)
        return results[:limit]

    def find_by_status(self, status: str, limit: int = 100) -> list[ExecutionResult]:
        """Find execution results by status."""
        all_results = self.find_all(limit=limit * 10)  # Fetch more to filter
        filtered = [r for r in all_results if r.status.value == status]
        return filtered[:limit]

    def find_by_date_range(
        self, start: datetime, end: datetime, task_id: str | None = None
    ) -> list[ExecutionResult]:
        """Find execution results within a date range."""
        if task_id:
            results = self.find_by_task_id(task_id, limit=10000)
        else:
            results = self.find_all(limit=10000)

        return [r for r in results if start <= r.started_at <= end]

    def get_task_stats(self, task_id: str) -> dict:
        """Get execution statistics for a task."""
        results = self.find_by_task_id(task_id, limit=1000)

        if not results:
            return {
                "total_runs": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "last_run": None,
                "last_status": None,
            }

        success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
        failure_count = sum(1 for r in results if r.status == ExecutionStatus.FAILURE)
        durations = [r.duration_seconds for r in results]

        return {
            "total_runs": len(results),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / len(results) * 100 if results else 0.0,
            "avg_duration": sum(durations) / len(durations) if durations else 0.0,
            "last_run": results[0].started_at.isoformat() if results else None,
            "last_status": results[0].status.value if results else None,
        }

    def clear_task_logs(self, task_id: str) -> bool:
        """Clear all logs for a task. Returns True if logs existed."""
        log_file = self._get_log_file(task_id)
        if log_file.exists():
            log_file.unlink()
            return True
        return False

    def tail(self, task_id: str, lines: int = 20) -> list[ExecutionResult]:
        """Get the most recent N execution results for a task."""
        return self.find_by_task_id(task_id, limit=lines)
