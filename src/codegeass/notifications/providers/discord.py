"""Discord notification provider."""

import re
from typing import Any

from codegeass.notifications.exceptions import ProviderError
from codegeass.notifications.models import Channel
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig


class DiscordProvider(NotificationProvider):
    """Provider for Discord Webhook notifications.

    Requires:
    - webhook_url: Discord webhook URL

    Create a webhook in Discord: Server Settings > Integrations > Webhooks
    """

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
        """Send a message via Discord webhook."""
        try:
            from discord_webhook import AsyncDiscordWebhook
        except ImportError as e:
            raise ProviderError(
                self.name,
                "discord-webhook package not installed. Install with: pip install discord-webhook",
                cause=e,
            )

        webhook_url = credentials["webhook_url"]
        username = channel.config.get("username", kwargs.get("username", "CodeGeass"))
        avatar_url = channel.config.get("avatar_url", kwargs.get("avatar_url"))

        try:
            webhook = AsyncDiscordWebhook(
                url=webhook_url,
                content=message,
                username=username,
                avatar_url=avatar_url,
            )
            response = await webhook.execute()

            # Check for success (2xx status code)
            if response and hasattr(response, "status_code"):
                if 200 <= response.status_code < 300:
                    return {"success": True}
                raise ProviderError(
                    self.name,
                    f"Discord API returned status {response.status_code}",
                )

            return {"success": True}
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
        max_length = 2000
        if len(message) > max_length:
            truncate_notice = "\n...(truncated)"
            message = message[: max_length - len(truncate_notice)] + truncate_notice
        return message
