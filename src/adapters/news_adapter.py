"""News adapter for fetching stock-related headlines."""

import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class NewsHeadline:
    """A news headline with metadata.

    Attributes:
        title: The headline text.
        source: The news source name.
        url: Link to the full article.
        published: Publication timestamp.
    """

    title: str
    source: str
    url: str
    published: datetime | None = None


class NewsAdapterError(Exception):
    """Error fetching news data."""

    pass


class NewsAdapter:
    """Adapter for fetching stock-related news headlines via RSS.

    Uses Google News RSS feed as the primary source.

    Returns:
        A NewsAdapter instance.
    """

    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US"

    def __init__(self, timeout: int = 10) -> None:
        """Initialize the news adapter.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    def get_headlines(
        self,
        symbol: str,
        max_headlines: int = 5,
    ) -> list[NewsHeadline]:
        """Fetch recent news headlines for a stock symbol.

        Args:
            symbol: The stock ticker symbol.
            max_headlines: Maximum number of headlines to return.

        Returns:
            List of NewsHeadline objects.
        """
        # Build search query
        query = f"{symbol} stock"
        encoded_query = quote(query)
        feed_url = self.GOOGLE_NEWS_RSS.format(query=encoded_query)

        logger.debug("Fetching news from: %s", feed_url)

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                logger.warning(
                    "Feed parsing issue for %s: %s",
                    symbol,
                    feed.bozo_exception,
                )
                return []

            headlines: list[NewsHeadline] = []

            for entry in feed.entries[:max_headlines]:
                # Parse publication date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except (TypeError, ValueError):
                        pass

                # Extract source from title if available
                # Google News format: "Headline - Source"
                title = entry.get("title", "")
                source = "Unknown"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    if len(parts) == 2:
                        title, source = parts

                headlines.append(
                    NewsHeadline(
                        title=title.strip(),
                        source=source.strip(),
                        url=entry.get("link", ""),
                        published=published,
                    )
                )

            logger.info(
                "Found %d headlines for %s",
                len(headlines),
                symbol,
            )
            return headlines

        except Exception as e:
            logger.error("Failed to fetch news for %s: %s", symbol, e)
            return []

    def get_headlines_text(
        self,
        symbol: str,
        max_headlines: int = 5,
    ) -> list[str]:
        """Fetch headlines as plain text strings.

        Args:
            symbol: The stock ticker symbol.
            max_headlines: Maximum number of headlines to return.

        Returns:
            List of headline strings.
        """
        headlines = self.get_headlines(symbol, max_headlines)
        return [h.title for h in headlines]

    def search_news(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[NewsHeadline]:
        """Search for news with a custom query.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.

        Returns:
            List of NewsHeadline objects.
        """
        encoded_query = quote(query)
        feed_url = self.GOOGLE_NEWS_RSS.format(query=encoded_query)

        logger.debug("Searching news: %s", query)

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                return []

            headlines: list[NewsHeadline] = []

            for entry in feed.entries[:max_results]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except (TypeError, ValueError):
                        pass

                title = entry.get("title", "")
                source = "Unknown"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    if len(parts) == 2:
                        title, source = parts

                headlines.append(
                    NewsHeadline(
                        title=title.strip(),
                        source=source.strip(),
                        url=entry.get("link", ""),
                        published=published,
                    )
                )

            return headlines

        except Exception as e:
            logger.error("Failed to search news: %s", e)
            return []
