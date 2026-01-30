"""Scheduler models for API."""


from pydantic import BaseModel


class SchedulerStatus(BaseModel):
    """Scheduler status information."""
    running: bool = False
    check_interval: int = 60
    max_concurrent: int = 1
    total_tasks: int = 0
    enabled_tasks: int = 0
    due_tasks: int = 0
    last_check: str | None = None
    next_check: str | None = None


class UpcomingRun(BaseModel):
    """Information about an upcoming task run."""
    task_id: str
    task_name: str
    schedule: str
    next_run: str
    skill: str | None = None
    enabled: bool = True
