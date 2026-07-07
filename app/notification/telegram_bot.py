from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not set. Notifications will be disabled.")
            self.bot = None
        else:
            self.bot = Bot(token=self.token)

    async def send_message(self, text: str) -> bool:
        """Send a message to the configured chat."""
        if self.bot is None:
            logger.error("Telegram bot not initialized due to missing credentials.")
            return False
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_photo(self, photo_url: str, caption: str = "") -> bool:
        """Send a photo with caption."""
        if self.bot is None:
            logger.error("Telegram bot not initialized.")
            return False
        try:
            await self.bot.send_photo(chat_id=self.chat_id, photo=photo_url, caption=caption)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            return False

    # Optional: set up a simple command handler for testing
    async def start_command(self, update, context):
        await update.message.reply_text('Bot is running and ready to send')
    def setup_application(self):
        """Set up the telegram application for polling (if we want to receive commands)."""
        if self.token is None:
            return None
        application = Application.builder().token(self.token).build()
        application.add_handler(CommandHandler("start", self.start_command))
        return application