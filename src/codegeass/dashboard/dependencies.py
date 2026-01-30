"""Dependency injection for services."""


from codegeass.execution.session import SessionManager
from codegeass.factory.registry import SkillRegistry
from codegeass.scheduling.scheduler import Scheduler
from codegeass.storage.approval_repository import PendingApprovalRepository
from codegeass.storage.channel_repository import ChannelRepository
from codegeass.storage.log_repository import LogRepository
from codegeass.storage.task_repository import TaskRepository

from .config import settings
from .services import (
    ApprovalService,
    LogService,
    NotificationService,
    SchedulerService,
    SkillService,
    TaskService,
)

# Singleton instances
_task_repo: TaskRepository | None = None
_log_repo: LogRepository | None = None
_channel_repo: ChannelRepository | None = None
_approval_repo: PendingApprovalRepository | None = None
_skill_registry: SkillRegistry | None = None
_session_manager: SessionManager | None = None
_scheduler: Scheduler | None = None
_core_notification_service = None  # Core NotificationService for task execution
_notification_service = None  # Dashboard NotificationService wrapper for API
_approval_service = None  # ApprovalService for plan mode
_execution_tracker = None  # ExecutionTracker for real-time monitoring


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
        _skill_registry = SkillRegistry.get_instance(settings.skills_dir)
    return _skill_registry


def get_session_manager() -> SessionManager:
    """Get or create SessionManager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(settings.get_sessions_dir())
    return _session_manager


def get_execution_tracker():
    """Get or create ExecutionTracker singleton."""
    global _execution_tracker
    if _execution_tracker is None:
        from codegeass.execution.tracker import get_execution_tracker as core_get_tracker
        _execution_tracker = core_get_tracker(settings.data_dir)
    return _execution_tracker


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
            tracker=get_execution_tracker(),
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

        # Pass approval and channel repos for plan mode support
        handler = NotificationHandler(
            service=core_service,
            approval_repo=get_approval_repo(),
            channel_repo=get_channel_repo(),
        )
        handler.register_with_scheduler(scheduler)
    except Exception as e:
        # Don't fail if notifications can't be set up
        print(f"Warning: Could not setup notifications: {e}")
        import traceback
        traceback.print_exc()


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
        notifications_path = settings.config_dir / "notifications.yaml"
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


def get_approval_repo() -> PendingApprovalRepository:
    """Get or create PendingApprovalRepository singleton."""
    global _approval_repo
    if _approval_repo is None:
        approvals_path = settings.data_dir / "approvals.yaml"
        _approval_repo = PendingApprovalRepository(approvals_path)
    return _approval_repo


def get_approval_service() -> ApprovalService:
    """Get or create ApprovalService singleton."""
    global _approval_service
    if _approval_service is None:
        _approval_service = ApprovalService(
            approval_repo=get_approval_repo(),
            channel_repo=get_channel_repo(),
        )
    return _approval_service
