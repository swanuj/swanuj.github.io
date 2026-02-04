"""CLI interface for PixieNews."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from loguru import logger

from pixienews.config import Config, COUNTRY_SOURCES

app = typer.Typer(
    name="pixienews",
    help="AI News Bot - Get AI news from around the world via Telegram or WhatsApp",
)
console = Console()


@app.command()
def run(
    bridge_url: str = typer.Option(
        "ws://localhost:3001",
        "--bridge", "-b",
        help="WhatsApp bridge WebSocket URL",
    ),
    data_dir: Path = typer.Option(
        Path.home() / ".pixienews",
        "--data", "-d",
        help="Data directory for storing config and user data",
    ),
):
    """Run the PixieNews WhatsApp bot."""
    from pixienews.bot import PixieNewsBot

    console.print("[bold green]🤖 Starting PixieNews Bot...[/]")
    console.print(f"📁 Data directory: {data_dir}")
    console.print(f"🔌 Bridge URL: {bridge_url}")

    config = Config(
        whatsapp_bridge_url=bridge_url,
        data_dir=data_dir,
    )

    bot = PixieNewsBot(config)

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/]")


@app.command()
def countries():
    """List all available countries and their news sources."""
    table = Table(title="Available Countries")
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Flag", justify="center")
    table.add_column("Country", style="green")
    table.add_column("Sources", justify="right", style="magenta")

    for code, info in COUNTRY_SOURCES.items():
        table.add_row(
            code,
            info["flag"],
            info["name"],
            str(len(info["sources"])),
        )

    console.print(table)


@app.command()
def news(
    country: str = typer.Argument("GLOBAL", help="Country code (US, UK, IN, etc.)"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of articles"),
):
    """Fetch AI news for a country (CLI mode)."""
    from pixienews.scrapers import NewsScraper

    country = country.upper()
    if country not in COUNTRY_SOURCES:
        console.print(f"[red]Unknown country: {country}[/]")
        console.print("Use 'pixienews countries' to see available codes.")
        raise typer.Exit(1)

    info = COUNTRY_SOURCES[country]
    console.print(f"\n{info['flag']} [bold]AI News from {info['name']}[/]\n")

    async def fetch():
        async with NewsScraper() as scraper:
            return await scraper.get_news(country, limit=limit)

    articles = asyncio.run(fetch())

    if not articles:
        console.print("[yellow]No recent news found.[/]")
        return

    for i, article in enumerate(articles, 1):
        console.print(f"[bold cyan]{i}. {article.title}[/]")
        console.print(f"   📰 {article.source} | 📅 {article.published.strftime('%Y-%m-%d')}")
        if article.summary:
            summary = article.summary[:200] + "..." if len(article.summary) > 200 else article.summary
            console.print(f"   [dim]{summary}[/]")
        console.print(f"   🔗 {article.url}\n")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of results"),
):
    """Search AI news across all countries."""
    from pixienews.scrapers import NewsScraper

    console.print(f"\n🔍 [bold]Searching for: {query}[/]\n")

    async def do_search():
        async with NewsScraper() as scraper:
            return await scraper.search_news(query, limit=limit)

    articles = asyncio.run(do_search())

    if not articles:
        console.print("[yellow]No results found.[/]")
        return

    for i, article in enumerate(articles, 1):
        info = COUNTRY_SOURCES.get(article.country, {})
        flag = info.get("flag", "📰")
        console.print(f"[bold cyan]{i}. {flag} {article.title}[/]")
        console.print(f"   📰 {article.source} ({article.country})")
        console.print(f"   🔗 {article.url}\n")


@app.command()
def setup():
    """Interactive setup for PixieNews."""
    console.print("[bold]🔧 PixieNews Setup[/]\n")

    # Create config
    config = Config()
    config.data_dir.mkdir(parents=True, exist_ok=True)

    console.print("1. Install the WhatsApp bridge:")
    console.print("   [cyan]cd pixienews/bridge && npm install[/]")
    console.print("")
    console.print("2. Start the WhatsApp bridge:")
    console.print("   [cyan]node server.js[/]")
    console.print("")
    console.print("3. Scan the QR code with your WhatsApp")
    console.print("")
    console.print("4. Start the bot:")
    console.print("   [cyan]pixienews run[/]")
    console.print("")

    config.save()
    console.print(f"[green]✓ Config saved to {config.data_dir / 'config.json'}[/]")


@app.command()
def webhook(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Run the WhatsApp Business API webhook server.

    This is the RECOMMENDED method for creating a real WhatsApp bot.

    Required environment variables:
    - WHATSAPP_PHONE_NUMBER_ID: Your phone number ID from Meta
    - WHATSAPP_ACCESS_TOKEN: Your access token from Meta
    - WHATSAPP_VERIFY_TOKEN: Your custom verify token

    Example:
        export WHATSAPP_PHONE_NUMBER_ID="123456789"
        export WHATSAPP_ACCESS_TOKEN="EAAxxxx..."
        export WHATSAPP_VERIFY_TOKEN="my_secret_token"
        pixienews webhook --port 8000
    """
    import os

    if debug:
        logger.enable("pixienews")

    # Check for required environment variables
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if not phone_id or not access_token:
        console.print("[bold red]Missing required environment variables![/]\n")
        console.print("Please set the following:")
        console.print("  [cyan]export WHATSAPP_PHONE_NUMBER_ID='your_phone_id'[/]")
        console.print("  [cyan]export WHATSAPP_ACCESS_TOKEN='your_token'[/]")
        console.print("  [cyan]export WHATSAPP_VERIFY_TOKEN='your_verify_token'[/]")
        console.print("\nSee README.md for setup instructions.")
        raise typer.Exit(1)

    console.print("[bold green]🚀 Starting PixieNews Webhook Server...[/]")
    console.print(f"📍 Listening on: http://{host}:{port}")
    console.print(f"🔗 Webhook URL: http://{host}:{port}/webhook")
    console.print(f"✅ Verify Token: {verify_token or 'pixienews_verify'}")
    console.print("\n[yellow]Configure this URL in your Meta Dashboard![/]\n")

    from pixienews.webhook_server import run_server
    run_server(host=host, port=port)


