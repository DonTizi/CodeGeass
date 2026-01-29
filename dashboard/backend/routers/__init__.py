"""API routers for CodeGeass Dashboard."""

from .tasks import router as tasks_router
from .skills import router as skills_router
from .logs import router as logs_router
from .scheduler import router as scheduler_router

__all__ = [
    "tasks_router",
    "skills_router",
    "logs_router",
    "scheduler_router",
]
