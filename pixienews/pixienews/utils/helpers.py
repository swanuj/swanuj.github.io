"""Helper utilities for PixieNews."""

from __future__ import annotations

import re
from datetime import datetime


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_date(dt: datetime, fmt: str = "%b %d, %Y") -> str:
    """Format datetime to string."""
    return dt.strftime(fmt)


def sanitize_filename(filename: str) -> str:
    """Sanitize string for use as filename."""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    # Limit length
    return sanitized[:100]


def clean_html(html: str) -> str:
    """Remove HTML tags from string."""
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser").get_text()


def is_valid_country_code(code: str) -> bool:
    """Check if country code is valid."""
    from pixienews.config import COUNTRY_SOURCES

    return code.upper() in COUNTRY_SOURCES
