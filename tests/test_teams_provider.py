"""Tests for Microsoft Teams notification provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests if httpx is not installed
pytest.importorskip("httpx")

from codegeass.notifications.providers.teams import TeamsProvider
from codegeass.notifications.providers.teams_utils import (
    TeamsAdaptiveCardBuilder,
    TeamsHtmlFormatter,
    callback_to_dashboard_url,
)
from codegeass.notifications.models import Channel
from codegeass.notifications.exceptions import ProviderError


class TestTeamsProvider:
    """Tests for TeamsProvider."""

    @pytest.fixture
    def provider(self):
        """Create a TeamsProvider instance."""
        return TeamsProvider()

    @pytest.fixture
    def channel(self):
        """Create a test Channel."""
        return Channel(
            id="test123",
            name="Test Teams Channel",
            provider="teams",
            credential_key="teams_test",
            config={},
            enabled=True,
            created_at="2025-01-01T00:00:00",
        )

    @pytest.fixture
    def valid_credentials_legacy(self):
        """Valid legacy Teams webhook credentials (O365 Connectors)."""
        return {
            "webhook_url": "https://company.webhook.office.com/webhookb2/abc123-def456/IncomingWebhook/xyz789"
        }

    @pytest.fixture
    def valid_credentials_logic_azure(self):
        """Valid Power Automate Logic Apps webhook credentials."""
        return {
            "webhook_url": "https://prod-42.westus.logic.azure.com:443/workflows/abc123def456/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun"
        }

    @pytest.fixture
    def valid_credentials_powerplatform(self):
        """Valid Power Platform webhook credentials."""
        return {
            "webhook_url": "https://default123abc.westus.api.powerplatform.com:443/workflows/xyz789/triggers/manual/paths/invoke"
        }

    # Property tests
    def test_name_property(self, provider):
        """Test that name property returns 'teams'."""
        assert provider.name == "teams"

    def test_display_name_property(self, provider):
        """Test that display_name returns 'Microsoft Teams'."""
        assert provider.display_name == "Microsoft Teams"

    def test_description_property(self, provider):
        """Test that description is set."""
        assert "Teams" in provider.description
        assert "Webhook" in provider.description

    # Config schema tests
    def test_get_config_schema(self, provider):
        """Test that config schema is properly defined."""
        schema = provider.get_config_schema()
        assert schema.name == "teams"
        assert schema.display_name == "Microsoft Teams"
        assert len(schema.required_credentials) == 1
        assert schema.required_credentials[0]["name"] == "webhook_url"
        assert len(schema.required_config) == 0  # No required config

    # Validation tests
    def test_validate_config_empty(self, provider):
        """Test that empty config is valid (no required fields)."""
        valid, error = provider.validate_config({})
        assert valid is True
        assert error is None

    def test_validate_credentials_legacy_url(self, provider, valid_credentials_legacy):
        """Test validation of legacy O365 Connector webhook URL."""
        valid, error = provider.validate_credentials(valid_credentials_legacy)
        assert valid is True
        assert error is None

    def test_validate_credentials_logic_azure_url(self, provider, valid_credentials_logic_azure):
        """Test validation of Power Automate Logic Apps webhook URL."""
        valid, error = provider.validate_credentials(valid_credentials_logic_azure)
        assert valid is True
        assert error is None

    def test_validate_credentials_powerplatform_url(self, provider, valid_credentials_powerplatform):
        """Test validation of Power Platform webhook URL."""
        valid, error = provider.validate_credentials(valid_credentials_powerplatform)
        assert valid is True
        assert error is None

    def test_validate_credentials_missing_webhook_url(self, provider):
        """Test that missing webhook_url fails validation."""
        valid, error = provider.validate_credentials({})
        assert valid is False
        assert "webhook_url is required" in error

    def test_validate_credentials_invalid_url_format(self, provider):
        """Test that invalid URL format fails validation."""
        invalid_urls = [
            {"webhook_url": "https://example.com/webhook"},
            {"webhook_url": "https://hooks.slack.com/services/xxx"},
            {"webhook_url": "https://discord.com/api/webhooks/123/abc"},
            {"webhook_url": "not-a-url"},
            {"webhook_url": "http://company.webhook.office.com/webhookb2/abc"},  # http not https
            {"webhook_url": "http://prod-42.logic.azure.com/workflows/abc"},  # http not https
        ]
        for creds in invalid_urls:
            valid, error = provider.validate_credentials(creds)
            assert valid is False, f"Should reject: {creds['webhook_url']}"
            assert "Invalid webhook URL format" in error

    def test_validate_credentials_various_valid_formats(self, provider):
        """Test that various valid Teams webhook URL formats are accepted."""
        valid_urls = [
            # Legacy O365 Connectors
            "https://company.webhook.office.com/webhookb2/abc123/IncomingWebhook/xyz",
            "https://my-org.webhook.office.com/webhookb2/guid-here-abc-123/IncomingWebhook/token123",
            "https://contoso.webhook.office.com/webhookb2/a1b2c3d4-e5f6-7890-abcd-ef1234567890/IncomingWebhook/abcdef123456",
            # Power Automate Logic Apps
            "https://prod-42.westus.logic.azure.com:443/workflows/abc123/triggers/manual/paths/invoke",
            "https://prod-123.eastus2.logic.azure.com/workflows/xyz789def456/triggers/manual/paths/invoke?api-version=2016-06-01",
            "https://prod-00.northeurope.logic.azure.com:443/workflows/workflow-id-here/triggers/manual/paths/invoke",
            # Power Platform
            "https://default123.westus.api.powerplatform.com:443/workflows/abc/triggers/manual",
            "https://org-env.eastus.api.powerplatform.com/workflows/workflow123/triggers/manual/paths/invoke",
        ]
        for url in valid_urls:
            valid, error = provider.validate_credentials({"webhook_url": url})
            assert valid is True, f"Should accept: {url}, got error: {error}"

    # Format message tests
    def test_format_message_short(self, provider):
        """Test formatting a short message."""
        message = "Hello Teams!"
        formatted = provider.format_message(message)
        assert formatted == message

    def test_format_message_truncation(self, provider):
        """Test that long messages are truncated to 28KB limit."""
        # Create a message larger than 28KB
        long_message = "x" * 30000
        formatted = provider.format_message(long_message)
        assert len(formatted) <= provider.MAX_MESSAGE_SIZE
        assert formatted.endswith("...(truncated)")

    def test_format_message_at_limit(self, provider):
        """Test message exactly at the limit is not truncated."""
        message = "x" * (provider.MAX_MESSAGE_SIZE - 100)
        formatted = provider.format_message(message)
        assert formatted == message
        assert "truncated" not in formatted

    # Adaptive Card payload tests (using TeamsAdaptiveCardBuilder utility)
    def test_build_adaptive_card_payload_with_title(self, provider):
        """Test Adaptive Card payload generation with title."""
        payload = TeamsAdaptiveCardBuilder.build_simple_card("Test message", "Test Title")

        assert payload["type"] == "message"
        assert len(payload["attachments"]) == 1
        attachment = payload["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert attachment["contentUrl"] is None  # Required for Workflows webhooks

        content = attachment["content"]
        assert content["type"] == "AdaptiveCard"
        assert content["version"] == "1.4"
        assert len(content["body"]) == 2  # Title + message

        # Check title block
        assert content["body"][0]["text"] == "Test Title"
        assert content["body"][0]["weight"] == "Bolder"

        # Check message block
        assert content["body"][1]["text"] == "Test message"
        assert content["body"][1]["wrap"] is True

    def test_build_adaptive_card_payload_without_title(self, provider):
        """Test Adaptive Card payload generation without title."""
        payload = TeamsAdaptiveCardBuilder.build_simple_card("Test message", None)

        content = payload["attachments"][0]["content"]
        assert len(content["body"]) == 1  # Only message, no title
        assert content["body"][0]["text"] == "Test message"

    # Send tests with mocking
    @pytest.mark.asyncio
    async def test_send_success(self, provider, channel, valid_credentials_logic_azure):
        """Test successful message sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.send(channel, valid_credentials_logic_azure, "Test message")

            assert result["success"] is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == valid_credentials_logic_azure["webhook_url"]
            # Verify payload is an Adaptive Card
            payload = call_args[1]["json"]
            assert payload["type"] == "message"
            assert "attachments" in payload

    @pytest.mark.asyncio
    async def test_send_with_title(self, provider, valid_credentials_logic_azure):
        """Test sending with custom title."""
        channel = Channel(
            id="test123",
            name="Test",
            provider="teams",
            credential_key="test",
            config={"title": "Custom Title"},
            enabled=True,
            created_at="2025-01-01T00:00:00",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await provider.send(channel, valid_credentials_logic_azure, "Test message")

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            # Check title is in the Adaptive Card body
            body = payload["attachments"][0]["content"]["body"]
            assert body[0]["text"] == "Custom Title"

    @pytest.mark.asyncio
    async def test_send_import_error(self, provider, channel, valid_credentials_logic_azure):
        """Test that ProviderError is raised when httpx request fails."""
        # Since httpx is imported at module level, we test connection error instead
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("codegeass.notifications.providers.teams.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ProviderError) as exc_info:
                await provider.send(channel, valid_credentials_logic_azure, "Test message")

            assert "Failed to send message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_http_error(self, provider, channel, valid_credentials_logic_azure):
        """Test handling of HTTP errors during send."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ProviderError) as exc_info:
                await provider.send(channel, valid_credentials_logic_azure, "Test message")

            assert "Teams API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_general_error(self, provider, channel, valid_credentials_logic_azure):
        """Test handling of general errors during send."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ProviderError) as exc_info:
                await provider.send(channel, valid_credentials_logic_azure, "Test message")

            assert "Failed to send message" in str(exc_info.value)

    # Test connection tests
    @pytest.mark.asyncio
    async def test_test_connection_success(self, provider, channel, valid_credentials_logic_azure):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            success, message = await provider.test_connection(
                channel, valid_credentials_logic_azure
            )

            assert success is True
            assert "Connected" in message
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_invalid_credentials(self, provider, channel):
        """Test connection test with invalid credentials."""
        success, message = await provider.test_connection(channel, {})
        assert success is False
        assert "webhook_url is required" in message

    @pytest.mark.asyncio
    async def test_test_connection_http_error(self, provider, channel, valid_credentials_logic_azure):
        """Test connection test handling HTTP errors."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            success, message = await provider.test_connection(
                channel, valid_credentials_logic_azure
            )

            assert success is False
            assert "Connection failed" in message
            assert "401" in message

    @pytest.mark.asyncio
    async def test_test_connection_general_error(
        self, provider, channel, valid_credentials_logic_azure
    ):
        """Test connection test handling general errors."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            success, message = await provider.test_connection(
                channel, valid_credentials_logic_azure
            )

            assert success is False
            assert "Connection failed" in message


class TestTeamsInteractive:
    """Tests for Teams interactive messages (plan approval)."""

    @pytest.fixture
    def provider(self):
        """Create a TeamsProvider instance."""
        return TeamsProvider()

    @pytest.fixture
    def channel_with_dashboard(self):
        """Create a test Channel with dashboard_url config."""
        return Channel(
            id="test123",
            name="Test Teams Channel",
            provider="teams",
            credential_key="teams_test",
            config={"dashboard_url": "http://localhost:5173"},
            enabled=True,
            created_at="2025-01-01T00:00:00",
        )

    @pytest.fixture
    def valid_credentials(self):
        """Valid Teams webhook credentials."""
        return {
            "webhook_url": "https://prod-42.westus.logic.azure.com:443/workflows/abc123/triggers/manual"
        }

    @pytest.fixture
    def interactive_message(self):
        """Create an interactive message with buttons."""
        from codegeass.notifications.interactive import (
            InteractiveMessage,
            InlineButton,
            ButtonStyle,
        )

        message = InteractiveMessage(
            text="<b>Plan Approval Required</b>\n\nThis is the plan text.",
            parse_mode="HTML",
        )
        message.add_row(
            InlineButton("Approve", "plan:approve:abc123", ButtonStyle.SUCCESS),
            InlineButton("Discuss", "plan:discuss:abc123", ButtonStyle.PRIMARY),
        )
        message.add_row(
            InlineButton("Cancel", "plan:cancel:abc123", ButtonStyle.DANGER),
        )
        return message

    def test_callback_to_dashboard_url_approve(self, provider):
        """Test converting approve callback to dashboard URL."""
        url = callback_to_dashboard_url(
            "plan:approve:abc123", "http://localhost:5173"
        )
        assert url == "http://localhost:5173/approvals/abc123?action=approve"

    def test_callback_to_dashboard_url_discuss(self, provider):
        """Test converting discuss callback to dashboard URL."""
        url = callback_to_dashboard_url(
            "plan:discuss:xyz789", "http://mydashboard.local:8080"
        )
        assert url == "http://mydashboard.local:8080/approvals/xyz789?action=discuss"

    def test_callback_to_dashboard_url_cancel(self, provider):
        """Test converting cancel callback to dashboard URL."""
        url = callback_to_dashboard_url(
            "plan:cancel:test123", "http://localhost:5173"
        )
        assert url == "http://localhost:5173/approvals/test123?action=cancel"

    def test_callback_to_dashboard_url_fallback(self, provider):
        """Test fallback for unknown callback format."""
        url = callback_to_dashboard_url(
            "unknown:data", "http://localhost:5173"
        )
        assert url == "http://localhost:5173/approvals"

    def test_html_to_plain_text(self, provider):
        """Test HTML to plain text conversion (strips formatting tags)."""
        html = "<b>Bold</b> and <i>italic</i> with <code>code</code>"
        result = TeamsHtmlFormatter.html_to_plain_text(html)
        # Tags should be stripped, only content remains
        assert "Bold" in result
        assert "italic" in result
        assert "code" in result
        # No HTML tags should remain
        assert "<b>" not in result
        assert "</b>" not in result
        assert "<i>" not in result
        assert "<code>" not in result

    def test_build_interactive_card_payload(self, provider, interactive_message):
        """Test building interactive Adaptive Card payload."""
        payload = TeamsAdaptiveCardBuilder.build_interactive_card(
            interactive_message, "CodeGeass", "http://localhost:5173"
        )

        assert payload["type"] == "message"
        content = payload["attachments"][0]["content"]
        assert content["type"] == "AdaptiveCard"
        assert "actions" in content
        assert len(content["actions"]) == 3  # Approve, Discuss, Cancel

        # Check action URLs
        actions = content["actions"]
        assert actions[0]["type"] == "Action.OpenUrl"
        assert "approve" in actions[0]["url"]
        assert actions[0]["style"] == "positive"

        assert "discuss" in actions[1]["url"]

        assert "cancel" in actions[2]["url"]
        assert actions[2]["style"] == "destructive"

    @pytest.mark.asyncio
    async def test_send_interactive_success(
        self, provider, channel_with_dashboard, valid_credentials, interactive_message
    ):
        """Test sending interactive message."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider.send_interactive(
                channel_with_dashboard, valid_credentials, interactive_message
            )

            assert result["success"] is True
            assert result["message_id"] is None  # Teams webhooks don't return IDs
            mock_client.post.assert_called_once()

            # Verify payload contains actions
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "actions" in payload["attachments"][0]["content"]


class TestTeamsMessageFormatter:
    """Tests for Teams message formatting in MessageFormatter."""

    def test_html_to_teams_markdown(self):
        """Test HTML to Teams Markdown conversion."""
        from codegeass.notifications.formatter import MessageFormatter

        formatter = MessageFormatter()
        html = "<b>Bold</b> and <i>italic</i> with <code>code</code>"
        result = formatter._html_to_teams_markdown(html)

        assert "**Bold**" in result
        assert "_italic_" in result
        assert "`code`" in result

    def test_html_to_teams_markdown_pre_block(self):
        """Test pre block conversion."""
        from codegeass.notifications.formatter import MessageFormatter

        formatter = MessageFormatter()
        html = "<pre>code block\nline 2</pre>"
        result = formatter._html_to_teams_markdown(html)

        assert "```" in result
        assert "code block" in result
