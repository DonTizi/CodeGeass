"""Shared utility for sending interactive messages to notification channels.

This module provides a reusable function for sending interactive messages
(like plan approval requests) to notification channels, used by both
NotificationHandler and PlanApprovalService.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codegeass.notifications.interactive import InteractiveMessage
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


async def send_interactive_to_channel(
    channel_repo: "ChannelRepository",
    channel_id: str,
    message: "InteractiveMessage",
) -> dict[str, Any]:
    """Send interactive message to a specific channel.

    This is the shared implementation used by NotificationHandler and
    PlanApprovalService for sending interactive messages like plan
    approval requests.

    Args:
        channel_repo: The channel repository for looking up channels
        channel_id: The channel ID to send to
        message: The interactive message with buttons

    Returns:
        Result dict with:
        - 'success': bool indicating if send succeeded
        - 'message_id': ID of sent message (None for providers like Teams)
        - 'chat_id': Chat ID where message was sent
        - 'provider': Name of the provider used
        - 'error': Error message if success is False
    """
    from codegeass.notifications.registry import get_provider_registry

    logger.debug(f"Sending interactive message to channel {channel_id}")

    try:
        # Get channel and credentials
        channel, credentials = channel_repo.get_channel_with_credentials(channel_id)
        logger.debug(
            f"Channel: provider={channel.provider}, enabled={channel.enabled}, "
            f"credentials present={bool(credentials)}"
        )

        if not channel.enabled:
            logger.warning(f"Channel {channel_id} is disabled, skipping")
            return {"success": False, "error": "Channel disabled"}

        # Get provider
        registry = get_provider_registry()
        provider = registry.get(channel.provider)
        logger.debug(
            f"Provider: {provider.name}, "
            f"has send_interactive={hasattr(provider, 'send_interactive')}"
        )

        # Check if provider supports interactive messages
        if not hasattr(provider, "send_interactive"):
            logger.warning(f"Provider {channel.provider} does not support interactive messages")
            return {"success": False, "error": "Provider does not support interactive messages"}

        # Send the message
        logger.debug(f"Calling {provider.name}.send_interactive()")
        result = await provider.send_interactive(channel, credentials, message)
        result["provider"] = channel.provider
        logger.debug(f"send_interactive result: {result}")

        return result

    except Exception as e:
        logger.error(f"Failed to send interactive message to {channel_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
