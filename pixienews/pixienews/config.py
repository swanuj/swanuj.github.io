"""Configuration for PixieNews."""

from __future__ import annotations

import json
from pathlib import Path
from pydantic import BaseModel, Field


# Country codes and their AI news sources
COUNTRY_SOURCES = {
    "US": {
        "name": "United States",
        "flag": "🇺🇸",
        "sources": [
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
            {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "type": "rss"},
            {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "type": "rss"},
        ],
    },
    "UK": {
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "sources": [
            {"name": "BBC Tech", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "type": "rss"},
            {"name": "The Guardian Tech", "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss", "type": "rss"},
            {"name": "Wired UK", "url": "https://www.wired.co.uk/feed/category/ai/latest/rss", "type": "rss"},
        ],
    },
    "IN": {
        "name": "India",
        "flag": "🇮🇳",
        "sources": [
            {"name": "Analytics India", "url": "https://analyticsindiamag.com/feed/", "type": "rss"},
            {"name": "Inc42", "url": "https://inc42.com/tag/artificial-intelligence/feed/", "type": "rss"},
            {"name": "YourStory Tech", "url": "https://yourstory.com/category/technology/feed", "type": "rss"},
        ],
    },
    "CN": {
        "name": "China",
        "flag": "🇨🇳",
        "sources": [
            {"name": "Synced AI", "url": "https://syncedreview.com/feed/", "type": "rss"},
            {"name": "Pandaily Tech", "url": "https://pandaily.com/category/tech/feed/", "type": "rss"},
        ],
    },
    "DE": {
        "name": "Germany",
        "flag": "🇩🇪",
        "sources": [
            {"name": "Heise AI", "url": "https://www.heise.de/thema/KI/rss.xml", "type": "rss"},
            {"name": "Golem AI", "url": "https://rss.golem.de/rss.php?tp=ki&feed=ATOM1.0", "type": "rss"},
        ],
    },
    "JP": {
        "name": "Japan",
        "flag": "🇯🇵",
        "sources": [
            {"name": "AI Japan", "url": "https://ledge.ai/feed/", "type": "rss"},
            {"name": "TechCrunch Japan", "url": "https://jp.techcrunch.com/tag/ai/feed/", "type": "rss"},
        ],
    },
    "FR": {
        "name": "France",
        "flag": "🇫🇷",
        "sources": [
            {"name": "L'Usine Digitale", "url": "https://www.usine-digitale.fr/intelligence-artificielle/rss", "type": "rss"},
            {"name": "ActuIA", "url": "https://www.actuia.com/feed/", "type": "rss"},
        ],
    },
    "KR": {
        "name": "South Korea",
        "flag": "🇰🇷",
        "sources": [
            {"name": "Korea AI Times", "url": "https://www.aitimes.com/rss/allArticle.xml", "type": "rss"},
            {"name": "ZDNet Korea AI", "url": "https://zdnet.co.kr/rss/ai.xml", "type": "rss"},
        ],
    },
    "CA": {
        "name": "Canada",
        "flag": "🇨🇦",
        "sources": [
            {"name": "BetaKit AI", "url": "https://betakit.com/tag/artificial-intelligence/feed/", "type": "rss"},
            {"name": "IT World Canada", "url": "https://www.itworldcanada.com/tag/artificial-intelligence/feed", "type": "rss"},
        ],
    },
    "AU": {
        "name": "Australia",
        "flag": "🇦🇺",
        "sources": [
            {"name": "iTnews AU", "url": "https://www.itnews.com.au/RSS/rss.ashx", "type": "rss"},
            {"name": "ZDNet AU", "url": "https://www.zdnet.com/au/topic/artificial-intelligence/rss.xml", "type": "rss"},
        ],
    },
    "GLOBAL": {
        "name": "Global/International",
        "flag": "🌍",
        "sources": [
            {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "type": "rss"},
            {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss/", "type": "rss"},
            {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss", "type": "rss"},
            {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "type": "rss"},
            {"name": "arXiv AI", "url": "https://arxiv.org/rss/cs.AI", "type": "rss"},
        ],
    },
}


class UserPreferences(BaseModel):
    """User preferences storage."""

    countries: list[str] = Field(default_factory=lambda: ["GLOBAL"])
    language: str = "en"
    news_count: int = 5
    notify_enabled: bool = True


class Config(BaseModel):
    """Main configuration."""

    whatsapp_bridge_url: str = "ws://localhost:3001"
    scrape_interval_minutes: int = 30
    max_news_per_source: int = 10
    cache_ttl_minutes: int = 15
    data_dir: Path = Path.home() / ".pixienews"

    def save(self) -> None:
        """Save config to file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.data_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

    @classmethod
    def load(cls) -> "Config":
        """Load config from file."""
        config_file = Path.home() / ".pixienews" / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                return cls(**json.load(f))
        return cls()
