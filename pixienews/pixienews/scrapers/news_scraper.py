"""AI News Scraper - Fetches news from multiple country sources."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx
import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from pixienews.config import COUNTRY_SOURCES


@dataclass
class NewsArticle:
    """Represents a news article."""

    title: str
    url: str
    summary: str
    source: str
    country: str
    published: datetime
    image_url: str | None = None

    @property
    def id(self) -> str:
        """Generate unique ID for article."""
        return hashlib.md5(self.url.encode()).hexdigest()[:12]

    def format_whatsapp(self) -> str:
        """Format article for WhatsApp message."""
        country_info = COUNTRY_SOURCES.get(self.country, {})
        flag = country_info.get("flag", "📰")

        # Truncate summary if too long
        summary = self.summary[:200] + "..." if len(self.summary) > 200 else self.summary

        return (
            f"{flag} *{self.title}*\n\n"
            f"📰 {self.source}\n"
            f"📅 {self.published.strftime('%b %d, %Y')}\n\n"
            f"{summary}\n\n"
            f"🔗 {self.url}"
        )


class NewsCache:
    """Simple in-memory cache for news articles."""

    def __init__(self, ttl_minutes: int = 15) -> None:
        self._cache: dict[str, tuple[list[NewsArticle], datetime]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(self, country: str) -> list[NewsArticle] | None:
        """Get cached articles for a country."""
        if country in self._cache:
            articles, timestamp = self._cache[country]
            if datetime.now() - timestamp < self._ttl:
                return articles
            del self._cache[country]
        return None

    def set(self, country: str, articles: list[NewsArticle]) -> None:
        """Cache articles for a country."""
        self._cache[country] = (articles, datetime.now())

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()


class NewsScraper:
    """Scrapes AI news from multiple countries."""

    def __init__(self, cache_ttl: int = 15) -> None:
        self.cache = NewsCache(ttl_minutes=cache_ttl)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "NewsScraper":
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "PixieNews/1.0 (AI News Aggregator)"}
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Scraper not initialized. Use 'async with' context.")
        return self._client

    def get_available_countries(self) -> list[dict[str, str]]:
        """Get list of available countries."""
        return [
            {"code": code, "name": info["name"], "flag": info["flag"]}
            for code, info in COUNTRY_SOURCES.items()
        ]

    async def get_news(
        self,
        country: str,
        limit: int = 5,
        use_cache: bool = True,
    ) -> list[NewsArticle]:
        """Get AI news for a specific country."""
        if country not in COUNTRY_SOURCES:
            logger.warning(f"Unknown country code: {country}")
            return []

        # Check cache first
        if use_cache:
            cached = self.cache.get(country)
            if cached:
                logger.debug(f"Cache hit for {country}")
                return cached[:limit]

        # Fetch from sources
        country_info = COUNTRY_SOURCES[country]
        all_articles: list[NewsArticle] = []

        tasks = [
            self._fetch_source(source, country)
            for source in country_info["sources"]
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Source fetch error: {result}")

        # Sort by date (newest first) and deduplicate
        all_articles = self._deduplicate(all_articles)
        all_articles.sort(key=lambda x: x.published, reverse=True)

        # Cache results
        self.cache.set(country, all_articles)

        return all_articles[:limit]

    async def get_news_multi_country(
        self,
        countries: list[str],
        limit_per_country: int = 3,
    ) -> dict[str, list[NewsArticle]]:
        """Get news for multiple countries."""
        tasks = {
            country: self.get_news(country, limit=limit_per_country)
            for country in countries
        }

        results = {}
        for country, task in tasks.items():
            try:
                results[country] = await task
            except Exception as e:
                logger.error(f"Error fetching {country}: {e}")
                results[country] = []

        return results

    async def search_news(
        self,
        query: str,
        countries: list[str] | None = None,
        limit: int = 10,
    ) -> list[NewsArticle]:
        """Search news across countries."""
        if countries is None:
            countries = list(COUNTRY_SOURCES.keys())

        all_news = await self.get_news_multi_country(countries, limit_per_country=10)

        # Filter by query
        query_lower = query.lower()
        matching = []

        for articles in all_news.values():
            for article in articles:
                if (query_lower in article.title.lower() or
                    query_lower in article.summary.lower()):
                    matching.append(article)

        # Sort by relevance (title match > summary match) and date
        matching.sort(
            key=lambda x: (
                query_lower in x.title.lower(),
                x.published
            ),
            reverse=True
        )

        return matching[:limit]

    async def _fetch_source(
        self,
        source: dict[str, str],
        country: str,
    ) -> list[NewsArticle]:
        """Fetch articles from a single source."""
        try:
            if source["type"] == "rss":
                return await self._fetch_rss(source, country)
            else:
                return await self._fetch_html(source, country)
        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")
            return []

    async def _fetch_rss(
        self,
        source: dict[str, str],
        country: str,
    ) -> list[NewsArticle]:
        """Fetch articles from RSS feed."""
        response = await self.client.get(source["url"])
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        articles = []

        for entry in feed.entries[:10]:  # Limit per source
            # Parse published date
            published = datetime.now()
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass

            # Get summary
            summary = ""
            if hasattr(entry, "summary"):
                summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]
            elif hasattr(entry, "description"):
                summary = BeautifulSoup(entry.description, "html.parser").get_text()[:500]

            # Filter for AI-related content
            title = entry.get("title", "")
            if not self._is_ai_related(title, summary):
                continue

            # Get image if available
            image_url = None
            if hasattr(entry, "media_content"):
                image_url = entry.media_content[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                image_url = entry.enclosures[0].get("href")

            articles.append(NewsArticle(
                title=title,
                url=entry.get("link", ""),
                summary=summary,
                source=source["name"],
                country=country,
                published=published,
                image_url=image_url,
            ))

        return articles

    async def _fetch_html(
        self,
        source: dict[str, str],
        country: str,
    ) -> list[NewsArticle]:
        """Fetch articles from HTML page (fallback)."""
        # Simplified HTML scraping - extend based on specific sites
        response = await self.client.get(source["url"])
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        # Generic article extraction
        for article_tag in soup.find_all("article")[:10]:
            title_tag = article_tag.find(["h1", "h2", "h3"])
            link_tag = article_tag.find("a", href=True)

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                url = link_tag["href"]

                if not url.startswith("http"):
                    url = source["url"].rstrip("/") + "/" + url.lstrip("/")

                summary_tag = article_tag.find("p")
                summary = summary_tag.get_text(strip=True) if summary_tag else ""

                if self._is_ai_related(title, summary):
                    articles.append(NewsArticle(
                        title=title,
                        url=url,
                        summary=summary,
                        source=source["name"],
                        country=country,
                        published=datetime.now(),
                    ))

        return articles

    def _is_ai_related(self, title: str, summary: str) -> bool:
        """Check if content is AI-related."""
        ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "ml",
            "deep learning", "neural", "gpt", "llm", "chatgpt", "claude",
            "gemini", "openai", "anthropic", "transformer", "nlp",
            "computer vision", "generative", "diffusion", "stable diffusion",
            "midjourney", "dall-e", "copilot", "automation", "robot",
        ]

        text = (title + " " + summary).lower()
        return any(keyword in text for keyword in ai_keywords)

    def _deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Remove duplicate articles."""
        seen: set[str] = set()
        unique = []

        for article in articles:
            if article.id not in seen:
                seen.add(article.id)
                unique.append(article)

        return unique
