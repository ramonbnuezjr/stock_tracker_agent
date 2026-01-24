"""Tests for market data multi-provider fallback."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.market_data_exceptions import (
    MarketDataUnavailableError,
    ProviderUnavailableError,
    RateLimitError,
)
from src.adapters.providers.alpha_vantage_provider import AlphaVantageProvider
from src.adapters.providers.finnhub_provider import FinnhubProvider
from src.adapters.providers.twelve_data_provider import TwelveDataProvider
from src.adapters.providers.yahoo_finance_provider import YahooFinanceProvider
from src.models.market_data import PriceQuote
from src.services.market_data_service import MarketDataService


class TestProviderFallback:
    """Tests for provider fallback logic."""

    def test_fallback_on_rate_limit(self) -> None:
        """Fallback occurs when primary provider rate-limits."""
        # Create mock providers
        provider1 = MagicMock()
        provider1.provider_name = "finnhub"
        provider1.get_latest_price.side_effect = RateLimitError(
            "finnhub",
            "Rate limit exceeded",
        )

        provider2 = MagicMock()
        provider2.provider_name = "twelve_data"
        provider2.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="twelve_data",
        )

        service = MarketDataService([provider1, provider2])

        quote = service.get_latest_price("AAPL")

        assert quote.symbol == "AAPL"
        assert quote.price == Decimal("150.00")
        assert quote.provider_name == "twelve_data"
        provider1.get_latest_price.assert_called_once_with("AAPL")
        provider2.get_latest_price.assert_called_once_with("AAPL")

    def test_fallback_on_provider_unavailable(self) -> None:
        """Fallback occurs when primary provider is unavailable."""
        provider1 = MagicMock()
        provider1.provider_name = "finnhub"
        provider1.get_latest_price.side_effect = ProviderUnavailableError(
            "finnhub",
            "Service unavailable",
        )

        provider2 = MagicMock()
        provider2.provider_name = "alpha_vantage"
        provider2.get_latest_price.return_value = PriceQuote(
            symbol="NVDA",
            price=Decimal("500.00"),
            timestamp=datetime.utcnow(),
            provider_name="alpha_vantage",
        )

        service = MarketDataService([provider1, provider2])

        quote = service.get_latest_price("NVDA")

        assert quote.symbol == "NVDA"
        assert quote.price == Decimal("500.00")
        assert quote.provider_name == "alpha_vantage"

    def test_all_providers_fail_raises_error(self) -> None:
        """Failure is clean if all providers are unavailable."""
        provider1 = MagicMock()
        provider1.provider_name = "finnhub"
        provider1.get_latest_price.side_effect = RateLimitError(
            "finnhub",
            "Rate limit",
        )

        provider2 = MagicMock()
        provider2.provider_name = "twelve_data"
        provider2.get_latest_price.side_effect = ProviderUnavailableError(
            "twelve_data",
            "Service down",
        )

        provider3 = MagicMock()
        provider3.provider_name = "alpha_vantage"
        provider3.get_latest_price.side_effect = ProviderUnavailableError(
            "alpha_vantage",
            "API key invalid",
        )

        service = MarketDataService([provider1, provider2, provider3])

        with pytest.raises(MarketDataUnavailableError) as exc_info:
            service.get_latest_price("MSFT")

        assert exc_info.value.symbol == "MSFT"
        assert "All providers failed" in str(exc_info.value)

    def test_stops_on_first_success(self) -> None:
        """Service stops on first successful response."""
        provider1 = MagicMock()
        provider1.provider_name = "finnhub"
        provider1.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="finnhub",
        )

        provider2 = MagicMock()
        provider2.provider_name = "twelve_data"

        service = MarketDataService([provider1, provider2])

        quote = service.get_latest_price("AAPL")

        assert quote.provider_name == "finnhub"
        provider1.get_latest_price.assert_called_once()
        provider2.get_latest_price.assert_not_called()


class TestCaching:
    """Tests for price caching."""

    def test_cache_prevents_redundant_api_calls(self) -> None:
        """Cache prevents redundant API calls."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="finnhub",
        )

        service = MarketDataService([provider], cache_ttl_seconds=60)

        # First call
        quote1 = service.get_latest_price("AAPL")
        assert quote1.price == Decimal("150.00")

        # Second call should use cache
        quote2 = service.get_latest_price("AAPL")
        assert quote2.price == Decimal("150.00")

        # Provider should only be called once
        provider.get_latest_price.assert_called_once_with("AAPL")

    def test_cache_expires_after_ttl(self) -> None:
        """Cache expires after TTL and makes new API call."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="finnhub",
        )

        service = MarketDataService([provider], cache_ttl_seconds=1)

        # First call
        service.get_latest_price("AAPL")

        # Wait for cache to expire
        import time

        time.sleep(1.1)

        # Second call should hit API again
        service.get_latest_price("AAPL")

        # Provider should be called twice
        assert provider.get_latest_price.call_count == 2

    def test_cache_checked_before_provider_calls(self) -> None:
        """Cache is checked before any provider calls."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="finnhub",
        )

        service = MarketDataService([provider])

        # First call populates cache
        service.get_latest_price("AAPL")
        provider.reset_mock()

        # Second call should use cache
        service.get_latest_price("AAPL")

        # Provider should not be called
        provider.get_latest_price.assert_not_called()


