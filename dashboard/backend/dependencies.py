"""Dependency injection for services."""

from functools import lru_cache
from pathlib import Path

from config import settings

# Import from codegeass package
import sys
sys.path.insert(0, str(settings.PROJECT_DIR / "src"))

from codegeass.storage.task_repository import TaskRepository
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.channel_repository import ChannelRepository
from codegeass.factory.registry import SkillRegistry
from codegeass.scheduling.scheduler import Scheduler
from codegeass.execution.session import SessionManager

from services import TaskService, SkillService, LogService, SchedulerService, NotificationService


# Singleton instances
_task_repo: TaskRepository | None = None
_log_repo: LogRepository | None = None
_channel_repo: ChannelRepository | None = None
_skill_registry: SkillRegistry | None = None
_session_manager: SessionManager | None = None
_scheduler: Scheduler | None = None
_core_notification_service = None  # Core NotificationService for task execution
_notification_service = None  # Dashboard NotificationService wrapper for API


def get_task_repo() -> TaskRepository:
    """Get or create TaskRepository singleton."""
    global _task_repo
    if _task_repo is None:
        _task_repo = TaskRepository(settings.get_schedules_path())
    return _task_repo


def get_log_repo() -> LogRepository:
    """Get or create LogRepository singleton."""
    global _log_repo
    if _log_repo is None:
        _log_repo = LogRepository(settings.get_logs_dir())
    return _log_repo


def get_skill_registry() -> SkillRegistry:
    """Get or create SkillRegistry singleton."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry.get_instance(settings.SKILLS_DIR)
    return _skill_registry


def get_session_manager() -> SessionManager:
    """Get or create SessionManager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(settings.get_sessions_dir())
    return _session_manager


def get_scheduler() -> Scheduler:
    """Get or create Scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(
            task_repository=get_task_repo(),
            skill_registry=get_skill_registry(),
            session_manager=get_session_manager(),
            log_repository=get_log_repo(),
            max_concurrent=1,
        )
        # Register notification handler
        _setup_notification_handler(_scheduler)
    return _scheduler


def _setup_notification_handler(scheduler: Scheduler) -> None:
    """Setup notification handler for the scheduler."""
    try:
        from codegeass.notifications.handler import NotificationHandler

        # Use core singleton service to preserve message_ids state across executions
        core_service = get_core_notification_service()
        handler = NotificationHandler(core_service)
        handler.register_with_scheduler(scheduler)
    except Exception as e:
        # Don't fail if notifications can't be set up
        print(f"Warning: Could not setup notifications: {e}")


# Service factories
def get_task_service() -> TaskService:
    """Get TaskService instance."""
    return TaskService(get_task_repo(), get_log_repo())


def get_skill_service() -> SkillService:
    """Get SkillService instance."""
    return SkillService(get_skill_registry())


def get_log_service() -> LogService:
    """Get LogService instance."""
    return LogService(get_log_repo(), get_task_repo())


def get_scheduler_service() -> SchedulerService:
    """Get SchedulerService instance."""
    return SchedulerService(get_scheduler(), get_task_repo())


def get_channel_repo() -> ChannelRepository:
    """Get or create ChannelRepository singleton."""
    global _channel_repo
    if _channel_repo is None:
        notifications_path = settings.CONFIG_DIR / "notifications.yaml"
        _channel_repo = ChannelRepository(notifications_path)
    return _channel_repo


def get_core_notification_service():
    """Get or create core NotificationService singleton.

    This is the core service used by the notification handler for task execution.
    It preserves message_ids state across task start/complete notifications.
    """
    global _core_notification_service
    if _core_notification_service is None:
        from codegeass.notifications.service import NotificationService as CoreNotificationService
        _core_notification_service = CoreNotificationService(get_channel_repo())
    return _core_notification_service


def get_notification_service() -> NotificationService:
    """Get or create dashboard NotificationService singleton.

    This is the dashboard wrapper that provides API-compatible methods.
    It uses the core singleton to ensure message_ids are shared.
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(
            channel_repo=get_channel_repo(),
            core_service=get_core_notification_service(),
        )
    return _notification_service
