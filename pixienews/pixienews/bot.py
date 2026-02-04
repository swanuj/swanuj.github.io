"""Main bot class that orchestrates everything."""

from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger

from pixienews.config import Config
from pixienews.channels.whatsapp import WhatsAppClient, WhatsAppMessage
from pixienews.handlers.commands import CommandHandler


class PixieNewsBot:
    """Main PixieNews bot orchestrator."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        self.whatsapp = WhatsAppClient(self.config.whatsapp_bridge_url)
        self.handler = CommandHandler(self.config.data_dir)

        # Set up message handler
        self.whatsapp.on_message(self._handle_message)

    async def _handle_message(self, message: WhatsAppMessage) -> str | None:
        """Handle incoming WhatsApp message."""
        logger.info(f"Message from {message.sender}: {message.content[:50]}...")

        try:
            response = await self.handler.handle(message)
            return response
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return "❌ Sorry, something went wrong. Please try again."

    async def run(self) -> None:
        """Run the bot."""
        logger.info("Starting PixieNews bot...")

        # Connect to WhatsApp
        if not self.whatsapp.connect():
            logger.error("Failed to connect to WhatsApp bridge")
            logger.info("Make sure the bridge is running: cd bridge && node server.js")
            return

        logger.info("Connected to WhatsApp bridge")
        logger.info("Waiting for messages...")

        try:
            await self.whatsapp.run()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.whatsapp.disconnect()

    async def send_news_blast(
        self,
        chat_ids: list[str],
        country: str = "GLOBAL",
    ) -> None:
        """Send news to multiple chats (for scheduled updates)."""
        from pixienews.scrapers import NewsScraper

        async with NewsScraper() as scraper:
            articles = await scraper.get_news(country, limit=5)

        if not articles:
            return

        from pixienews.config import COUNTRY_SOURCES
        info = COUNTRY_SOURCES[country]

        message_lines = [f"{info['flag']} *Daily AI News from {info['name']}*\n"]
        for i, article in enumerate(articles[:5], 1):
            message_lines.append(f"\n*{i}. {article.title}*")
            message_lines.append(f"📰 {article.source}")
            message_lines.append(f"🔗 {article.url}")

        message = "\n".join(message_lines)

        for chat_id in chat_ids:
            self.whatsapp.send_message(chat_id, message)
            await asyncio.sleep(1)  # Rate limiting