@app.command()
def telegram(
    token: str = typer.Option(
        None,
        "--token", "-t",
        envvar="TELEGRAM_BOT_TOKEN",
        help="Telegram bot token from @BotFather",
    ),
    data_dir: Path = typer.Option(
        Path.home() / ".pixienews",
        "--data", "-d",
        help="Data directory for storing user data",
    ),
):
    """Run PixieNews as a Telegram bot (EASIEST METHOD!).

    This is the simplest way to deploy PixieNews!

    Setup in 2 minutes:
    1. Message @BotFather on Telegram
    2. Send /newbot and follow instructions
    3. Copy the token
    4. Run: pixienews telegram --token YOUR_TOKEN

    Or set environment variable:
        export TELEGRAM_BOT_TOKEN="your_token"
        pixienews telegram
    """
    if not token:
        console.print("[bold red]Missing Telegram bot token![/]\n")
        console.print("[bold]How to get a token (2 minutes):[/]")
        console.print("1. Open Telegram and message [cyan]@BotFather[/]")
        console.print("2. Send [cyan]/newbot[/]")
        console.print("3. Choose a name (e.g., 'My AI News Bot')")
        console.print("4. Choose a username (e.g., 'myainews_bot')")
        console.print("5. Copy the token you receive")
        console.print("")
        console.print("[bold]Then run:[/]")
        console.print("  [green]pixienews telegram --token YOUR_TOKEN[/]")
        console.print("")
        console.print("[bold]Or set environment variable:[/]")
        console.print("  [green]export TELEGRAM_BOT_TOKEN='your_token'[/]")
        console.print("  [green]pixienews telegram[/]")
        raise typer.Exit(1)

    try:
        from pixienews.channels.telegram import TelegramBot
    except ImportError:
        console.print("[bold red]python-telegram-bot is required![/]")
        console.print("Install with: [cyan]pip install 'pixienews[telegram]'[/]")
        raise typer.Exit(1)

    console.print("[bold green]🤖 Starting PixieNews Telegram Bot...[/]")
    console.print(f"📁 Data directory: {data_dir}")
    console.print("")
    console.print("[bold]Your bot is now running![/]")
    console.print("Open Telegram and send [cyan]/start[/] to your bot.")
    console.print("")

    bot = TelegramBot(token=token, data_dir=str(data_dir))

    try:
        bot.run_sync()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/]")


@app.command()
def bridge():
    """Show instructions for setting up the WhatsApp bridge (Method 2 - Personal use)."""
    console.print("""
[bold]WhatsApp Bridge Setup (Personal Use)[/]

[yellow]⚠️  This method links YOUR WhatsApp account (like WhatsApp Web).
    The bot responds AS YOU, not as a separate bot.[/]

For a REAL bot, use: [green]pixienews webhook[/] (WhatsApp Business API)

[bold cyan]Prerequisites:[/]
• Node.js >= 18
• npm or yarn

[bold cyan]Installation:[/]
1. Navigate to the bridge directory:
   [green]cd pixienews/bridge[/]

2. Install dependencies:
   [green]npm install[/]

3. Start the bridge:
   [green]node server.js[/]

4. Scan the QR code with WhatsApp:
   • Open WhatsApp on your phone
   • Go to Settings > Linked Devices
   • Tap "Link a Device"
   • Scan the QR code shown in terminal

[bold cyan]Running the Bot:[/]
Once the bridge is connected, start PixieNews:
   [green]pixienews run[/]

[bold cyan]Notes:[/]
• The bridge runs on ws://localhost:3001 by default
• Session data is stored in bridge/.wwebjs_auth/
• Keep the bridge running for the bot to work
""")


if __name__ == "__main__":
    app()
