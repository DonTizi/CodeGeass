"""Discord notification provider.

Supports interactive messages with URL-based action buttons.
Since Discord webhooks don't support callback buttons, actions
link to the Dashboard for approval workflows.
"""

import logging
import re
from typing import TYPE_CHECKING, Any

from codegeass.notifications.exceptions import ProviderError
from codegeass.notifications.models import Channel
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig
from codegeass.notifications.providers.discord_utils import (
    DiscordEmbedBuilder,
    DiscordHtmlFormatter,
)

if TYPE_CHECKING:
    from codegeass.notifications.interactive import InteractiveMessage

logger = logging.getLogger(__name__)


class DiscordProvider(NotificationProvider):
    """Provider for Discord Webhook notifications.

    Requires:
    - webhook_url: Discord webhook URL

    Create a webhook in Discord: Server Settings > Integrations > Webhooks

    Supports:
    - Simple text messages
    - Rich embeds with formatting
    - Interactive messages with URL action buttons (links to Dashboard)
    """

    # Maximum message size for Discord
    MAX_MESSAGE_SIZE = 2000
    MAX_EMBED_DESCRIPTION = 4096

    @property
    def name(self) -> str:
        return "discord"

    @property
    def display_name(self) -> str:
        return "Discord"

    @property
    def description(self) -> str:
        return "Send notifications via Discord Webhooks"

    def get_config_schema(self) -> ProviderConfig:
        return ProviderConfig(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            required_credentials=[
                {
                    "name": "webhook_url",
                    "description": "Discord webhook URL (from Server Settings > Integrations)",
                    "sensitive": True,
                },
            ],
            required_config=[],  # No non-secret config required
            optional_config=[
                {
                    "name": "username",
                    "description": "Override the webhook's default username",
                    "default": "CodeGeass",
                },
                {
                    "name": "avatar_url",
                    "description": "Override the webhook's default avatar",
                    "default": None,
                },
                {
                    "name": "dashboard_url",
                    "description": "Dashboard URL for approval links (default: http://localhost:5173)",
                    "default": "http://localhost:5173",
                },
            ],
        )

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate channel configuration."""
        # No required config fields for Discord (webhook_url is a credential)
        return True, None

    def validate_credentials(self, credentials: dict[str, str]) -> tuple[bool, str | None]:
        """Validate credentials."""
        webhook_url = credentials.get("webhook_url")
        if not webhook_url:
            return False, "webhook_url is required"

        # Validate Discord webhook URL format
        pattern = r"^https://discord\.com/api/webhooks/\d+/[\w-]+$"
        if not re.match(pattern, webhook_url):
            return False, (
                "Invalid webhook URL format. "
                "Expected: https://discord.com/api/webhooks/{id}/{token}"
            )

        return True, None

    async def send(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a message via Discord webhook using embeds for better formatting."""
        try:
            import httpx
        except ImportError as e:
            raise ProviderError(
                self.name,
                "httpx package not installed. Install with: pip install httpx",
                cause=e,
            )

        webhook_url = credentials["webhook_url"]
        username = channel.config.get("username", kwargs.get("username", "CodeGeass"))

        # Convert HTML to Discord markdown
        formatted_message = DiscordHtmlFormatter.html_to_discord_markdown(message)

        # Truncate if needed
        if len(formatted_message) > self.MAX_EMBED_DESCRIPTION:
            truncate_notice = "\n\n*...(truncated)*"
            formatted_message = (
                formatted_message[: self.MAX_EMBED_DESCRIPTION - len(truncate_notice)]
                + truncate_notice
            )

        # Determine color based on message content
        color = DiscordEmbedBuilder.COLORS["primary"]
        if "SUCCESS" in message or "success" in message.lower() or "✅" in message:
            color = DiscordEmbedBuilder.COLORS["success"]
        elif "FAILURE" in message or "failed" in message.lower() or "error" in message.lower():
            color = DiscordEmbedBuilder.COLORS["danger"]
        elif "Running" in message or "Processing" in message:
            color = DiscordEmbedBuilder.COLORS["warning"]

        # Build embed payload for rich formatting
        payload = {
            "username": username,
            "embeds": [{
                "description": formatted_message,
                "color": color,
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook_url, json=payload)

                if 200 <= response.status_code < 300:
                    return {"success": True}
                raise ProviderError(
                    self.name,
                    f"Discord API returned status {response.status_code}: {response.text}",
                )
        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(self.name, f"Failed to send message: {e}", cause=e)

    async def test_connection(
        self,
        channel: Channel,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Test the Discord webhook connection."""
        try:
            from discord_webhook import AsyncDiscordWebhook
        except ImportError:
            return False, "discord-webhook package not installed"

        # Validate credentials first
        valid, error = self.validate_credentials(credentials)
        if not valid:
            return False, error or "Invalid credentials"

        try:
            # Send a test message
            webhook = AsyncDiscordWebhook(
                url=credentials["webhook_url"],
                content="CodeGeass connection test",
                username=channel.config.get("username", "CodeGeass"),
            )
            response = await webhook.execute()

            if response and hasattr(response, "status_code"):
                if 200 <= response.status_code < 300:
                    return True, "Connected! Test message sent successfully."
                return False, f"Discord API returned status {response.status_code}"

            return True, "Connected!"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def format_message(self, message: str, **kwargs: Any) -> str:
        """Format message for Discord.

        Discord supports Markdown formatting natively.
        We limit message length to Discord's 2000 character limit.
        """
        max_length = self.MAX_MESSAGE_SIZE
        if len(message) > max_length:
            truncate_notice = "\n...(truncated)"
            message = message[: max_length - len(truncate_notice)] + truncate_notice
        return message

    # =========================================================================
    # Interactive Messages (Plan Approval)
    # =========================================================================
    # Discord webhooks don't support callback buttons, so we use URL links
    # that point to the Dashboard for approval actions.
    # This is the same approach used for Teams.
    # =========================================================================

    async def send_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: "InteractiveMessage",
    ) -> dict[str, Any]:
        """Send an interactive message with action buttons as URL links.

        Since Discord webhooks don't support callbacks, we convert
        buttons to clickable links in an embed pointing to the Dashboard.

        Args:
            channel: The channel to send to
            credentials: Resolved credentials for this channel
            message: The interactive message with buttons

        Returns:
            Dict with 'success' and 'message_id' (None for Discord webhooks)
        """
        logger.debug("DiscordProvider.send_interactive called")

        try:
            import httpx
        except ImportError as e:
            raise ProviderError(
                self.name,
                "httpx package not installed. Install with: pip install httpx",
                cause=e,
            )

        webhook_url = credentials["webhook_url"]
        username = channel.config.get("username", "CodeGeass")
        dashboard_url = channel.config.get("dashboard_url", "http://localhost:5173")

        try:
            # Build embed with action links
            payload = DiscordEmbedBuilder.build_interactive_message(
                message, "Plan Approval Required", dashboard_url, username
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook_url, json=payload)
                logger.debug(f"Discord response: status={response.status_code}")

                if response.status_code < 200 or response.status_code >= 300:
                    raise ProviderError(
                        self.name,
                        f"Discord API error: {response.status_code} - {response.text}",
                    )

            logger.debug("Discord send_interactive succeeded")
            return {
                "success": True,
                "message_id": None,  # Discord webhooks don't return message IDs
                "chat_id": None,
            }
        except Exception as e:
            logger.error(f"Discord send_interactive failed: {e}", exc_info=True)
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(
                self.name, f"Failed to send interactive message: {e}", cause=e
            )

    async def edit_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        message: "InteractiveMessage",
    ) -> dict[str, Any]:
        """Edit an existing interactive message.

        Note: Discord webhooks don't support editing messages.
        This method sends a new message instead.
        """
        # Discord webhooks don't support editing, send new message
        return await self.send_interactive(channel, credentials, message)

    async def remove_buttons(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        new_text: str | None = None,
    ) -> dict[str, Any]:
        """Remove buttons from a message.

        Note: Discord webhooks don't support editing messages.
        This method sends a new message with the updated text if provided.
        """
        if new_text:
            return await self.send(channel, credentials, new_text)
        return {"success": True}  # Nothing to do
