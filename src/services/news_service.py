"""News service for fetching stock-related headlines."""

import logging

from src.adapters.news_adapter import NewsAdapter, NewsHeadline

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and managing news headlines.

    Returns:
        A NewsService instance.
    """

    def __init__(self, timeout: int = 10) -> None:
        """Initialize the news service.

        Args:
            timeout: Request timeout in seconds.
        """
        self.adapter = NewsAdapter(timeout=timeout)

    def get_headlines_for_symbol(
        self,
        symbol: str,
        max_headlines: int = 5,
    ) -> list[NewsHeadline]:
        """Get recent news headlines for a stock symbol.

        Args:
            symbol: The stock ticker symbol.
            max_headlines: Maximum number of headlines to return.

        Returns:
            List of NewsHeadline objects.
        """
        logger.info("Fetching news for %s", symbol)
        return self.adapter.get_headlines(symbol, max_headlines)

    def get_headlines_text(
        self,
        symbol: str,
        max_headlines: int = 5,
    ) -> list[str]:
        """Get headlines as plain text for LLM context.

        Args:
            symbol: The stock ticker symbol.
            max_headlines: Maximum number of headlines.

        Returns:
            List of headline strings.
        """
        return self.adapter.get_headlines_text(symbol, max_headlines)

    def format_headlines_for_prompt(
        self,
        symbol: str,
        max_headlines: int = 5,
    ) -> str:
        """Format headlines as a string for LLM prompts.

        Args:
            symbol: The stock ticker symbol.
            max_headlines: Maximum number of headlines.

        Returns:
            Formatted string with numbered headlines.
        """
        headlines = self.get_headlines_text(symbol, max_headlines)

        if not headlines:
            return "No recent news headlines available."

        formatted = []
        for i, headline in enumerate(headlines, 1):
            formatted.append(f"{i}. {headline}")

        return "\n".join(formatted)

    def get_market_news(self, max_headlines: int = 5) -> list[NewsHeadline]:
        """Get general market news headlines.

        Args:
            max_headlines: Maximum number of headlines.

        Returns:
            List of NewsHeadline objects.
        """
        return self.adapter.search_news("stock market today", max_headlines)
