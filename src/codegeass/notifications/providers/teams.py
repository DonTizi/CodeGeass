"""Microsoft Teams notification provider.

Supports both legacy Office 365 Connectors and new Power Automate Workflows webhooks.

References:
- Microsoft retired O365 Connectors (Dec 2025): https://devblogs.microsoft.com/microsoft365dev/retirement-of-office-365-connectors-within-microsoft-teams/
- Create Workflows webhooks: https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498
"""

import logging
import re
from typing import TYPE_CHECKING, Any

import httpx

from codegeass.notifications.exceptions import ProviderError
from codegeass.notifications.models import Channel
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig
from codegeass.notifications.providers.teams_utils import (
    TeamsAdaptiveCardBuilder,
    TeamsHtmlFormatter,
)

if TYPE_CHECKING:
    from codegeass.notifications.interactive import InteractiveMessage

logger = logging.getLogger(__name__)


class TeamsProvider(NotificationProvider):
    """Provider for Microsoft Teams webhook notifications.

    Supports:
    - Power Automate Workflows (recommended): https://*.logic.azure.com/workflows/...
    - Power Platform workflows: https://*.api.powerplatform.com/workflows/...
    - Legacy O365 Connectors (deprecated): https://*.webhook.office.com/webhookb2/...

    Create a webhook in Teams:
    1. Go to your channel > ⋯ (3 dots) > Workflows
    2. Search for "Post to a channel when a webhook request is received"
    3. Click Add and configure the workflow
    4. Copy the HTTP POST URL
    """

    # Maximum message size for Adaptive Card payload (28 KB)
    MAX_MESSAGE_SIZE = 28000

    @property
    def name(self) -> str:
        return "teams"

    @property
    def display_name(self) -> str:
        return "Microsoft Teams"

    @property
    def description(self) -> str:
        return "Send notifications via Teams Incoming Webhooks"

    def get_config_schema(self) -> ProviderConfig:
        return ProviderConfig(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            required_credentials=[
                {
                    "name": "webhook_url",
                    "description": (
                        "Teams Workflow webhook URL (Channel > Workflows > "
                        "'Post to a channel when a webhook request is received')"
                    ),
                    "sensitive": True,
                },
            ],
            required_config=[],  # No non-secret config required
            optional_config=[
                {
                    "name": "title",
                    "description": "Optional title for message cards",
                    "default": "CodeGeass",
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
        # No required config fields for Teams (webhook_url is a credential)
        return True, None

    # URL patterns for Teams webhooks
    # 1. Power Automate Logic Apps: https://prod-XX.region.logic.azure.com:443/workflows/...
    # 2. Power Platform: https://defaultXXX.XX.environment.api.powerplatform.com:443/...
    # 3. Legacy O365 Connectors (deprecated but still works): https://*.webhook.office.com/webhookb2/...
    WEBHOOK_PATTERNS = [
        r"^https://[\w.-]+\.logic\.azure\.com[:/].*workflows.*$",
        r"^https://[\w.-]+\.api\.powerplatform\.com[:/].*workflows.*$",
        r"^https://[\w-]+\.webhook\.office\.com/webhookb2/.*$",  # Legacy
    ]

    def validate_credentials(self, credentials: dict[str, str]) -> tuple[bool, str | None]:
        """Validate credentials."""
        webhook_url = credentials.get("webhook_url")
        if not webhook_url:
            return False, "webhook_url is required"

        # Check against all valid URL patterns
        for pattern in self.WEBHOOK_PATTERNS:
            if re.match(pattern, webhook_url, re.IGNORECASE):
                return True, None

        return False, (
            "Invalid webhook URL format. Expected one of:\n"
            "  - Power Automate: https://*.logic.azure.com/workflows/...\n"
            "  - Power Platform: https://*.api.powerplatform.com/workflows/...\n"
            "  - Legacy O365: https://*.webhook.office.com/webhookb2/..."
        )

    async def send(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a message via Teams webhook using Adaptive Cards.

        Uses httpx for HTTP POST to support both legacy O365 Connectors
        and new Power Automate Workflows webhooks.
        """
        webhook_url = credentials["webhook_url"]
        title = channel.config.get("title", kwargs.get("title", "CodeGeass"))

        try:
            # Convert HTML to plain text for Teams Adaptive Cards
            clean_message = TeamsHtmlFormatter.html_to_plain_text(message)

            # Build Adaptive Card payload (works with both legacy and new webhooks)
            payload = TeamsAdaptiveCardBuilder.build_simple_card(clean_message, title)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

            return {"success": True}
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                self.name,
                f"Teams API error: {e.response.status_code} - {e.response.text}",
                cause=e,
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
        """Test the Teams webhook connection."""
        # Validate credentials first
        valid, error = self.validate_credentials(credentials)
        if not valid:
            return False, error or "Invalid credentials"

        try:
            # Send a test message using Adaptive Card
            payload = TeamsAdaptiveCardBuilder.build_simple_card(
                "Connection test successful!", "CodeGeass"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(credentials["webhook_url"], json=payload)
                response.raise_for_status()

            return True, "Connected! Test message sent successfully."
        except httpx.HTTPStatusError as e:
            return False, f"Connection failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def format_message(self, message: str, **kwargs: Any) -> str:
        """Format message for Teams.

        Teams supports Markdown formatting natively.
        We limit message length to Teams' 28 KB limit for Adaptive Card payload.
        """
        max_length = self.MAX_MESSAGE_SIZE
        if len(message) > max_length:
            truncate_notice = "\n...(truncated)"
            message = message[: max_length - len(truncate_notice)] + truncate_notice
        return message

    # =========================================================================
    # Interactive Messages (Plan Approval)
    # =========================================================================
    # Teams Workflows webhooks don't support callback buttons, so we use
    # Action.OpenUrl to link to the Dashboard for approval actions.
    # This is the most secure approach - no tunnel/public URL needed.
    # =========================================================================

    async def send_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: "InteractiveMessage",
    ) -> dict[str, Any]:
        """Send an interactive message with action buttons.

        Since Teams Workflows webhooks don't support callbacks, we convert
        buttons to Action.OpenUrl links pointing to the Dashboard.

        Args:
            channel: The channel to send to
            credentials: Resolved credentials for this channel
            message: The interactive message with buttons

        Returns:
            Dict with 'success' and 'message_id' (None for Teams webhooks)
        """
        logger.debug("TeamsProvider.send_interactive called")

        webhook_url = credentials["webhook_url"]
        title = channel.config.get("title", "CodeGeass")
        dashboard_url = channel.config.get("dashboard_url", "http://localhost:5173")

        try:
            # Build Adaptive Card with action buttons as links
            payload = TeamsAdaptiveCardBuilder.build_interactive_card(
                message, title, dashboard_url
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook_url, json=payload)
                logger.debug(f"Teams response: status={response.status_code}")
                response.raise_for_status()

            logger.debug("Teams send_interactive succeeded")
            return {
                "success": True,
                "message_id": None,  # Teams webhooks don't return message IDs
                "chat_id": None,
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Teams send_interactive failed: {e.response.status_code}")
            raise ProviderError(
                self.name,
                f"Teams API error: {e.response.status_code} - {e.response.text}",
                cause=e,
            )
        except Exception as e:
            logger.error(f"Teams send_interactive failed: {e}", exc_info=True)
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(self.name, f"Failed to send interactive message: {e}", cause=e)

    async def edit_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        message: "InteractiveMessage",
    ) -> dict[str, Any]:
        """Edit an existing interactive message.

        Note: Teams Workflows webhooks don't support editing messages.
        This method sends a new message instead.
        """
        # Teams webhooks don't support editing, send new message
        return await self.send_interactive(channel, credentials, message)

    async def remove_buttons(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        new_text: str | None = None,
    ) -> dict[str, Any]:
        """Remove buttons from a message.

        Note: Teams Workflows webhooks don't support editing messages.
        This method sends a new message with the updated text if provided.
        """
        if new_text:
            return await self.send(channel, credentials, new_text)
        return {"success": True}  # Nothing to do
