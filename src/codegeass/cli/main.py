"""Main CLI entry point for CodeGeass."""

from pathlib import Path
from typing import Any

import click
from rich.console import Console

from codegeass import __version__

# Global console for rich output
console = Console()

# Default paths - use current working directory
def _detect_project_dir() -> Path:
    """Detect project directory from current working directory or package location."""
    cwd = Path.cwd()

    # Check if current directory has CodeGeass structure
    if (cwd / "config" / "schedules.yaml").exists():
        return cwd
    if (cwd / ".claude" / "skills").exists() and (cwd / "config").exists():
        return cwd

    # Fall back to package location (development mode)
    pkg_dir = Path(__file__).parent.parent.parent.parent
    if (pkg_dir / "config" / "schedules.yaml").exists():
        return pkg_dir

    # Default to current working directory
    return cwd


DEFAULT_PROJECT_DIR = _detect_project_dir()
DEFAULT_CONFIG_DIR = DEFAULT_PROJECT_DIR / "config"
DEFAULT_DATA_DIR = DEFAULT_PROJECT_DIR / "data"
DEFAULT_SKILLS_DIR = DEFAULT_PROJECT_DIR / ".claude" / "skills"


class Context:
    """CLI context object holding shared state."""

    def __init__(self) -> None:
        self.project_dir = DEFAULT_PROJECT_DIR
        self.config_dir = DEFAULT_CONFIG_DIR
        self.data_dir = DEFAULT_DATA_DIR
        self.skills_dir = DEFAULT_SKILLS_DIR
        self.verbose = False

        # Lazy-loaded components
        self._task_repo = None
        self._log_repo = None
        self._skill_registry = None
        self._session_manager = None
        self._scheduler = None
        self._channel_repo = None
        self._notification_service = None

    @property
    def schedules_file(self) -> Path:
        return self.config_dir / "schedules.yaml"

    @property
    def settings_file(self) -> Path:
        return self.config_dir / "settings.yaml"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @property
    def task_repo(self):
        if self._task_repo is None:
            from codegeass.storage.task_repository import TaskRepository

            self._task_repo = TaskRepository(self.schedules_file)
        return self._task_repo

    @property
    def log_repo(self):
        if self._log_repo is None:
            from codegeass.storage.log_repository import LogRepository

            self._log_repo = LogRepository(self.logs_dir)
        return self._log_repo

    @property
    def skill_registry(self):
        if self._skill_registry is None:
            from codegeass.factory.registry import SkillRegistry

            self._skill_registry = SkillRegistry(self.skills_dir)
        return self._skill_registry

    @property
    def session_manager(self):
        if self._session_manager is None:
            from codegeass.execution.session import SessionManager

            self._session_manager = SessionManager(self.sessions_dir)
        return self._session_manager

    @property
    def channel_repo(self):
        if self._channel_repo is None:
            from codegeass.storage.channel_repository import ChannelRepository

            notifications_file = self.config_dir / "notifications.yaml"
            if notifications_file.exists():
                self._channel_repo = ChannelRepository(notifications_file)
        return self._channel_repo

    @property
    def notification_service(self):
        if self._notification_service is None and self.channel_repo is not None:
            from codegeass.notifications.service import NotificationService

            self._notification_service = NotificationService(self.channel_repo)
        return self._notification_service

    @property
    def scheduler(self):
        if self._scheduler is None:
            from codegeass.scheduling.scheduler import Scheduler

            self._scheduler = Scheduler(
                task_repository=self.task_repo,
                skill_registry=self.skill_registry,
                session_manager=self.session_manager,
                log_repository=self.log_repo,
            )

            # Register notification handler if notifications are configured
            self._setup_notification_handler(self._scheduler)

        return self._scheduler

    def _setup_notification_handler(self, scheduler) -> None:
        """Setup notification handler for the scheduler."""
        try:
            from codegeass.notifications.handler import NotificationHandler

            # Use singleton notification_service to preserve message_ids state
            if self.notification_service is not None:
                handler = NotificationHandler(self.notification_service)
                handler.register_with_scheduler(scheduler)
        except Exception as e:
            # Don't fail if notifications can't be set up
            if self.verbose:
                console.print(f"[yellow]Warning: Could not setup notifications: {e}[/yellow]")


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.version_option(version=__version__, prog_name="codegeass")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project directory (default: detected from CLI location)",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, project_dir: Path | None) -> None:
    """CodeGeass - Claude Code Scheduler Framework.

    Orchestrate automated Claude Code sessions with templates, prompts and skills.
    """
    context = Context()
    context.verbose = verbose

    if project_dir:
        context.project_dir = project_dir
        context.config_dir = project_dir / "config"
        context.data_dir = project_dir / "data"
        context.skills_dir = project_dir / ".claude" / "skills"

    ctx.obj = context


# Import and register command groups
from codegeass.cli.commands import logs, notification, scheduler, skill, task

cli.add_command(task.task)
cli.add_command(skill.skill)
cli.add_command(scheduler.scheduler)
cli.add_command(logs.logs)
cli.add_command(notification.notification)


@cli.command()
@pass_context
def init(ctx: Context) -> None:
    """Initialize CodeGeass project structure."""
    from rich.panel import Panel

    # Create directories
    dirs_to_create = [
        ctx.config_dir,
        ctx.data_dir / "logs",
        ctx.data_dir / "sessions",
        ctx.skills_dir,
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        if ctx.verbose:
            console.print(f"Created: {dir_path}")

    # Create default config files if they don't exist
    if not ctx.settings_file.exists():
        default_settings = """# CodeGeass Settings
claude:
  default_model: sonnet
  default_timeout: 300
  unset_api_key: true

paths:
  skills: .claude/skills/
  logs: data/logs/
  sessions: data/sessions/

scheduler:
  check_interval: 60
  max_concurrent: 1
"""
        ctx.settings_file.write_text(default_settings)
        console.print(f"Created: {ctx.settings_file}")

    if not ctx.schedules_file.exists():
        default_schedules = """# CodeGeass Scheduled Tasks
# Add your tasks here

tasks: []
"""
        ctx.schedules_file.write_text(default_schedules)
        console.print(f"Created: {ctx.schedules_file}")

    console.print(
        Panel.fit(
            "[green]CodeGeass initialized successfully![/green]\n\n"
            f"Project directory: {ctx.project_dir}\n"
            f"Config directory: {ctx.config_dir}\n"
            f"Skills directory: {ctx.skills_dir}\n\n"
            "Next steps:\n"
            "1. Create skills in .claude/skills/\n"
            "2. Add tasks with: codegeass task create\n"
            "3. Run scheduler: codegeass scheduler run",
            title="Initialized",
        )
    )


if __name__ == "__main__":
    cli()
