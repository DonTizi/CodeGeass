"""Base scheduler provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SchedulerStatus:
    """Status of the scheduler installation."""

    installed: bool
    running: bool
    scheduler_type: str
    details: str | None = None


@dataclass
class SchedulerConfig:
    """Metadata about a scheduler provider."""

    name: str
    display_name: str
    description: str
    check_command: str
    stop_command: str


class SchedulerProvider(ABC):
    """Abstract base class for scheduler providers.

    Each provider (launchd, systemd, Windows Task Scheduler)
    implements this interface for platform-specific scheduling.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'launchd', 'windows')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this scheduler is available on the system."""
        ...

    @abstractmethod
    def install(
        self, codegeass_path: str, working_dir: Path | None = None
    ) -> tuple[bool, str]:
        """Install the scheduler service.

        Args:
            codegeass_path: Path to the codegeass executable
            working_dir: Optional working directory for the scheduler

        Returns:
            Tuple of (success, message_or_error)
        """
        ...

    @abstractmethod
    def uninstall(self) -> tuple[bool, str]:
        """Uninstall the scheduler service.

        Returns:
            Tuple of (success, message_or_error)
        """
        ...

    @abstractmethod
    def status(self) -> SchedulerStatus:
        """Get current scheduler status.

        Returns:
            SchedulerStatus with installation and running state
        """
        ...

    @abstractmethod
    def get_config(self) -> SchedulerConfig:
        """Get the configuration/metadata for this provider.

        Returns:
            SchedulerConfig with provider information
        """
        ...
