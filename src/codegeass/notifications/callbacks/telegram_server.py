"""Polling server for Telegram callbacks and replies."""

import asyncio
import logging
from typing import TYPE_CHECKING

from codegeass.notifications.callbacks.handler import CallbackHandler

if TYPE_CHECKING:
    from codegeass.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)


class TelegramCallbackServer:
    """Polling server for handling Telegram callbacks and replies.

    Polls the Telegram Bot API for updates and routes callback queries
    and reply messages to the CallbackHandler.
    """

    def __init__(
        self,
        callback_handler: CallbackHandler,
        channel_repo: "ChannelRepository",
        poll_interval: float = 0.5,
    ):
        self._handler = callback_handler
        self._channels = channel_repo
        self._poll_interval = poll_interval
        self._running = False
        self._last_update_id: dict[str, int] = {}

    async def start(self) -> None:
        """Start the polling loop."""
        self._running = True
        logger.info("Telegram callback server starting...")
        print("[Callback Server] Starting polling loop...")

        poll_count = 0
        while self._running:
            try:
                await self._poll_all_bots()
                poll_count += 1
                if poll_count % 10 == 0:
                    print(f"[Callback Server] Polling active ({poll_count} polls)", flush=True)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                print(f"[Callback Server] Error in polling: {e}", flush=True)

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        logger.info("Telegram callback server stopping...")

    async def _poll_all_bots(self) -> None:
        """Poll all configured Telegram bots for updates."""
        all_channels = self._channels.find_all()
        telegram_channels = [ch for ch in all_channels if ch.provider == "telegram"]

        if not telegram_channels:
            return

        seen_tokens: set[str] = set()

        for channel in telegram_channels:
            if not channel.enabled:
                continue

            try:
                _, credentials = self._channels.get_channel_with_credentials(channel.id)
                bot_token = credentials.get("bot_token")

                if not bot_token or bot_token in seen_tokens:
                    continue

                seen_tokens.add(bot_token)
                await self._poll_bot(bot_token, credentials)

            except Exception as e:
                print(f"[Callback Server] Error getting credentials for {channel.id}: {e}")

    async def _poll_bot(self, bot_token: str, credentials: dict[str, str]) -> None:
        """Poll a specific bot for updates."""
        try:
            from telegram import Bot
        except ImportError:
            print("[Callback Server] telegram package not installed")
            return

        bot = Bot(token=bot_token)
        offset = (
            self._last_update_id.get(bot_token, 0) + 1
            if bot_token in self._last_update_id
            else None
        )

        try:
            updates = await bot.get_updates(
                offset=offset,
                timeout=2,
                allowed_updates=["callback_query", "message"],
            )

            if updates:
                print(f"[Callback Server] Received {len(updates)} update(s)", flush=True)

            for update in updates:
                self._last_update_id[bot_token] = update.update_id
                await self._process_update(update, credentials)

        except Exception as e:
            if "Timed out" not in str(e):
                logger.error(f"Error polling bot: {e}")
                print(f"[Callback Server] Error polling: {e}", flush=True)

    async def _process_update(self, update: object, credentials: dict[str, str]) -> None:
        """Process a single update from Telegram."""
        from codegeass.notifications.interactive import CallbackQuery as CallbackQueryModel

        if update.callback_query:  # type: ignore[attr-defined]
            await self._process_callback_query(update, credentials, CallbackQueryModel)
        elif update.message and update.message.reply_to_message:  # type: ignore[attr-defined]
            await self._process_reply_message(update)
        elif update.message:  # type: ignore[attr-defined]
            self._log_non_reply_message(update)

    async def _process_callback_query(
        self, update: object, credentials: dict[str, str], callback_query_model: type
    ) -> None:
        """Process a callback query (button click)."""
        cq = update.callback_query  # type: ignore[attr-defined]
        print(f"[Callback Server] Button clicked: {cq.data}")

        callback = callback_query_model(
            query_id=str(cq.id),
            from_user_id=str(cq.from_user.id),
            from_username=cq.from_user.username,
            message_id=cq.message.message_id if cq.message else 0,
            chat_id=str(cq.message.chat.id) if cq.message else "",
            callback_data=cq.data or "",
            provider="telegram",
        )

        success, message = await self._handler.handle_callback(callback, credentials)
        print(f"[Callback Server] Callback result: success={success}, message={message}")

    async def _process_reply_message(self, update: object) -> None:
        """Process a reply message (potential feedback)."""
        msg = update.message  # type: ignore[attr-defined]
        text_preview = msg.text[:50] if msg.text else "(no text)"
        reply_id = msg.reply_to_message.message_id
        print(f"[Callback Server] Reply: '{text_preview}' to msg {reply_id}", flush=True)

        handled, result = await self._handler.handle_reply_message(
            chat_id=str(msg.chat.id),
            user_id=str(msg.from_user.id) if msg.from_user else "",
            reply_to_message_id=msg.reply_to_message.message_id,
            text=msg.text or "",
        )
        print(f"[Callback Server] Reply result: {handled}, {result}", flush=True)

    def _log_non_reply_message(self, update: object) -> None:
        """Log a non-reply message for debugging."""
        umsg = update.message  # type: ignore[attr-defined]
        text_preview = umsg.text[:50] if umsg.text else "(no text)"
        print(f"[Callback Server] Message (not reply): '{text_preview}'", flush=True)
