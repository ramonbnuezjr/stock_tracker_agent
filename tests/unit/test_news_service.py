"""Unit tests for news service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.news_adapter import NewsAdapter, NewsHeadline
from src.services.news_service import NewsService


class TestNewsAdapter:
    """Tests for the NewsAdapter."""

    @patch("src.adapters.news_adapter.feedparser")
    def test_get_headlines(self, mock_feedparser: MagicMock) -> None:
        """Test fetching headlines from RSS."""
        mock_feedparser.parse.return_value = MagicMock(
            bozo=False,
            entries=[
                {
                    "title": "Apple announces new product - Reuters",
                    "link": "https://example.com/1",
                    "published_parsed": (2026, 1, 24, 12, 0, 0, 0, 0, 0),
                },
                {
                    "title": "Tech stocks rally - Bloomberg",
                    "link": "https://example.com/2",
                    "published_parsed": (2026, 1, 24, 11, 0, 0, 0, 0, 0),
                },
            ],
        )

        adapter = NewsAdapter()
        headlines = adapter.get_headlines("AAPL", max_headlines=2)

        assert len(headlines) == 2
        assert headlines[0].title == "Apple announces new product"
        assert headlines[0].source == "Reuters"
        assert headlines[1].source == "Bloomberg"

    @patch("src.adapters.news_adapter.feedparser")
    def test_get_headlines_empty(self, mock_feedparser: MagicMock) -> None:
        """Test handling empty feed."""
        mock_feedparser.parse.return_value = MagicMock(
            bozo=True,
            bozo_exception=Exception("Feed error"),
            entries=[],
        )

        adapter = NewsAdapter()
        headlines = adapter.get_headlines("INVALID")

        assert headlines == []

    @patch("src.adapters.news_adapter.feedparser")
    def test_get_headlines_text(self, mock_feedparser: MagicMock) -> None:
        """Test getting headlines as text."""
        mock_feedparser.parse.return_value = MagicMock(
            bozo=False,
            entries=[
                {
                    "title": "Apple stock rises - Reuters",
                    "link": "https://example.com/1",
                },
            ],
        )

        adapter = NewsAdapter()
        text = adapter.get_headlines_text("AAPL")

        assert len(text) == 1
        assert text[0] == "Apple stock rises"

    @patch("src.adapters.news_adapter.feedparser")
    def test_parse_title_without_source(
        self,
        mock_feedparser: MagicMock,
    ) -> None:
        """Test parsing title without source separator."""
        mock_feedparser.parse.return_value = MagicMock(
            bozo=False,
            entries=[
                {
                    "title": "Simple headline without source",
                    "link": "https://example.com/1",
                },
            ],
        )

        adapter = NewsAdapter()
        headlines = adapter.get_headlines("AAPL")

        assert headlines[0].title == "Simple headline without source"
        assert headlines[0].source == "Unknown"


class TestNewsService:
    """Tests for the NewsService."""

    @patch("src.services.news_service.NewsAdapter")
    def test_get_headlines_for_symbol(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test getting headlines for a symbol."""
        mock_adapter = MagicMock()
        mock_adapter.get_headlines.return_value = [
            NewsHeadline(
                title="Test headline",
                source="Test Source",
                url="https://example.com",
                published=datetime.utcnow(),
            ),
        ]
        mock_adapter_class.return_value = mock_adapter

        service = NewsService()
        headlines = service.get_headlines_for_symbol("AAPL")

        assert len(headlines) == 1
        assert headlines[0].title == "Test headline"
        mock_adapter.get_headlines.assert_called_once_with("AAPL", 5)

    @patch("src.services.news_service.NewsAdapter")
    def test_format_headlines_for_prompt(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test formatting headlines for LLM prompt."""
        mock_adapter = MagicMock()
        mock_adapter.get_headlines_text.return_value = [
            "First headline",
            "Second headline",
        ]
        mock_adapter_class.return_value = mock_adapter

        service = NewsService()
        formatted = service.format_headlines_for_prompt("AAPL")

        assert "1. First headline" in formatted
        assert "2. Second headline" in formatted

    @patch("src.services.news_service.NewsAdapter")
    def test_format_headlines_empty(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test formatting when no headlines available."""
        mock_adapter = MagicMock()
        mock_adapter.get_headlines_text.return_value = []
        mock_adapter_class.return_value = mock_adapter

        service = NewsService()
        formatted = service.format_headlines_for_prompt("INVALID")

        assert "No recent news" in formatted

    @patch("src.services.news_service.NewsAdapter")
    def test_get_market_news(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test getting general market news."""
        mock_adapter = MagicMock()
        mock_adapter.search_news.return_value = [
            NewsHeadline(
                title="Market news",
                source="Reuters",
                url="https://example.com",
            ),
        ]
        mock_adapter_class.return_value = mock_adapter

        service = NewsService()
        news = service.get_market_news()

        assert len(news) == 1
        mock_adapter.search_news.assert_called_once()