class TestProviderSpecificErrors:
    """Tests that provider-specific errors do not leak upward."""

    def test_rate_limit_error_handled_gracefully(self) -> None:
        """RateLimitError from provider is handled gracefully."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.side_effect = RateLimitError(
            "finnhub",
            "Rate limit exceeded",
        )

        service = MarketDataService([provider])

        with pytest.raises(MarketDataUnavailableError):
            service.get_latest_price("AAPL")

    def test_provider_unavailable_error_handled_gracefully(self) -> None:
        """ProviderUnavailableError is handled gracefully."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.side_effect = ProviderUnavailableError(
            "finnhub",
            "Service unavailable",
        )

        service = MarketDataService([provider])

        with pytest.raises(MarketDataUnavailableError):
            service.get_latest_price("AAPL")

    def test_generic_exception_handled_gracefully(self) -> None:
        """Generic exceptions from providers are handled gracefully."""
        provider = MagicMock()
        provider.provider_name = "finnhub"
        provider.get_latest_price.side_effect = ValueError("Unexpected error")

        service = MarketDataService([provider])

        with pytest.raises(MarketDataUnavailableError):
            service.get_latest_price("AAPL")


class TestProviderPriority:
    """Tests for provider priority ordering."""

    def test_providers_tried_in_order(self) -> None:
        """Providers are tried in the order specified."""
        provider1 = MagicMock()
        provider1.provider_name = "finnhub"
        provider1.get_latest_price.side_effect = RateLimitError(
            "finnhub",
            "Rate limit",
        )

        provider2 = MagicMock()
        provider2.provider_name = "twelve_data"
        provider2.get_latest_price.side_effect = RateLimitError(
            "twelve_data",
            "Rate limit",
        )

        provider3 = MagicMock()
        provider3.provider_name = "alpha_vantage"
        provider3.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
            provider_name="alpha_vantage",
        )

        service = MarketDataService([provider1, provider2, provider3])

        quote = service.get_latest_price("AAPL")

        assert quote.provider_name == "alpha_vantage"
        provider1.get_latest_price.assert_called_once()
        provider2.get_latest_price.assert_called_once()
        provider3.get_latest_price.assert_called_once()


class TestRealProviderAdapters:
    """Tests for real provider adapter implementations."""

    def test_yahoo_finance_provider_raises_rate_limit_on_429(self) -> None:
        """Yahoo Finance provider raises RateLimitError on 429."""
        provider = YahooFinanceProvider()

        with patch("yfinance.Ticker") as mock_ticker:
            mock_info = {"error": "429 Too Many Requests"}
            mock_ticker.return_value.info = mock_info

            with pytest.raises(RateLimitError) as exc_info:
                provider.get_latest_price("AAPL")

            assert exc_info.value.provider == "yahoo_finance"

    def test_alpha_vantage_provider_requires_api_key(self) -> None:
        """Alpha Vantage provider requires API key."""
        provider = AlphaVantageProvider(api_key="")

        with pytest.raises(ProviderUnavailableError) as exc_info:
            provider.get_latest_price("AAPL")

        assert "API key not configured" in str(exc_info.value)

    def test_finnhub_provider_requires_api_key(self) -> None:
        """Finnhub provider requires API key."""
        provider = FinnhubProvider(api_key="")

        with pytest.raises(ProviderUnavailableError) as exc_info:
            provider.get_latest_price("AAPL")

        assert "API key not configured" in str(exc_info.value)

    def test_twelve_data_provider_requires_api_key(self) -> None:
        """Twelve Data provider requires API key."""
        provider = TwelveDataProvider(api_key="")

        with pytest.raises(ProviderUnavailableError) as exc_info:
            provider.get_latest_price("AAPL")

        assert "API key not configured" in str(exc_info.value)
