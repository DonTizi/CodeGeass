"""Telegram notification provider."""

import re
from typing import Any

from codegeass.notifications.exceptions import ProviderError
from codegeass.notifications.models import Channel
from codegeass.notifications.providers.base import NotificationProvider, ProviderConfig


class TelegramProvider(NotificationProvider):
    """Provider for Telegram Bot API notifications.

    Requires:
    - bot_token: Token from @BotFather
    - chat_id: Target chat/group/channel ID

    The bot must be added to the chat and have permission to send messages.
    """

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def display_name(self) -> str:
        return "Telegram"

    @property
    def description(self) -> str:
        return "Send notifications via Telegram Bot API"

    def get_config_schema(self) -> ProviderConfig:
        return ProviderConfig(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            required_credentials=[
                {
                    "name": "bot_token",
                    "description": "Bot token from @BotFather (e.g., 123456:ABC-DEF...)",
                    "sensitive": True,
                },
            ],
            required_config=[
                {
                    "name": "chat_id",
                    "description": "Chat/Group/Channel ID (e.g., -1001234567890)",
                    "sensitive": False,
                },
            ],
            optional_config=[
                {
                    "name": "parse_mode",
                    "description": "Message format: HTML or MarkdownV2 (default: HTML)",
                    "default": "HTML",
                },
                {
                    "name": "disable_notification",
                    "description": "Send silently without notification sound",
                    "default": False,
                },
            ],
        )

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate channel configuration."""
        chat_id = config.get("chat_id")
        if not chat_id:
            return False, "chat_id is required"

        # chat_id can be negative (groups/channels) or positive (users)
        try:
            int(chat_id)
        except (ValueError, TypeError):
            return False, "chat_id must be a valid integer"

        return True, None

    def validate_credentials(self, credentials: dict[str, str]) -> tuple[bool, str | None]:
        """Validate credentials."""
        bot_token = credentials.get("bot_token")
        if not bot_token:
            return False, "bot_token is required"

        # Basic format check: number:alphanumeric
        if not re.match(r"^\d+:[A-Za-z0-9_-]+$", bot_token):
            return False, "bot_token format is invalid (expected: 123456:ABC-DEF...)"

        return True, None

    async def send(
        self,
        channel: Channel,
        credentials: dict[str, str],
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a message via Telegram.

        Returns:
            Dict with 'success' and 'message_id' (for later editing)
        """
        try:
            from telegram import Bot
            from telegram.constants import ParseMode
        except ImportError as e:
            raise ProviderError(
                self.name,
                "python-telegram-bot package not installed. "
                "Install with: pip install python-telegram-bot",
                cause=e,
            )

        bot_token = credentials["bot_token"]
        chat_id = channel.config["chat_id"]
        parse_mode_str = channel.config.get("parse_mode", kwargs.get("parse_mode", "HTML"))
        disable_notification = channel.config.get(
            "disable_notification", kwargs.get("disable_notification", False)
        )

        # Map string to ParseMode enum
        parse_mode = ParseMode.HTML if parse_mode_str == "HTML" else ParseMode.MARKDOWN_V2

        # Format message for the parse mode
        formatted_message = self.format_message(message, parse_mode=parse_mode_str)

        # Check if we should edit an existing message
        message_id = kwargs.get("message_id")

        try:
            bot = Bot(token=bot_token)

            if message_id:
                # Edit existing message
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=formatted_message,
                    parse_mode=parse_mode,
                )
                return {"success": True, "message_id": message_id}
            else:
                # Send new message
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                )
                return {"success": True, "message_id": sent_message.message_id}
        except Exception as e:
            raise ProviderError(self.name, f"Failed to send message: {e}", cause=e)

    async def test_connection(
        self,
        channel: Channel,
        credentials: dict[str, str],
    ) -> tuple[bool, str]:
        """Test the Telegram connection."""
        try:
            from telegram import Bot
        except ImportError:
            return False, "python-telegram-bot package not installed"

        # Validate config and credentials first
        valid, error = self.validate_credentials(credentials)
        if not valid:
            return False, error or "Invalid credentials"

        valid, error = self.validate_config(channel.config)
        if not valid:
            return False, error or "Invalid config"

        try:
            bot = Bot(token=credentials["bot_token"])
            # Get bot info to verify token
            bot_info = await bot.get_me()

            # Try to get chat info to verify chat_id
            chat_id = channel.config["chat_id"]
            try:
                chat = await bot.get_chat(chat_id=chat_id)
                chat_title = getattr(chat, "title", None) or getattr(
                    chat, "username", None
                ) or "Private Chat"
                return True, f"Connected! Bot: @{bot_info.username}, Chat: {chat_title}"
            except Exception as e:
                return False, f"Bot token valid (@{bot_info.username}), but cannot access chat: {e}"

        except Exception as e:
            return False, f"Connection failed: {e}"

    def format_message(self, message: str, **kwargs: Any) -> str:
        """Format message for Telegram.

        For HTML mode, we trust the message already contains valid HTML tags.
        Only escape if explicitly requested for user content.
        """
        # Don't escape - our templates already have proper HTML
        return message
