"""WhatsApp and other channel integrations."""

from pixienews.channels.whatsapp import WhatsAppClient, WhatsAppMessage

# WhatsApp Business API (recommended)
try:
    from pixienews.channels.whatsapp_business import (
        WhatsAppBusinessAPI,
        WhatsAppMessage as BusinessMessage,
    )
    HAS_BUSINESS_API = True
except ImportError:
    HAS_BUSINESS_API = False

__all__ = ["WhatsAppClient", "WhatsAppMessage"]

if HAS_BUSINESS_API:
    __all__.extend(["WhatsAppBusinessAPI", "BusinessMessage"])
