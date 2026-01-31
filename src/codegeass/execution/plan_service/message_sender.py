"""Message sending logic for plan approval notifications."""

import logging
from typing import TYPE_CHECKING, Any

from codegeass.execution.plan_approval import PendingApproval
from codegeass.notifications.interactive import InteractiveMessage

if TYPE_CHECKING:
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


class ApprovalMessageSender:
    """Handles sending and updating interactive approval messages."""

    def __init__(self, channel_repo: "ChannelRepository"):
        """Initialize with channel repository."""
        self._channels = channel_repo

    async def send_interactive_to_channel(
        self,
        channel_id: str,
        message: InteractiveMessage,
    ) -> dict[str, Any]:
        """Send interactive message to a specific channel."""
        from codegeass.notifications.registry import get_provider_registry

        channel, credentials = self._channels.get_channel_with_credentials(channel_id)

        if not channel.enabled:
            return {"success": False, "error": "Channel disabled"}

        registry = get_provider_registry()
        provider = registry.get(channel.provider)

        if not hasattr(provider, "send_interactive"):
            logger.warning(f"Provider {channel.provider} does not support interactive messages")
            return {"success": False, "error": "Provider does not support interactive messages"}

        result: dict[str, Any] = await provider.send_interactive(channel, credentials, message)
        result["provider"] = channel.provider

        return result

    async def update_approval_messages(
        self,
        approval: PendingApproval,
        status: str,
        details: str = "",
    ) -> None:
        """Update all notification messages for an approval."""
        from codegeass.notifications.interactive import create_approval_status_message
        from codegeass.notifications.registry import get_provider_registry

        message_text = create_approval_status_message(
            task_name=approval.task_name,
            status=status,
            details=details,
        )

        registry = get_provider_registry()

        for msg_ref in approval.channel_messages:
            try:
                provider = registry.get(msg_ref.provider)
                channel = self._find_channel_by_chat_id(msg_ref.chat_id)

                if not channel:
                    continue

                _, credentials = self._channels.get_channel_with_credentials(channel.id)

                if hasattr(provider, "remove_buttons"):
                    await provider.remove_buttons(
                        channel=channel,
                        credentials=credentials,
                        message_id=msg_ref.message_id,
                        new_text=message_text,
                    )

            except Exception as e:
                logger.warning(f"Failed to update message {msg_ref.message_id}: {e}")

    async def remove_old_message_buttons(self, approval: PendingApproval) -> None:
        """Remove buttons from old messages without changing text."""
        from codegeass.notifications.registry import get_provider_registry

        registry = get_provider_registry()

        for msg_ref in approval.channel_messages:
            try:
                provider = registry.get(msg_ref.provider)
                channel = self._find_channel_by_chat_id(msg_ref.chat_id)

                if not channel:
                    continue

                _, credentials = self._channels.get_channel_with_credentials(channel.id)

                if hasattr(provider, "remove_buttons"):
                    await provider.remove_buttons(
                        channel=channel,
                        credentials=credentials,
                        message_id=msg_ref.message_id,
                    )

            except Exception as e:
                logger.warning(f"Failed to remove buttons from {msg_ref.message_id}: {e}")

    def _find_channel_by_chat_id(self, chat_id: str) -> Any:
        """Find channel by chat_id."""
        all_channels = self._channels.find_all()
        for ch in all_channels:
            if str(ch.config.get("chat_id")) == str(chat_id):
                return ch
        return None

    def get_channel_ids_from_approval(self, approval: PendingApproval) -> list[str]:
        """Get channel IDs from approval message refs."""
        channel_ids = []
        all_channels = self._channels.find_all()

        for msg_ref in approval.channel_messages:
            for ch in all_channels:
                if str(ch.config.get("chat_id")) == str(msg_ref.chat_id):
                    if ch.id not in channel_ids:
                        channel_ids.append(ch.id)
                    break

        return channel_ids
