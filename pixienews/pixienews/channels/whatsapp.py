"""WhatsApp client using whatsapp-web.js bridge."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

import websocket
from loguru import logger


@dataclass
class WhatsAppMessage:
    """Incoming WhatsApp message."""

    chat_id: str
    sender: str
    content: str
    timestamp: int
    is_group: bool = False
    group_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WhatsAppMessage":
        return cls(
            chat_id=data.get("chatId", ""),
            sender=data.get("sender", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", 0),
            is_group=data.get("isGroup", False),
            group_name=data.get("groupName"),
        )


class WhatsAppClient:
    """WhatsApp client connecting to Node.js bridge."""

    def __init__(self, bridge_url: str = "ws://localhost:3001") -> None:
        self.bridge_url = bridge_url
        self._ws: websocket.WebSocket | None = None
        self._connected = False
        self._message_handler: Callable[[WhatsAppMessage], Awaitable[str | None]] | None = None
        self._running = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def on_message(
        self,
        handler: Callable[[WhatsAppMessage], Awaitable[str | None]],
    ) -> None:
        """Set message handler."""
        self._message_handler = handler

    def connect(self) -> bool:
        """Connect to WhatsApp bridge."""
        try:
            self._ws = websocket.WebSocket()
            self._ws.connect(self.bridge_url)
            self._connected = True
            logger.info("Connected to WhatsApp bridge")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WhatsApp bridge: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from bridge."""
        if self._ws:
            self._ws.close()
            self._connected = False
            logger.info("Disconnected from WhatsApp bridge")

    async def run(self) -> None:
        """Run the message listener loop."""
        if not self._connected:
            if not self.connect():
                raise RuntimeError("Cannot connect to WhatsApp bridge")

        self._running = True
        logger.info("WhatsApp client started - listening for messages")

        while self._running and self._ws:
            try:
                # Non-blocking receive with timeout
                self._ws.settimeout(1.0)
                try:
                    raw = self._ws.recv()
                except websocket.WebSocketTimeoutException:
                    await asyncio.sleep(0.1)
                    continue

                data = json.loads(raw)
                event_type = data.get("type")

                if event_type == "message":
                    message = WhatsAppMessage.from_dict(data.get("data", {}))
                    logger.debug(f"Received message from {message.sender}: {message.content[:50]}")

                    if self._message_handler:
                        try:
                            response = await self._message_handler(message)
                            if response:
                                self.send_message(message.chat_id, response)
                        except Exception as e:
                            logger.error(f"Handler error: {e}")

                elif event_type == "qr":
                    qr_code = data.get("data", {}).get("qr", "")
                    logger.info(f"Scan QR code to connect WhatsApp:\n{qr_code}")

                elif event_type == "ready":
                    logger.info("WhatsApp client is ready!")

                elif event_type == "disconnected":
                    logger.warning("WhatsApp disconnected")
                    self._connected = False

            except websocket.WebSocketConnectionClosedException:
                logger.warning("WebSocket connection closed, reconnecting...")
                self._connected = False
                await asyncio.sleep(5)
                self.connect()

            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(1)

    def stop(self) -> None:
        """Stop the message listener."""
        self._running = False

    def send_message(self, chat_id: str, content: str) -> bool:
        """Send a message to a chat."""
        if not self._ws or not self._connected:
            logger.error("Not connected to WhatsApp bridge")
            return False

        try:
            payload = json.dumps({
                "type": "send_message",
                "data": {
                    "chatId": chat_id,
                    "content": content,
                }
            })
            self._ws.send(payload)
            logger.debug(f"Sent message to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: str = "",
    ) -> bool:
        """Send an image to a chat."""
        if not self._ws or not self._connected:
            return False

        try:
            payload = json.dumps({
                "type": "send_image",
                "data": {
                    "chatId": chat_id,
                    "imageUrl": image_url,
                    "caption": caption,
                }
            })
            self._ws.send(payload)
            return True
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            return False

    def send_buttons(
        self,
        chat_id: str,
        content: str,
        buttons: list[dict[str, str]],
    ) -> bool:
        """Send a message with buttons."""
        if not self._ws or not self._connected:
            return False

        try:
            payload = json.dumps({
                "type": "send_buttons",
                "data": {
                    "chatId": chat_id,
                    "content": content,
                    "buttons": buttons,
                }
            })
            self._ws.send(payload)
            return True
        except Exception as e:
            logger.error(f"Failed to send buttons: {e}")
            return False
