"""Notification service for orchestrating notifications."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from codegeass.notifications.exceptions import (
    ChannelNotFoundError,
    CredentialError,
    ProviderError,
)
from codegeass.notifications.formatter import MessageFormatter, get_message_formatter
from codegeass.notifications.models import Channel, NotificationConfig, NotificationEvent
from codegeass.notifications.registry import ProviderRegistry, get_provider_registry
from codegeass.storage.channel_repository import ChannelRepository

if TYPE_CHECKING:
    from codegeass.core.entities import Task
    from codegeass.core.value_objects import ExecutionResult

logger = logging.getLogger(__name__)


class NotificationService:
    """Main service for sending notifications.

    Orchestrates the flow of notifications from events to providers:
    1. Receives notification requests with event, task, and result
    2. Determines which channels to notify based on task config
    3. Formats messages using MessageFormatter
    4. Sends via appropriate providers
    """

    def __init__(
        self,
        channel_repo: ChannelRepository,
        registry: ProviderRegistry | None = None,
        formatter: MessageFormatter | None = None,
    ):
        self._channels = channel_repo
        self._registry = registry or get_provider_registry()
        self._formatter = formatter or get_message_formatter()
        # Track message IDs for editing: {task_id: {channel_id: message_id}}
        self._message_ids: dict[str, dict[str, int]] = {}

    async def notify(
        self,
        event: NotificationEvent,
        task: "Task",
        result: "ExecutionResult | None" = None,
        notification_config: NotificationConfig | None = None,
    ) -> dict[str, bool]:
        """Send notifications for an event.

        Args:
            event: The event that occurred
            task: The task that triggered the event
            result: Execution result (for completion events)
            notification_config: Override notification config (uses task.notifications if None)

        Returns:
            Dict mapping channel_id to success status
        """
        # Get notification config from task if not provided
        if notification_config is None:
            notification_config = NotificationConfig.from_dict(getattr(task, "notifications", None))

        # If no config or no channels, nothing to do
        if not notification_config or not notification_config.channels:
            return {}

        # Check if we should notify for this event
        if not notification_config.should_notify(event):
            return {}

        # Send to all configured channels in parallel
        tasks = []
        for channel_id in notification_config.channels:
            tasks.append(
                self._send_to_channel(
                    channel_id=channel_id,
                    event=event,
                    task=task,
                    result=result,
                    include_output=notification_config.include_output,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dict
        outcome: dict[str, bool] = {}
        for channel_id, send_result in zip(notification_config.channels, results):
            if isinstance(send_result, Exception):
                logger.error(f"Failed to notify channel {channel_id}: {send_result}")
                outcome[channel_id] = False
            else:
                outcome[channel_id] = send_result

        return outcome

    async def _send_to_channel(
        self,
        channel_id: str,
        event: NotificationEvent,
        task: "Task",
        result: "ExecutionResult | None",
        include_output: bool,
    ) -> bool:
        """Send notification to a single channel."""
        try:
            # Get channel and credentials
            channel, credentials = self._channels.get_channel_with_credentials(channel_id)

            if not channel.enabled:
                logger.debug(f"Channel {channel_id} is disabled, skipping")
                return False

            # Get provider
            provider = self._registry.get(channel.provider)

            # Format message for this provider
            message = self._formatter.format_for_provider(
                provider=channel.provider,
                event=event,
                task=task,
                result=result,
                include_output=include_output,
            )

            # Check if we should edit an existing message
            message_id = None
            if task.id in self._message_ids and channel_id in self._message_ids[task.id]:
                message_id = self._message_ids[task.id][channel_id]

            # Send or edit
            send_result = await provider.send(channel, credentials, message, message_id=message_id)

            # Store message ID for future edits
            if send_result.get("message_id"):
                if task.id not in self._message_ids:
                    self._message_ids[task.id] = {}
                self._message_ids[task.id][channel_id] = send_result["message_id"]

            # Clean up message IDs on completion events
            if event in (
                NotificationEvent.TASK_SUCCESS,
                NotificationEvent.TASK_FAILURE,
                NotificationEvent.TASK_COMPLETE,
            ):
                if task.id in self._message_ids:
                    self._message_ids.pop(task.id, None)

            return send_result.get("success", False)

        except ChannelNotFoundError:
            logger.error(f"Channel not found: {channel_id}")
            return False
        except CredentialError as e:
            logger.error(f"Credentials missing for channel {channel_id}: {e}")
            return False
        except ProviderError as e:
            logger.error(f"Provider error for channel {channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to channel {channel_id}: {e}")
            return False

    async def test_channel(self, channel_id: str) -> tuple[bool, str]:
        """Test a notification channel.

        Args:
            channel_id: Channel ID to test

        Returns:
            Tuple of (success, message)
        """
        try:
            channel, credentials = self._channels.get_channel_with_credentials(channel_id)
            provider = self._registry.get(channel.provider)
            return await provider.test_connection(channel, credentials)

        except ChannelNotFoundError:
            return False, f"Channel not found: {channel_id}"
        except CredentialError as e:
            return False, f"Credentials not found: {e.credential_key}"
        except Exception as e:
            return False, f"Error: {e}"

    async def send_test_message(
        self,
        channel_id: str,
        message: str = "Test notification from CodeGeass!",
    ) -> bool:
        """Send a test message to a channel.

        Args:
            channel_id: Channel ID
            message: Test message

        Returns:
            True if sent successfully
        """
        try:
            channel, credentials = self._channels.get_channel_with_credentials(channel_id)
            provider = self._registry.get(channel.provider)
            formatted = provider.format_message(message)
            result = await provider.send(channel, credentials, formatted)
            return result.get("success", False)

        except (ChannelNotFoundError, CredentialError, ProviderError) as e:
            logger.error(f"Failed to send test message: {e}")
            return False

    def list_channels(self) -> list[Channel]:
        """List all configured channels."""
        return self._channels.find_all()

    def get_channel(self, channel_id: str) -> Channel | None:
        """Get a channel by ID."""
        return self._channels.find_by_id(channel_id)

    def create_channel(
        self,
        name: str,
        provider: str,
        credential_key: str,
        credentials: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> Channel:
        """Create a new notification channel.

        Args:
            name: Display name for the channel
            provider: Provider name (e.g., 'telegram')
            credential_key: Key for storing credentials
            credentials: Credential fields
            config: Non-secret configuration

        Returns:
            Created channel

        Raises:
            ProviderNotFoundError: If provider is not available
            ChannelConfigError: If config is invalid
        """
        from codegeass.notifications.exceptions import ChannelConfigError

        # Validate provider exists
        provider_impl = self._registry.get(provider)

        # Validate credentials
        valid, error = provider_impl.validate_credentials(credentials)
        if not valid:
            raise ChannelConfigError("new", error or "Invalid credentials")

        # Validate config
        valid, error = provider_impl.validate_config(config or {})
        if not valid:
            raise ChannelConfigError("new", error or "Invalid config")

        # Save credentials
        self._channels.save_credentials(credential_key, credentials)

        # Create and save channel
        channel = Channel.create(
            name=name,
            provider=provider,
            credential_key=credential_key,
            config=config,
        )
        self._channels.save(channel)

        return channel

    def delete_channel(self, channel_id: str, delete_credentials: bool = True) -> bool:
        """Delete a notification channel.

        Args:
            channel_id: Channel ID
            delete_credentials: Whether to also delete associated credentials

        Returns:
            True if deleted
        """
        channel = self._channels.find_by_id(channel_id)
        if not channel:
            return False

        if delete_credentials:
            self._channels.delete_credentials(channel.credential_key)

        return self._channels.delete(channel_id)

    def enable_channel(self, channel_id: str) -> bool:
        """Enable a channel."""
        return self._channels.enable(channel_id)

    def disable_channel(self, channel_id: str) -> bool:
        """Disable a channel."""
        return self._channels.disable(channel_id)


# Global service instance
_service: NotificationService | None = None


def get_notification_service(channel_repo: ChannelRepository | None = None) -> NotificationService:
    """Get the notification service instance.

    Args:
        channel_repo: Channel repository. Required on first call.

    Returns:
        NotificationService instance
    """
    global _service

    if _service is None:
        if channel_repo is None:
            raise ValueError("channel_repo must be provided on first call")
        _service = NotificationService(channel_repo)

    return _service


def reset_notification_service() -> None:
    """Reset the global service (for testing)."""
    global _service
    _service = None
