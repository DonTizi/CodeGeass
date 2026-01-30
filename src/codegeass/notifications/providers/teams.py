"""Microsoft Teams notification provider.

Supports both legacy Office 365 Connectors and new Power Automate Workflows webhooks.

References:
- Microsoft retired O365 Connectors (Dec 2025): https://devblogs.microsoft.com/microsoft365dev/retirement-of-office-365-connectors-within-microsoft-teams/
- Create Workflows webhooks: https://support.microsoft.com/en-us/office/create-incoming-webhooks-with-workflows-for-microsoft-teams-8ae491c7-0394-4861-ba59-055e33f75498
"""

import logging
import re
from typing import TYPE_CHECKING, Any

from codegeass.notifications.exceptions import ProviderError
from codegeass.notifications.models import Channel
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig

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
        try:
            import httpx
        except ImportError as e:
            raise ProviderError(
                self.name,
                "httpx package not installed. Install with: pip install httpx",
                cause=e,
            )

        webhook_url = credentials["webhook_url"]
        title = channel.config.get("title", kwargs.get("title", "CodeGeass"))

        try:
            # Convert HTML to Markdown for Teams Adaptive Cards
            clean_message = self._html_to_plain_text(message)

            # Build Adaptive Card payload (works with both legacy and new webhooks)
            payload = self._build_adaptive_card_payload(clean_message, title)

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

    def _build_adaptive_card_payload(self, message: str, title: str | None) -> dict[str, Any]:
        """Build an Adaptive Card payload for Teams webhooks.

        This format works with both:
        - Legacy O365 Connectors
        - Power Automate Workflows webhooks
        """
        body_elements: list[dict[str, Any]] = []

        # Add title as a header if provided
        if title:
            body_elements.append({
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            })

        # Add message content
        body_elements.append({
            "type": "TextBlock",
            "text": message,
            "wrap": True,
        })

        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "type": "AdaptiveCard",
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.4",
                    "body": body_elements,
                },
            }],
        }

    async def test_connection(
        self,
        channel: Channel,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Test the Teams webhook connection."""
        try:
            import httpx
        except ImportError:
            return False, "httpx package not installed"

        # Validate credentials first
        valid, error = self.validate_credentials(credentials)
        if not valid:
            return False, error or "Invalid credentials"

        try:
            # Send a test message using Adaptive Card
            payload = self._build_adaptive_card_payload(
                "✅ Connection test successful!", "CodeGeass"
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
        print("[Teams] send_interactive called")
        logger.info("TeamsProvider.send_interactive called")

        try:
            import httpx
        except ImportError as e:
            print("[Teams] ERROR: httpx not installed")
            logger.error("httpx package not installed")
            raise ProviderError(
                self.name,
                "httpx package not installed. Install with: pip install httpx",
                cause=e,
            )

        webhook_url = credentials["webhook_url"]
        title = channel.config.get("title", "CodeGeass")
        dashboard_url = channel.config.get("dashboard_url", "http://localhost:5173")

        # Log URL prefix for debugging (don't log full URL for security)
        url_prefix = webhook_url[:60] + "..." if len(webhook_url) > 60 else webhook_url
        logger.debug(f"webhook_url: {url_prefix}")
        logger.debug(f"title: {title}, dashboard_url: {dashboard_url}")

        try:
            # Build Adaptive Card with action buttons as links
            payload = self._build_interactive_card_payload(message, title, dashboard_url)
            logger.debug(f"Payload built with {len(payload.get('attachments', []))} attachments")

            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Sending POST request to Teams webhook...")
                response = await client.post(webhook_url, json=payload)

                # Log response details
                logger.info(f"Teams response: status={response.status_code}")
                response_text = response.text[:500] if response.text else "(empty)"
                logger.debug(f"Teams response body: {response_text}")

                response.raise_for_status()

            logger.info("Teams send_interactive succeeded")
            return {
                "success": True,
                "message_id": None,  # Teams webhooks don't return message IDs
                "chat_id": None,
            }
        except Exception as e:
            logger.error(f"Teams send_interactive failed: {e}", exc_info=True)
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(self.name, f"Failed to send interactive message: {e}", cause=e)

    def _build_interactive_card_payload(
        self,
        message: "InteractiveMessage",
        title: str | None,
        dashboard_url: str,
    ) -> dict[str, Any]:
        """Build an Adaptive Card with interactive buttons as URL links.

        Converts callback buttons to Action.OpenUrl pointing to the Dashboard.
        """
        body_elements: list[dict[str, Any]] = []

        # Add title
        if title:
            body_elements.append({
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            })

        # Add message text (convert HTML to plain text for Adaptive Cards)
        clean_text = self._html_to_plain_text(message.text)
        body_elements.append({
            "type": "TextBlock",
            "text": clean_text,
            "wrap": True,
        })

        # Convert buttons to actions
        actions: list[dict[str, Any]] = []
        for row in message.button_rows:
            for button in row.buttons:
                # Parse callback_data to build dashboard URL
                # Format: "plan:approve:abc123" -> /approvals/abc123?action=approve
                action_url = self._callback_to_dashboard_url(
                    button.callback_data, dashboard_url
                )

                # Map button style to Adaptive Card style
                style = "positive" if button.style.value == "success" else (
                    "destructive" if button.style.value == "danger" else "default"
                )

                actions.append({
                    "type": "Action.OpenUrl",
                    "title": button.text,
                    "url": action_url,
                    "style": style,
                })

        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "type": "AdaptiveCard",
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.4",
                    "body": body_elements,
                    "actions": actions,
                },
            }],
        }

    def _callback_to_dashboard_url(self, callback_data: str, dashboard_url: str) -> str:
        """Convert callback_data to a Dashboard URL.

        Args:
            callback_data: Format "plan:action:id" (e.g., "plan:approve:abc123")
            dashboard_url: Base dashboard URL (e.g., "http://localhost:5173")

        Returns:
            Full URL to dashboard approval page
        """
        parts = callback_data.split(":", 2)
        if len(parts) >= 3:
            prefix, action, approval_id = parts
            if prefix == "plan":
                return f"{dashboard_url}/approvals/{approval_id}?action={action}"

        # Fallback: just link to approvals page
        return f"{dashboard_url}/approvals"

    def _html_to_plain_text(self, html: str) -> str:
        """Convert HTML to plain text for Adaptive Cards.

        Adaptive Cards TextBlock doesn't support HTML or Markdown by default,
        so we strip all formatting tags and keep just the text content.
        """
        import re

        text = html

        # Convert <br> to newlines first
        text = re.sub(r"<br\s*/?>", "\n", text)

        # Convert <pre> and <code> blocks - preserve content with newlines
        text = re.sub(r"<pre>(.*?)</pre>", r"\n\1\n", text, flags=re.DOTALL)
        text = re.sub(r"<code>(.*?)</code>", r"\1", text, flags=re.DOTALL)

        # Remove bold/italic tags but keep content
        text = re.sub(r"<b>(.*?)</b>", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"<strong>(.*?)</strong>", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"<i>(.*?)</i>", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"<em>(.*?)</em>", r"\1", text, flags=re.DOTALL)

        # Remove any remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

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
