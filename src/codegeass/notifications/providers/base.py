"""Base notification provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from codegeass.notifications.models import Channel


@dataclass
class ProviderConfig:
    """Metadata about a provider's configuration requirements."""

    name: str
    display_name: str
    description: str
    required_credentials: list[dict[str, str]]  # [{"name": "bot_token", "description": "..."}]
    required_config: list[dict[str, str]]  # Non-secret config fields
    optional_config: list[dict[str, str]] = None  # Optional config fields

    def __post_init__(self) -> None:
        if self.optional_config is None:
            self.optional_config = []


class NotificationProvider(ABC):
    """Abstract base class for notification providers.

    Each provider (Telegram, Discord, etc.) implements this interface
    to provide platform-specific notification capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'telegram', 'discord')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the provider."""
        pass

    @abstractmethod
    async def send(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a notification message.

        Args:
            channel: The channel to send to
            credentials: Resolved credentials for this channel
            message: The message to send
            **kwargs: Provider-specific options (e.g., parse_mode, message_id for editing)

        Returns:
            Dict with 'success' bool and optional 'message_id' for editing later
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate channel configuration.

        Args:
            config: The channel's config dict (non-secret fields)

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def validate_credentials(self, credentials: dict[str, str]) -> tuple[bool, str | None]:
        """Validate credentials.

        Args:
            credentials: The credentials dict

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    async def test_connection(
        self,
        channel: Channel,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Test the connection to the notification service.

        Args:
            channel: The channel to test
            credentials: Resolved credentials

        Returns:
            Tuple of (success, message)
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> ProviderConfig:
        """Get the configuration schema for this provider.

        Returns:
            ProviderConfig with required fields information
        """
        pass

    def format_message(self, message: str, **kwargs: Any) -> str:
        """Format a message for this provider.

        Override to apply provider-specific formatting (e.g., Markdown escaping).

        Args:
            message: Raw message
            **kwargs: Additional context

        Returns:
            Formatted message
        """
        return message
