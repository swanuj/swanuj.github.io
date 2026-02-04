"""WhatsApp Business API client using Meta Cloud API or Twilio."""

from __future__ import annotations

import asyncio
import hmac
import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

import httpx
from loguru import logger


@dataclass
class WhatsAppMessage:
    """Incoming WhatsApp message."""
    chat_id: str
    sender: str
    sender_name: str
    content: str
    timestamp: int
    message_type: str = "text"

    @classmethod
    def from_webhook(cls, data: dict[str, Any]) -> "WhatsAppMessage | None":
        """Parse message from Meta webhook payload."""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
            contacts = value.get("contacts", [{}])
            contact = contacts[0] if contacts else {}

            # Extract text content
            content = ""
            msg_type = msg.get("type", "text")

            if msg_type == "text":
                content = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                interactive = msg.get("interactive", {})
                if "button_reply" in interactive:
                    content = interactive["button_reply"].get("id", "")
                elif "list_reply" in interactive:
                    content = interactive["list_reply"].get("id", "")

            return cls(
                chat_id=msg.get("from", ""),
                sender=msg.get("from", ""),
                sender_name=contact.get("profile", {}).get("name", "User"),
                content=content,
                timestamp=int(msg.get("timestamp", 0)),
                message_type=msg_type,
            )
        except Exception as e:
            logger.error(f"Error parsing webhook: {e}")
            return None


class WhatsAppBusinessAPI:
    """Official WhatsApp Business API client (Meta Cloud API)."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        verify_token: str = "pixienews_verify",
        webhook_secret: str | None = None,
    ) -> None:
        """
        Initialize WhatsApp Business API client.

        Args:
            phone_number_id: Your WhatsApp Business phone number ID
            access_token: Meta API access token
            verify_token: Token for webhook verification
            webhook_secret: Secret for validating webhook signatures
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.webhook_secret = webhook_secret
        self._client: httpx.AsyncClient | None = None
        self._message_handler: Callable[[WhatsAppMessage], Awaitable[str | None]] | None = None

    async def __aenter__(self) -> "WhatsAppBusinessAPI":
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        return self._client

    def on_message(
        self,
        handler: Callable[[WhatsAppMessage], Awaitable[str | None]],
    ) -> None:
        """Set message handler."""
        self._message_handler = handler

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        """Verify webhook subscription (GET request from Meta)."""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        logger.warning(f"Webhook verification failed: mode={mode}")
        return None

    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        if not self.webhook_secret:
            return True  # Skip validation if no secret configured

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        # Signature format: sha256=<hash>
        provided = signature.replace("sha256=", "")
        return hmac.compare_digest(expected, provided)

    async def handle_webhook(self, data: dict[str, Any]) -> None:
        """Handle incoming webhook event."""
        message = WhatsAppMessage.from_webhook(data)

        if message and self._message_handler:
            try:
                response = await self._message_handler(message)
                if response:
                    await self.send_message(message.chat_id, response)
            except Exception as e:
                logger.error(f"Handler error: {e}")

    async def send_message(self, to: str, content: str) -> bool:
        """Send a text message."""
        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": content},
                },
            )
            response.raise_for_status()
            logger.debug(f"Sent message to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: list[dict] | None = None,
    ) -> bool:
        """Send a template message (required for first contact)."""
        try:
            payload: dict[str, Any] = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                },
            }

            if components:
                payload["template"]["components"] = components

            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send template: {e}")
            return False

    async def send_interactive_buttons(
        self,
        to: str,
        body: str,
        buttons: list[dict[str, str]],
        header: str | None = None,
        footer: str | None = None,
    ) -> bool:
        """Send interactive message with buttons."""
        try:
            interactive: dict[str, Any] = {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"][:20]},
                        }
                        for btn in buttons[:3]  # Max 3 buttons
                    ]
                },
            }

            if header:
                interactive["header"] = {"type": "text", "text": header}
            if footer:
                interactive["footer"] = {"text": footer}

            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "interactive",
                    "interactive": interactive,
                },
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send buttons: {e}")
            return False

    async def send_interactive_list(
        self,
        to: str,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
        header: str | None = None,
        footer: str | None = None,
    ) -> bool:
        """Send interactive message with list menu."""
        try:
            interactive: dict[str, Any] = {
                "type": "list",
                "body": {"text": body},
                "action": {
                    "button": button_text,
                    "sections": sections,
                },
            }

            if header:
                interactive["header"] = {"type": "text", "text": header}
            if footer:
                interactive["footer"] = {"text": footer}

            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "interactive",
                    "interactive": interactive,
                },
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send list: {e}")
            return False

    async def send_country_selector(self, to: str) -> bool:
        """Send country selection menu."""
        from pixienews.config import COUNTRY_SOURCES

        sections = [{
            "title": "Select Country",
            "rows": [
                {
                    "id": f"country_{code}",
                    "title": f"{info['flag']} {code}",
                    "description": info["name"],
                }
                for code, info in list(COUNTRY_SOURCES.items())[:10]
            ],
        }]

        return await self.send_interactive_list(
            to=to,
            body="🌍 Select a country to get AI news:",
            button_text="Choose Country",
            sections=sections,
            header="PixieNews",
            footer="Tap to select your region",
        )
