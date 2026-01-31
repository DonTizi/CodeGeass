"""Utility classes and functions for Microsoft Teams notifications.

This module contains reusable components for building Teams Adaptive Cards
and processing HTML content for Teams webhooks.
"""

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codegeass.notifications.interactive import InteractiveMessage


class TeamsHtmlFormatter:
    """Convert HTML to plain text for Teams Adaptive Cards.

    Adaptive Cards TextBlock doesn't support HTML or Markdown by default,
    so we strip all formatting tags and keep just the text content.
    """

    @staticmethod
    def html_to_plain_text(html: str) -> str:
        """Convert HTML to plain text.

        Args:
            html: HTML string to convert

        Returns:
            Plain text with formatting stripped
        """
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


class TeamsAdaptiveCardBuilder:
    """Build Adaptive Card payloads for Teams webhooks.

    This builder creates cards that work with both:
    - Legacy O365 Connectors
    - Power Automate Workflows webhooks
    """

    @staticmethod
    def build_simple_card(message: str, title: str | None = None) -> dict[str, Any]:
        """Build a simple Adaptive Card with text content.

        Args:
            message: The message text (HTML will be converted to plain text)
            title: Optional title for the card

        Returns:
            Adaptive Card payload dict
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

        return TeamsAdaptiveCardBuilder._wrap_in_message(body_elements)

    @staticmethod
    def build_interactive_card(
        message: "InteractiveMessage",
        title: str | None,
        dashboard_url: str,
    ) -> dict[str, Any]:
        """Build an Adaptive Card with interactive buttons as URL links.

        Since Teams Workflows webhooks don't support callbacks, buttons
        are converted to Action.OpenUrl pointing to the Dashboard.

        Args:
            message: The interactive message with buttons
            title: Optional title for the card
            dashboard_url: Base URL for the dashboard

        Returns:
            Adaptive Card payload dict
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
        clean_text = TeamsHtmlFormatter.html_to_plain_text(message.text)
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
                action_url = callback_to_dashboard_url(button.callback_data, dashboard_url)

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

        return TeamsAdaptiveCardBuilder._wrap_in_message(body_elements, actions)

    @staticmethod
    def _wrap_in_message(
        body_elements: list[dict[str, Any]],
        actions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Wrap body elements in the Teams message envelope.

        Args:
            body_elements: The card body elements
            actions: Optional list of card actions

        Returns:
            Complete message payload
        """
        content: dict[str, Any] = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body_elements,
        }

        if actions:
            content["actions"] = actions

        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": content,
            }],
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
