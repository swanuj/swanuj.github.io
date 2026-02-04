"""Telegram Bot integration for PixieNews.

This is the EASIEST way to deploy PixieNews!
Just get a token from @BotFather and you're done.

Setup:
1. Message @BotFather on Telegram
2. Send /newbot
3. Follow instructions to get your token
4. Run: pixienews telegram --token YOUR_TOKEN
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class TelegramBot:
    """Telegram bot for PixieNews.

    Usage:
        bot = TelegramBot(token="YOUR_BOT_TOKEN")
        await bot.run()
    """

    def __init__(self, token: str, data_dir: str | None = None) -> None:
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "python-telegram-bot is required. "
                "Install with: pip install 'pixienews[telegram]'"
            )

        self.token = token
        self.data_dir = data_dir
        self._app: Application | None = None

        # Import handlers
        from pixienews.handlers.commands import CommandHandler as NewsHandler, UserStore
        from pathlib import Path

        data_path = Path(data_dir) if data_dir else Path.home() / ".pixienews"
        self.news_handler = NewsHandler(data_path)

    def _build_country_keyboard(self) -> InlineKeyboardMarkup:
        """Build inline keyboard with country buttons."""
        from pixienews.config import COUNTRY_SOURCES

        buttons = []
        row = []

        for i, (code, info) in enumerate(COUNTRY_SOURCES.items()):
            row.append(
                InlineKeyboardButton(
                    f"{info['flag']} {code}",
                    callback_data=f"country_{code}"
                )
            )
            if len(row) == 3:  # 3 buttons per row
                buttons.append(row)
                row = []

        if row:  # Add remaining buttons
            buttons.append(row)

        return InlineKeyboardMarkup(buttons)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome = (
            "🤖 *Welcome to PixieNews!*\n\n"
            "I deliver the latest AI news from around the world.\n\n"
            "🌍 *Quick Start:*\n"
            "• Tap a country button below\n"
            "• Or type a country code (US, UK, IN, etc.)\n"
            "• Use /news to get your personalized feed\n\n"
            "📋 Type /help for all commands"
        )

        await update.message.reply_text(
            welcome,
            parse_mode="Markdown",
            reply_markup=self._build_country_keyboard()
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "📚 *PixieNews Commands:*\n\n"
            "• /start - Welcome & country selection\n"
            "• /help - Show this help message\n"
            "• /countries - List all available countries\n"
            "• /set US - Set your default country\n"
            "• /news - Get news for your country\n"
            "• /news UK - Get news for specific country\n"
            "• /global - Get global AI news\n"
            "• /search keyword - Search news\n"
            "• /subscribe - Daily news updates\n"
            "• /unsubscribe - Stop updates\n\n"
            "💡 *Tip:* Just type a country code to get news!"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _cmd_countries(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /countries command."""
        from pixienews.config import COUNTRY_SOURCES

        lines = ["🗺️ *Available Countries:*\n"]
        for code, info in COUNTRY_SOURCES.items():
            lines.append(f"{info['flag']} *{code}* - {info['name']}")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=self._build_country_keyboard()
        )

    async def _cmd_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /news command."""
        args = " ".join(context.args) if context.args else ""

        # Create a fake message object for our handler
        class FakeMsg:
            def __init__(self, content: str, sender: str):
                self.content = f"/news {content}".strip()
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(args, str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(
            response or "No news found.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    async def _cmd_global(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /global command."""
        class FakeMsg:
            def __init__(self, sender: str):
                self.content = "/global"
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(
            response or "No news found.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    async def _cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /search command."""
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please provide a search query.\n\nExample: /search OpenAI"
            )
            return

        query = " ".join(context.args)

        class FakeMsg:
            def __init__(self, content: str, sender: str):
                self.content = f"/search {content}"
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(query, str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(
            response or "No results found.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    async def _cmd_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /set command."""
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a country code.\n\nExample: /set US",
                reply_markup=self._build_country_keyboard()
            )
            return

        country = context.args[0].upper()

        class FakeMsg:
            def __init__(self, content: str, sender: str):
                self.content = f"/set {content}"
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(country, str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /subscribe command."""
        class FakeMsg:
            def __init__(self, sender: str):
                self.content = "/subscribe"
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _cmd_unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unsubscribe command."""
        class FakeMsg:
            def __init__(self, sender: str):
                self.content = "/unsubscribe"
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle plain text messages (country codes, search queries)."""
        text = update.message.text.strip()

        class FakeMsg:
            def __init__(self, content: str, sender: str):
                self.content = content
                self.sender = sender
                self.chat_id = sender

        fake = FakeMsg(text, str(update.effective_user.id))
        response = await self.news_handler.handle(fake)

        if response:
            await update.message.reply_text(
                response,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("country_"):
            country = data.replace("country_", "")

            class FakeMsg:
                def __init__(self, content: str, sender: str):
                    self.content = content
                    self.sender = sender
                    self.chat_id = sender

            fake = FakeMsg(country, str(update.effective_user.id))
            response = await self.news_handler.handle(fake)

            await query.edit_message_text(
                response or "No news found.",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

    async def run(self) -> None:
        """Run the Telegram bot."""
        logger.info("Starting Telegram bot...")

        self._app = Application.builder().token(self.token).build()

        # Add command handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("countries", self._cmd_countries))
        self._app.add_handler(CommandHandler("news", self._cmd_news))
        self._app.add_handler(CommandHandler("global", self._cmd_global))
        self._app.add_handler(CommandHandler("search", self._cmd_search))
        self._app.add_handler(CommandHandler("set", self._cmd_set))
        self._app.add_handler(CommandHandler("subscribe", self._cmd_subscribe))
        self._app.add_handler(CommandHandler("unsubscribe", self._cmd_unsubscribe))

        # Handle plain text
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))

        # Handle button callbacks
        self._app.add_handler(CallbackQueryHandler(self._handle_callback))

        logger.info("Telegram bot started! Send /start to your bot.")

        # Run the bot
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()

    def run_sync(self) -> None:
        """Run the bot synchronously (for CLI)."""
        asyncio.run(self.run())
