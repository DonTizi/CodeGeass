"""API routers for CodeGeass Dashboard."""

from .approvals import router as approvals_router
from .executions import router as executions_router
from .logs import router as logs_router
from .notifications import router as notifications_router
from .projects import router as projects_router
from .scheduler import router as scheduler_router
from .skills import router as skills_router
from .tasks import router as tasks_router

__all__ = [
    "tasks_router",
    "skills_router",
    "logs_router",
    "scheduler_router",
    "notifications_router",
    "approvals_router",
    "executions_router",
    "projects_router",
]
