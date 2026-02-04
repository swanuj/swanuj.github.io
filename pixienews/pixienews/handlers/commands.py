"""Command handler for WhatsApp messages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from pixienews.config import COUNTRY_SOURCES, UserPreferences
from pixienews.scrapers import NewsScraper, NewsArticle
from pixienews.channels.whatsapp import WhatsAppMessage


class UserStore:
    """Simple file-based user preferences store."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir / "users"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_id: str) -> UserPreferences:
        """Get user preferences."""
        user_file = self.data_dir / f"{self._safe_id(user_id)}.json"
        if user_file.exists():
            with open(user_file) as f:
                return UserPreferences(**json.load(f))
        return UserPreferences()

    def save(self, user_id: str, prefs: UserPreferences) -> None:
        """Save user preferences."""
        user_file = self.data_dir / f"{self._safe_id(user_id)}.json"
        with open(user_file, "w") as f:
            json.dump(prefs.model_dump(), f, indent=2)

    def _safe_id(self, user_id: str) -> str:
        """Make user ID safe for filename."""
        return user_id.replace("@", "_").replace(":", "_")


class CommandHandler:
    """Handles user commands and returns responses."""

    COMMANDS = {
        "/start": "Start the bot and see welcome message",
        "/help": "Show available commands",
        "/countries": "List all available countries",
        "/set": "Set your preferred country (e.g., /set US)",
        "/news": "Get latest AI news for your country",
        "/global": "Get global AI news",
        "/search": "Search news (e.g., /search OpenAI GPT)",
        "/subscribe": "Subscribe to daily news updates",
        "/unsubscribe": "Unsubscribe from updates",
    }

    def __init__(self, data_dir: Path) -> None:
        self.users = UserStore(data_dir)
        self.scraper: NewsScraper | None = None

    async def handle(self, message: WhatsAppMessage) -> str | None:
        """Handle an incoming message and return response."""
        content = message.content.strip()

        # Ignore empty messages
        if not content:
            return None

        # Check if it's a command
        if content.startswith("/"):
            return await self._handle_command(message)

        # Check for country code (quick selection)
        upper_content = content.upper()
        if upper_content in COUNTRY_SOURCES:
            return await self._handle_country_selection(message, upper_content)

        # Default: treat as search query if it looks like one
        if len(content) > 2:
            return await self._handle_search(message, content)

        return self._get_help_message()

    async def _handle_command(self, message: WhatsAppMessage) -> str:
        """Handle a slash command."""
        parts = message.content.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "/start": self._cmd_start,
            "/help": self._cmd_help,
            "/countries": self._cmd_countries,
            "/set": self._cmd_set_country,
            "/news": self._cmd_news,
            "/global": self._cmd_global,
            "/search": self._cmd_search,
            "/subscribe": self._cmd_subscribe,
            "/unsubscribe": self._cmd_unsubscribe,
        }

        handler = handlers.get(command)
        if handler:
            return await handler(message, args)

        return f"❓ Unknown command: {command}\n\nType /help for available commands."

    async def _cmd_start(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /start command."""
        return (
            "🤖 *Welcome to PixieNews!*\n\n"
            "I deliver the latest AI news from around the world directly to your WhatsApp.\n\n"
            "🌍 *Quick Start:*\n"
            "1️⃣ Type a country code (US, UK, IN, etc.) to get news\n"
            "2️⃣ Use /set US to set your default country\n"
            "3️⃣ Type /news to get your personalized feed\n\n"
            "📋 Type /help for all commands\n"
            "🗺️ Type /countries to see all available regions"
        )

    async def _cmd_help(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /help command."""
        return self._get_help_message()

    async def _cmd_countries(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /countries command."""
        lines = ["🗺️ *Available Countries:*\n"]

        for code, info in COUNTRY_SOURCES.items():
            sources_count = len(info["sources"])
            lines.append(f"{info['flag']} *{code}* - {info['name']} ({sources_count} sources)")

        lines.append("\n💡 _Reply with a country code to get news!_")
        return "\n".join(lines)

    async def _cmd_set_country(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /set command."""
        if not args:
            return "⚠️ Please specify a country code.\n\nExample: /set US\n\nType /countries to see available codes."

        country = args.upper().strip()
        if country not in COUNTRY_SOURCES:
            return f"❌ Unknown country: {country}\n\nType /countries to see available codes."

        prefs = self.users.get(message.sender)
        prefs.countries = [country]
        self.users.save(message.sender, prefs)

        info = COUNTRY_SOURCES[country]
        return (
            f"✅ Your default country is now set to:\n\n"
            f"{info['flag']} *{info['name']}*\n\n"
            f"Type /news to get the latest AI news!"
        )

    async def _cmd_news(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /news command."""
        prefs = self.users.get(message.sender)
        country = args.upper().strip() if args else prefs.countries[0]

        if country not in COUNTRY_SOURCES:
            return f"❌ Unknown country: {country}\n\nType /countries to see available codes."

        return await self._fetch_and_format_news(country, prefs.news_count)

    async def _cmd_global(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /global command."""
        return await self._fetch_and_format_news("GLOBAL", 5)

    async def _cmd_search(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /search command."""
        if not args:
            return "⚠️ Please provide a search query.\n\nExample: /search OpenAI GPT-5"

        return await self._handle_search(message, args)

    async def _cmd_subscribe(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /subscribe command."""
        prefs = self.users.get(message.sender)
        prefs.notify_enabled = True
        self.users.save(message.sender, prefs)

        return (
            "✅ You're now subscribed to daily AI news!\n\n"
            "📬 You'll receive updates every morning at 9 AM.\n\n"
            "Use /unsubscribe to stop notifications."
        )

    async def _cmd_unsubscribe(self, message: WhatsAppMessage, args: str) -> str:
        """Handle /unsubscribe command."""
        prefs = self.users.get(message.sender)
        prefs.notify_enabled = False
        self.users.save(message.sender, prefs)

        return "✅ You've unsubscribed from daily news updates."

    async def _handle_country_selection(
        self,
        message: WhatsAppMessage,
        country: str,
    ) -> str:
        """Handle direct country code input."""
        prefs = self.users.get(message.sender)
        return await self._fetch_and_format_news(country, prefs.news_count)

    async def _handle_search(self, message: WhatsAppMessage, query: str) -> str:
        """Handle search query."""
        async with NewsScraper() as scraper:
            articles = await scraper.search_news(query, limit=5)

        if not articles:
            return f"🔍 No news found for: *{query}*\n\nTry different keywords."

        lines = [f"🔍 *Search Results for:* {query}\n"]
        for i, article in enumerate(articles, 1):
            info = COUNTRY_SOURCES.get(article.country, {})
            flag = info.get("flag", "📰")
            lines.append(f"\n{i}. {flag} *{article.title}*")
            lines.append(f"   📰 {article.source}")
            lines.append(f"   🔗 {article.url}")

        return "\n".join(lines)

    async def _fetch_and_format_news(self, country: str, limit: int) -> str:
        """Fetch and format news for a country."""
        async with NewsScraper() as scraper:
            articles = await scraper.get_news(country, limit=limit)

        if not articles:
            info = COUNTRY_SOURCES.get(country, {})
            return f"📭 No recent AI news found for {info.get('name', country)}.\n\nTry /global for worldwide news."

        info = COUNTRY_SOURCES[country]
        lines = [f"{info['flag']} *AI News from {info['name']}*\n"]

        for i, article in enumerate(articles, 1):
            lines.append(f"\n*{i}. {article.title}*")
            lines.append(f"📰 {article.source} | 📅 {article.published.strftime('%b %d')}")

            # Truncate summary
            summary = article.summary[:150] + "..." if len(article.summary) > 150 else article.summary
            if summary:
                lines.append(f"_{summary}_")

            lines.append(f"🔗 {article.url}")

        lines.append(f"\n💡 _Reply with another country code for more news!_")
        return "\n".join(lines)

    def _get_help_message(self) -> str:
        """Get formatted help message."""
        lines = ["📚 *PixieNews Commands:*\n"]

        for cmd, desc in self.COMMANDS.items():
            lines.append(f"• *{cmd}* - {desc}")

        lines.append("\n🌍 *Quick Access:*")
        lines.append("Just type a country code (US, UK, IN, DE, etc.) to get news!")
        lines.append("\n🔍 *Search:*")
        lines.append("Type any keyword to search across all news sources.")

        return "\n".join(lines)
