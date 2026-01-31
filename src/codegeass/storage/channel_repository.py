"""Repository for notification channels."""

import logging
from pathlib import Path

from codegeass.notifications.exceptions import ChannelNotFoundError
from codegeass.notifications.models import Channel, NotificationDefaults
from codegeass.storage.credential_manager import CredentialManager, get_credential_manager
from codegeass.storage.yaml_backend import YAMLBackend, YAMLListBackend

logger = logging.getLogger(__name__)


class ChannelRepository:
    """Repository for managing notification channels.

    Channels are stored in config/notifications.yaml with the following structure:

        channels:
          - id: "abc123"
            name: "DevOps Telegram"
            provider: "telegram"
            enabled: true
            credential_key: "telegram_devops"
            config:
              chat_id: "-1001234567890"
            created_at: "2025-01-29T10:00:00"

        defaults:
          enabled: false
          events: [task_failure]
          include_output: false

    Credentials are stored separately in ~/.codegeass/credentials.yaml.
    """

    def __init__(
        self,
        notifications_file: Path,
        credential_manager: CredentialManager | None = None,
    ):
        self._backend = YAMLListBackend(notifications_file, list_key="channels")
        self._defaults_backend = YAMLBackend(notifications_file)
        self._creds = credential_manager or get_credential_manager()

    def find_all(self) -> list[Channel]:
        """Get all channels."""
        items = self._backend.read_all()
        return [Channel.from_dict(item) for item in items]

    def find_enabled(self) -> list[Channel]:
        """Get all enabled channels."""
        return [ch for ch in self.find_all() if ch.enabled]

    def find_by_id(self, channel_id: str) -> Channel | None:
        """Find a channel by ID."""
        item = self._backend.find_by_key("id", channel_id)
        return Channel.from_dict(item) if item else None

    def find_by_name(self, name: str) -> Channel | None:
        """Find a channel by name."""
        item = self._backend.find_by_key("name", name)
        return Channel.from_dict(item) if item else None

    def find_by_provider(self, provider: str) -> list[Channel]:
        """Find all channels for a provider."""
        return [ch for ch in self.find_all() if ch.provider == provider]

    def save(self, channel: Channel) -> None:
        """Save a channel (create or update)."""
        existing = self._backend.find_by_key("id", channel.id)
        if existing:
            self._backend.update_by_key("id", channel.id, channel.to_dict())
        else:
            self._backend.append(channel.to_dict())

    def delete(self, channel_id: str) -> bool:
        """Delete a channel by ID.

        Note: This does not delete the associated credentials.
        """
        return self._backend.delete_by_key("id", channel_id)

    def enable(self, channel_id: str) -> bool:
        """Enable a channel."""
        channel = self.find_by_id(channel_id)
        if channel:
            channel.enabled = True
            self.save(channel)
            return True
        return False

    def disable(self, channel_id: str) -> bool:
        """Disable a channel."""
        channel = self.find_by_id(channel_id)
        if channel:
            channel.enabled = False
            self.save(channel)
            return True
        return False

    def get_defaults(self) -> NotificationDefaults:
        """Get default notification settings."""
        data = self._defaults_backend.read()
        return NotificationDefaults.from_dict(data.get("defaults"))

    def save_defaults(self, defaults: NotificationDefaults) -> None:
        """Save default notification settings."""
        data = self._defaults_backend.read()
        data["defaults"] = defaults.to_dict()
        self._defaults_backend.write(data)

    def get_channel_with_credentials(self, channel_id: str) -> tuple[Channel, dict[str, str]]:
        """Get a channel with its resolved credentials.

        Args:
            channel_id: Channel ID or name (CLI allows both)

        Returns:
            Tuple of (channel, credentials_dict)

        Raises:
            ChannelNotFoundError: If channel not found
            CredentialError: If credentials not found
        """
        logger.debug(f"Getting channel {channel_id} with credentials")

        # Try by ID first, then by name (CLI allows both)
        channel = self.find_by_id(channel_id)
        if not channel:
            channel = self.find_by_name(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found")
            raise ChannelNotFoundError(channel_id)

        logger.debug(
            f"Found channel: name={channel.name}, provider={channel.provider}, "
            f"credential_key={channel.credential_key}"
        )

        from codegeass.notifications.exceptions import CredentialError

        credentials = self._creds.get(channel.credential_key)
        if not credentials:
            logger.error(f"Credentials not found for key: {channel.credential_key}")
            raise CredentialError(channel.credential_key)

        logger.debug(f"Credentials found with keys: {list(credentials.keys())}")
        return channel, credentials

    def get_credentials_for_channel(self, channel: Channel) -> dict[str, str] | None:
        """Get credentials for a channel.

        Args:
            channel: Channel object

        Returns:
            Credentials dict or None if not found
        """
        return self._creds.get(channel.credential_key)

    def save_credentials(self, credential_key: str, credentials: dict[str, str]) -> None:
        """Save credentials for a channel.

        Args:
            credential_key: Key to store under
            credentials: Credential fields
        """
        self._creds.save(credential_key, credentials)

    def delete_credentials(self, credential_key: str) -> bool:
        """Delete credentials.

        Args:
            credential_key: Key to delete

        Returns:
            True if deleted
        """
        return self._creds.delete(credential_key)


# Global instance
_repository: ChannelRepository | None = None
_notifications_file: Path | None = None


def get_channel_repository(notifications_file: Path | None = None) -> ChannelRepository:
    """Get the channel repository instance.

    Args:
        notifications_file: Path to notifications.yaml. If not provided,
            uses the previously set path or raises an error.

    Returns:
        ChannelRepository instance
    """
    global _repository, _notifications_file

    if notifications_file:
        _notifications_file = notifications_file

    if _repository is None:
        if _notifications_file is None:
            raise ValueError("notifications_file must be provided on first call")
        _repository = ChannelRepository(_notifications_file)

    return _repository


def reset_channel_repository() -> None:
    """Reset the global repository (for testing)."""
    global _repository, _notifications_file
    _repository = None
    _notifications_file = None
