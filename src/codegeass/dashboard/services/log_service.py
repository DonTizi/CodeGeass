"""Log service wrapping LogRepository."""

from datetime import datetime
from typing import Any

from codegeass.core.value_objects import ExecutionResult as CoreResult
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.task_repository import TaskRepository

from ..models import ExecutionResult, ExecutionStatus, LogFilter, LogStats


class LogService:
    """Service for managing execution logs."""

    def __init__(self, log_repo: LogRepository, task_repo: TaskRepository):
        self.log_repo = log_repo
        self.task_repo = task_repo

    def _core_to_api(self, result: CoreResult) -> ExecutionResult:
        """Convert core ExecutionResult to API model."""
        # Get task name if available
        task_name = None
        task = self.task_repo.find_by_id(result.task_id)
        if task:
            task_name = task.name

        return ExecutionResult(
            task_id=result.task_id,
            task_name=task_name,
            session_id=result.session_id,
            status=ExecutionStatus(result.status.value),
            output=result.output,
            clean_output=result.clean_output,
            error=result.error,
            exit_code=result.exit_code,
            started_at=result.started_at.isoformat(),
            finished_at=result.finished_at.isoformat() if result.finished_at else None,
            duration_seconds=result.duration_seconds,
        )

    def get_logs(self, filter: LogFilter | None = None) -> list[ExecutionResult]:
        """Get execution logs with optional filtering."""
        if filter is None:
            filter = LogFilter()

        if filter.status:
            core_results = self.log_repo.find_by_status(
                filter.status.value,
                limit=filter.limit
            )
        elif filter.task_id:
            core_results = self.log_repo.find_by_task_id(
                filter.task_id,
                limit=filter.limit
            )
        elif filter.start_date and filter.end_date:
            start = datetime.fromisoformat(filter.start_date)
            end = datetime.fromisoformat(filter.end_date)
            core_results = self.log_repo.find_by_date_range(
                start, end,
                task_id=filter.task_id
            )
        else:
            core_results = self.log_repo.find_all(limit=filter.limit)

        return [self._core_to_api(r) for r in core_results]

    def get_task_logs(self, task_id: str, limit: int = 10) -> list[ExecutionResult]:
        """Get logs for a specific task."""
        core_results = self.log_repo.find_by_task_id(task_id, limit=limit)
        return [self._core_to_api(r) for r in core_results]

    def get_latest_log(self, task_id: str) -> ExecutionResult | None:
        """Get the latest log for a task."""
        result = self.log_repo.find_latest(task_id)
        if result:
            return self._core_to_api(result)
        return None

    def get_overall_stats(self) -> LogStats:
        """Get overall log statistics."""
        all_logs = self.log_repo.find_all(limit=10000)

        total = len(all_logs)
        successful = sum(1 for r in all_logs if r.status.value == "success")
        failed = sum(1 for r in all_logs if r.status.value == "failure")
        timeout = sum(1 for r in all_logs if r.status.value == "timeout")

        success_rate = (successful / total * 100) if total > 0 else 0.0

        durations = [r.duration_seconds for r in all_logs if r.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        last_execution = None
        if all_logs:
            last_execution = max(r.finished_at for r in all_logs if r.finished_at)
            if last_execution:
                last_execution = last_execution.isoformat()

        # Per-task breakdown
        by_task: dict[str, dict[str, Any]] = {}
        for task in self.task_repo.find_all():
            stats = self.log_repo.get_task_stats(task.id)
            by_task[task.id] = {
                "name": task.name,
                "total": stats.get("total", 0),
                "success": stats.get("success", 0),
                "failure": stats.get("failure", 0),
                "success_rate": stats.get("success_rate", 0.0),
            }

        return LogStats(
            total_executions=total,
            successful=successful,
            failed=failed,
            timeout=timeout,
            success_rate=success_rate,
            avg_duration_seconds=avg_duration,
            last_execution=last_execution,
            by_task=by_task,
        )

    def clear_task_logs(self, task_id: str) -> bool:
        """Clear logs for a specific task."""
        return self.log_repo.clear_task_logs(task_id)

    def tail_logs(self, task_id: str, lines: int = 20) -> list[ExecutionResult]:
        """Get the most recent logs for a task."""
        core_results = self.log_repo.tail(task_id, lines=lines)
        return [self._core_to_api(r) for r in core_results]
