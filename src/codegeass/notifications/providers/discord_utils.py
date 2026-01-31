"""Utility classes and functions for Discord notifications.

This module contains reusable components for building Discord embeds
and processing HTML content for Discord webhooks.
"""

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codegeass.notifications.interactive import InteractiveMessage


class DiscordHtmlFormatter:
    """Convert HTML to Discord Markdown.

    Discord supports a subset of Markdown for formatting messages.
    """

    @staticmethod
    def html_to_discord_markdown(html: str) -> str:
        """Convert HTML to Discord Markdown.

        Args:
            html: HTML string to convert

        Returns:
            Discord Markdown formatted string
        """
        text = html

        # Convert <br> to newlines
        text = re.sub(r"<br\s*/?>", "\n", text)

        # Convert bold tags
        text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)
        text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)

        # Convert italic tags
        text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.DOTALL)
        text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)

        # Convert code tags
        text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)

        # Convert pre blocks to code blocks
        text = re.sub(r"<pre>(.*?)</pre>", r"```\n\1\n```", text, flags=re.DOTALL)

        # Remove any remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


class DiscordEmbedBuilder:
    """Build Discord embed payloads for webhooks.

    Discord embeds support rich formatting including colors, fields,
    and action URLs (but not callback buttons via webhooks).
    """

    # Discord color codes
    COLORS = {
        "primary": 5814783,    # Blue (#58b9ff)
        "success": 5763719,    # Green (#57F287)
        "danger": 15548997,    # Red (#ED4245)
        "warning": 16776960,   # Yellow (#FFFF00)
        "default": 5793266,    # Gray (#586770)
    }

    @staticmethod
    def build_simple_message(message: str, username: str = "CodeGeass") -> dict[str, Any]:
        """Build a simple text message payload.

        Args:
            message: The message text
            username: Username to display

        Returns:
            Discord webhook payload dict
        """
        return {
            "content": message,
            "username": username,
        }

    @staticmethod
    def build_embed_message(
        title: str,
        description: str,
        color: str = "primary",
        username: str = "CodeGeass",
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build an embed message payload.

        Args:
            title: Embed title
            description: Embed description
            color: Color name (primary, success, danger, warning, default)
            username: Username to display
            fields: Optional list of embed fields

        Returns:
            Discord webhook payload dict
        """
        embed: dict[str, Any] = {
            "title": title,
            "description": description,
            "color": DiscordEmbedBuilder.COLORS.get(color, DiscordEmbedBuilder.COLORS["default"]),
        }

        if fields:
            embed["fields"] = fields

        return {
            "username": username,
            "embeds": [embed],
        }

    @staticmethod
    def build_interactive_message(
        message: "InteractiveMessage",
        title: str,
        dashboard_url: str,
        username: str = "CodeGeass",
    ) -> dict[str, Any]:
        """Build an embed with action buttons as URL links.

        Since Discord webhooks don't support callback buttons,
        we convert buttons to clickable links in the embed.

        Args:
            message: The interactive message with buttons
            title: Title for the embed
            dashboard_url: Base URL for the dashboard
            username: Username to display

        Returns:
            Discord webhook payload dict
        """
        # Convert HTML to Discord markdown
        description = DiscordHtmlFormatter.html_to_discord_markdown(message.text)

        # Truncate if too long (Discord limit is 4096 for description)
        max_length = 3800
        if len(description) > max_length:
            description = description[:max_length] + "\n\n*[truncated...]*"

        # Build action links as fields
        fields: list[dict[str, Any]] = []

        # Create action links
        action_links: list[str] = []
        for row in message.button_rows:
            for button in row.buttons:
                action_url = callback_to_dashboard_url(button.callback_data, dashboard_url)
                # Use emoji based on button style
                emoji = _get_button_emoji(button.style.value)
                action_links.append(f"{emoji} **[{button.text}]({action_url})**")

        if action_links:
            fields.append({
                "name": "Actions",
                "value": "\n".join(action_links),
                "inline": False,
            })

        # Determine color based on message type (plan approval = primary)
        color = DiscordEmbedBuilder.COLORS["primary"]

        embed: dict[str, Any] = {
            "title": title,
            "description": description,
            "color": color,
            "fields": fields,
        }

        return {
            "username": username,
            "embeds": [embed],
        }

    @staticmethod
    def build_status_message(
        title: str,
        status: str,
        description: str | None = None,
        color: str = "success",
        username: str = "CodeGeass",
    ) -> dict[str, Any]:
        """Build a status update message.

        Args:
            title: Title for the embed
            status: Status text
            description: Optional additional description
            color: Color name
            username: Username to display

        Returns:
            Discord webhook payload dict
        """
        embed_desc = f"**Status:** {status}"
        if description:
            embed_desc += f"\n\n{description}"

        embed: dict[str, Any] = {
            "title": title,
            "description": embed_desc,
            "color": DiscordEmbedBuilder.COLORS.get(color, DiscordEmbedBuilder.COLORS["default"]),
        }

        return {
            "username": username,
            "embeds": [embed],
        }


def callback_to_dashboard_url(callback_data: str, dashboard_url: str) -> str:
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


def _get_button_emoji(style: str) -> str:
    """Get emoji for button style.

    Args:
        style: Button style name

    Returns:
        Emoji string
    """
    emoji_map = {
        "success": "✅",
        "danger": "❌",
        "warning": "⚠️",
        "primary": "🔵",
        "secondary": "⚪",
    }
    return emoji_map.get(style, "▶️")
