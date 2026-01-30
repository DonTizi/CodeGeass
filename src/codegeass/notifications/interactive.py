"""Interactive notification abstractions for button-based messages.

This module provides cross-platform abstractions for interactive notifications
that support inline buttons (Telegram, Discord, Slack, etc.).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, Self

from codegeass.notifications.models import Channel


class ButtonStyle(str, Enum):
    """Style/color of a button."""

    PRIMARY = "primary"  # Blue/default
    SECONDARY = "secondary"  # Gray
    SUCCESS = "success"  # Green
    DANGER = "danger"  # Red
    WARNING = "warning"  # Yellow/orange


@dataclass
class InlineButton:
    """A button that can be attached to a message.

    Attributes:
        text: Display text on the button
        callback_data: Data sent back when button is clicked (must be unique)
        style: Visual style of the button
        url: Optional URL (makes button a link instead of callback)
    """

    text: str
    callback_data: str
    style: ButtonStyle = ButtonStyle.PRIMARY
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "callback_data": self.callback_data,
            "style": self.style.value,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            text=data["text"],
            callback_data=data["callback_data"],
            style=ButtonStyle(data.get("style", "primary")),
            url=data.get("url"),
        )


@dataclass
class ButtonRow:
    """A row of buttons (displayed horizontally)."""

    buttons: list[InlineButton] = field(default_factory=list)

    def add(self, button: InlineButton) -> None:
        """Add a button to the row."""
        self.buttons.append(button)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"buttons": [b.to_dict() for b in self.buttons]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(buttons=[InlineButton.from_dict(b) for b in data.get("buttons", [])])


@dataclass
class InteractiveMessage:
    """A message with inline buttons.

    The message can have multiple rows of buttons, each row displayed horizontally.
    """

    text: str
    button_rows: list[ButtonRow] = field(default_factory=list)
    parse_mode: str = "HTML"  # "HTML" or "MarkdownV2"

    def add_row(self, *buttons: InlineButton) -> None:
        """Add a row of buttons."""
        row = ButtonRow(buttons=list(buttons))
        self.button_rows.append(row)

    def add_button(self, button: InlineButton, row_index: int = -1) -> None:
        """Add a button to a specific row (or last row if -1)."""
        if not self.button_rows or row_index >= len(self.button_rows):
            self.button_rows.append(ButtonRow())
            row_index = -1
        self.button_rows[row_index].add(button)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "button_rows": [r.to_dict() for r in self.button_rows],
            "parse_mode": self.parse_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create from dictionary."""
        return cls(
            text=data["text"],
            button_rows=[ButtonRow.from_dict(r) for r in data.get("button_rows", [])],
            parse_mode=data.get("parse_mode", "HTML"),
        )


@dataclass
class CallbackQuery:
    """Represents a callback from a button click.

    This is the data received when a user clicks an inline button.
    """

    query_id: str  # Unique ID for this callback (used to answer)
    from_user_id: str
    from_username: str | None
    message_id: int | str
    chat_id: str
    callback_data: str
    provider: str  # "telegram", "discord", etc.

    def parse_action(self) -> tuple[str, str, str]:
        """Parse callback_data into (prefix, action, id).

        Expected format: "plan:approve:abc123"
        Returns: ("plan", "approve", "abc123")
        """
        parts = self.callback_data.split(":", 2)
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return parts[0], parts[1], ""
        else:
            return self.callback_data, "", ""


class InteractiveProvider(Protocol):
    """Protocol for providers that support interactive messages.

    Providers implementing this protocol can send messages with inline buttons
    and handle callback queries from button clicks.
    """

    async def send_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: InteractiveMessage,
    ) -> dict[str, Any]:
        """Send an interactive message with buttons.

        Args:
            channel: The channel to send to
            credentials: Resolved credentials for this channel
            message: The interactive message with buttons

        Returns:
            Dict with 'success', 'message_id', and optionally other data
        """
        ...

    async def edit_interactive(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        message: InteractiveMessage,
    ) -> dict[str, Any]:
        """Edit an existing interactive message.

        Args:
            channel: The channel containing the message
            credentials: Resolved credentials
            message_id: ID of the message to edit
            message: New message content (can have different buttons)

        Returns:
            Dict with 'success' and optionally other data
        """
        ...

    async def remove_buttons(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message_id: int | str,
        new_text: str | None = None,
    ) -> dict[str, Any]:
        """Remove buttons from a message (optionally update text).

        Used after an action is taken to prevent further clicks.

        Args:
            channel: The channel containing the message
            credentials: Resolved credentials
            message_id: ID of the message to edit
            new_text: Optional new text (keeps original if None)

        Returns:
            Dict with 'success'
        """
        ...

    async def answer_callback(
        self,
        credentials: dict[str, str],
        callback_query: CallbackQuery,
        text: str | None = None,
        show_alert: bool = False,
    ) -> bool:
        """Answer a callback query (acknowledge button click).

        Args:
            credentials: Resolved credentials
            callback_query: The callback query to answer
            text: Optional text to show (toast or alert)
            show_alert: If True, show as modal alert instead of toast

        Returns:
            True if answered successfully
        """
        ...


def create_plan_approval_message(
    approval_id: str,
    task_name: str,
    plan_text: str,
    iteration: int = 0,
    max_iterations: int = 5,
) -> InteractiveMessage:
    """Create an interactive message for plan approval.

    Args:
        approval_id: Unique ID for this approval
        task_name: Name of the task
        plan_text: The plan text from Claude
        iteration: Current iteration number
        max_iterations: Maximum allowed iterations

    Returns:
        InteractiveMessage with Approve/Discuss/Cancel buttons
    """
    # Truncate plan if too long (Telegram has 4096 char limit)
    max_plan_length = 3500
    if len(plan_text) > max_plan_length:
        plan_text = plan_text[:max_plan_length] + "\n\n<i>[Plan truncated...]</i>"

    # Build header
    if iteration == 0:
        header = f"<b>Plan Approval Required: {task_name}</b>\n\n"
    else:
        header = f"<b>Updated Plan (iteration {iteration}/{max_iterations}): {task_name}</b>\n\n"

    text = f"{header}<code>{plan_text}</code>"

    # Create message with buttons
    message = InteractiveMessage(text=text, parse_mode="HTML")

    # First row: Approve and Discuss
    approve_btn = InlineButton(
        text="Approve",
        callback_data=f"plan:approve:{approval_id}",
        style=ButtonStyle.SUCCESS,
    )

    if iteration < max_iterations:
        discuss_btn = InlineButton(
            text="Discuss",
            callback_data=f"plan:discuss:{approval_id}",
            style=ButtonStyle.PRIMARY,
        )
        message.add_row(approve_btn, discuss_btn)
    else:
        # No more discuss allowed
        message.add_row(approve_btn)

    # Second row: Cancel
    cancel_btn = InlineButton(
        text="Cancel",
        callback_data=f"plan:cancel:{approval_id}",
        style=ButtonStyle.DANGER,
    )
    message.add_row(cancel_btn)

    return message


def create_approval_status_message(
    task_name: str,
    status: str,
    details: str = "",
) -> str:
    """Create a status message after approval action.

    Args:
        task_name: Name of the task
        status: Status text (e.g., "Approved", "Executing", "Completed")
        details: Additional details

    Returns:
        Formatted HTML message
    """
    message = f"<b>{task_name}</b>\n\n<b>Status:</b> {status}"
    if details:
        message += f"\n\n{details}"

    return message
