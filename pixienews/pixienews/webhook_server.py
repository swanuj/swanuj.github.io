"""FastAPI webhook server for WhatsApp Business API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, Query
from loguru import logger

from pixienews.config import Config
from pixienews.channels.whatsapp_business import WhatsAppBusinessAPI, WhatsAppMessage
from pixienews.handlers.commands import CommandHandler


# Global instances
config = Config.load()
handler = CommandHandler(config.data_dir)
whatsapp: WhatsAppBusinessAPI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize WhatsApp client."""
    global whatsapp

    # Load credentials from environment
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "pixienews_verify")
    webhook_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")

    if not phone_number_id or not access_token:
        logger.warning("WhatsApp credentials not set. Bot will not respond.")
        yield
        return

    whatsapp = WhatsAppBusinessAPI(
        phone_number_id=phone_number_id,
        access_token=access_token,
        verify_token=verify_token,
        webhook_secret=webhook_secret,
    )

    # Set message handler
    whatsapp.on_message(handle_message)

    async with whatsapp:
        logger.info("WhatsApp Business API client initialized")
        yield

    logger.info("Shutting down WhatsApp client")


app = FastAPI(
    title="PixieNews WhatsApp Bot",
    description="AI News aggregator for WhatsApp",
    version="1.0.0",
    lifespan=lifespan,
)


async def handle_message(message: WhatsAppMessage) -> str | None:
    """Handle incoming WhatsApp message."""
    logger.info(f"Message from {message.sender_name} ({message.sender}): {message.content[:50]}")

    # Convert to our message format
    class FakeMessage:
        def __init__(self, wa_msg: WhatsAppMessage):
            self.content = wa_msg.content
            self.sender = wa_msg.sender
            self.chat_id = wa_msg.chat_id

    fake_msg = FakeMessage(message)

    # Handle button/list replies
    if message.content.startswith("country_"):
        country_code = message.content.replace("country_", "").upper()
        fake_msg.content = country_code

    try:
        response = await handler.handle(fake_msg)
        return response
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        return "❌ Sorry, something went wrong. Please try again."


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "PixieNews WhatsApp Bot"}


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Webhook verification endpoint (called by Meta)."""
    if not whatsapp:
        raise HTTPException(status_code=503, detail="WhatsApp not configured")

    result = whatsapp.verify_webhook(hub_mode or "", hub_token or "", hub_challenge or "")

    if result:
        return Response(content=result, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook events from Meta."""
    if not whatsapp:
        raise HTTPException(status_code=503, detail="WhatsApp not configured")

    # Get raw body for signature validation
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not whatsapp.validate_signature(body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse and handle the event
    try:
        data = await request.json()
        await whatsapp.handle_webhook(data)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")

    # Always return 200 to acknowledge receipt
    return {"status": "ok"}


@app.post("/send")
async def send_message(to: str, message: str):
    """Manual endpoint to send a message (for testing)."""
    if not whatsapp:
        raise HTTPException(status_code=503, detail="WhatsApp not configured")

    success = await whatsapp.send_message(to, message)
    return {"success": success}


@app.post("/send-country-menu")
async def send_country_menu(to: str):
    """Send country selection menu to a user."""
    if not whatsapp:
        raise HTTPException(status_code=503, detail="WhatsApp not configured")

    success = await whatsapp.send_country_selector(to)
    return {"success": success}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the webhook server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
