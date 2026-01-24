#!/usr/bin/env python3
"""Demo script to test multi-provider fallback without real API calls."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.adapters.market_data_exceptions import (
    ProviderUnavailableError,
    RateLimitError,
)
from src.adapters.providers.alpha_vantage_provider import AlphaVantageProvider
from src.adapters.providers.finnhub_provider import FinnhubProvider
from src.adapters.providers.twelve_data_provider import TwelveDataProvider
from src.adapters.providers.yahoo_finance_provider import YahooFinanceProvider
from src.models.market_data import PriceQuote
from src.services.market_data_service import MarketDataService


def test_scenario_1_primary_succeeds() -> None:
    """Test: Primary provider (Finnhub) succeeds immediately."""
    print("\n" + "=" * 60)
    print("SCENARIO 1: Primary Provider Succeeds")
    print("=" * 60)

    # Mock providers
    finnhub = MagicMock(spec=FinnhubProvider)
    finnhub.provider_name = "finnhub"
    finnhub.get_latest_price.return_value = PriceQuote(
        symbol="AAPL",
        price=Decimal("150.00"),
        provider_name="finnhub",
    )

    twelve_data = MagicMock(spec=TwelveDataProvider)
    twelve_data.provider_name = "twelve_data"

    service = MarketDataService([finnhub, twelve_data])

    quote = service.get_latest_price("AAPL")

    print(f"✅ Success! Got price: ${quote.price} from {quote.provider_name}")
    print(f"   Finnhub called: {finnhub.get_latest_price.called}")
    print(f"   Twelve Data called: {twelve_data.get_latest_price.called}")
    assert quote.provider_name == "finnhub"
    assert not twelve_data.get_latest_price.called


def test_scenario_2_fallback_on_rate_limit() -> None:
    """Test: Primary rate-limited, secondary succeeds."""
    print("\n" + "=" * 60)
    print("SCENARIO 2: Primary Rate-Limited, Secondary Succeeds")
    print("=" * 60)

    finnhub = MagicMock(spec=FinnhubProvider)
    finnhub.provider_name = "finnhub"
    finnhub.get_latest_price.side_effect = RateLimitError(
        "finnhub",
        "Rate limit exceeded",
    )

    twelve_data = MagicMock(spec=TwelveDataProvider)
    twelve_data.provider_name = "twelve_data"
    twelve_data.get_latest_price.return_value = PriceQuote(
        symbol="AAPL",
        price=Decimal("150.50"),
        provider_name="twelve_data",
    )

    service = MarketDataService([finnhub, twelve_data])

    quote = service.get_latest_price("AAPL")

    print(f"✅ Success! Got price: ${quote.price} from {quote.provider_name}")
    print(f"   Finnhub called: {finnhub.get_latest_price.called}")
    print(f"   Twelve Data called: {twelve_data.get_latest_price.called}")
    assert quote.provider_name == "twelve_data"
    assert finnhub.get_latest_price.called
    assert twelve_data.get_latest_price.called


def test_scenario_3_all_fail() -> None:
    """Test: All providers fail."""
    print("\n" + "=" * 60)
    print("SCENARIO 3: All Providers Fail")
    print("=" * 60)

    finnhub = MagicMock(spec=FinnhubProvider)
    finnhub.provider_name = "finnhub"
    finnhub.get_latest_price.side_effect = RateLimitError("finnhub", "Rate limit")

    twelve_data = MagicMock(spec=TwelveDataProvider)
    twelve_data.provider_name = "twelve_data"
    twelve_data.get_latest_price.side_effect = ProviderUnavailableError(
        "twelve_data",
        "Service down",
    )

    alpha_vantage = MagicMock(spec=AlphaVantageProvider)
    alpha_vantage.provider_name = "alpha_vantage"
    alpha_vantage.get_latest_price.side_effect = ProviderUnavailableError(
        "alpha_vantage",
        "API key invalid",
    )

    yahoo = MagicMock(spec=YahooFinanceProvider)
    yahoo.provider_name = "yahoo_finance"
    yahoo.get_latest_price.side_effect = ProviderUnavailableError(
        "yahoo_finance",
        "Network error",
    )

    service = MarketDataService([finnhub, twelve_data, alpha_vantage, yahoo])

    try:
        service.get_latest_price("AAPL")
        print("❌ Should have raised MarketDataUnavailableError")
        assert False
    except Exception as e:
        print(f"✅ Correctly raised: {type(e).__name__}")
        print(f"   Message: {e}")
        assert "All providers failed" in str(e)


def test_scenario_4_caching() -> None:
    """Test: Caching prevents redundant API calls."""
    print("\n" + "=" * 60)
    print("SCENARIO 4: Caching Prevents Redundant Calls")
    print("=" * 60)

    finnhub = MagicMock(spec=FinnhubProvider)
    finnhub.provider_name = "finnhub"
    finnhub.get_latest_price.return_value = PriceQuote(
        symbol="AAPL",
        price=Decimal("150.00"),
        provider_name="finnhub",
    )

    service = MarketDataService([finnhub], cache_ttl_seconds=60)

    # First call
    quote1 = service.get_latest_price("AAPL")
    print(f"✅ First call: ${quote1.price}")

    # Second call (should use cache)
    quote2 = service.get_latest_price("AAPL")
    print(f"✅ Second call: ${quote2.price} (from cache)")

    print(f"   Finnhub called {finnhub.get_latest_price.call_count} times")
    assert finnhub.get_latest_price.call_count == 1
    assert quote1.price == quote2.price


def test_scenario_5_provider_priority() -> None:
    """Test: Providers tried in correct priority order."""
    print("\n" + "=" * 60)
    print("SCENARIO 5: Provider Priority Order")
    print("=" * 60)

    finnhub = MagicMock(spec=FinnhubProvider)
    finnhub.provider_name = "finnhub"
    finnhub.get_latest_price.side_effect = RateLimitError("finnhub", "Rate limit")

    twelve_data = MagicMock(spec=TwelveDataProvider)
    twelve_data.provider_name = "twelve_data"
    twelve_data.get_latest_price.side_effect = ProviderUnavailableError(
        "twelve_data",
        "Service down",
    )

    alpha_vantage = MagicMock(spec=AlphaVantageProvider)
    alpha_vantage.provider_name = "alpha_vantage"
    alpha_vantage.get_latest_price.return_value = PriceQuote(
        symbol="AAPL",
        price=Decimal("150.25"),
        provider_name="alpha_vantage",
    )

    yahoo = MagicMock(spec=YahooFinanceProvider)
    yahoo.provider_name = "yahoo_finance"

    service = MarketDataService([finnhub, twelve_data, alpha_vantage, yahoo])

    quote = service.get_latest_price("AAPL")

    print(f"✅ Success! Got price: ${quote.price} from {quote.provider_name}")
    print(f"   Priority order verified:")
    print(f"   1. Finnhub called: {finnhub.get_latest_price.called}")
    print(f"   2. Twelve Data called: {twelve_data.get_latest_price.called}")
    print(f"   3. Alpha Vantage called: {alpha_vantage.get_latest_price.called}")
    print(f"   4. Yahoo Finance called: {yahoo.get_latest_price.called}")

    assert quote.provider_name == "alpha_vantage"
    assert finnhub.get_latest_price.called
    assert twelve_data.get_latest_price.called
    assert alpha_vantage.get_latest_price.called
    assert not yahoo.get_latest_price.called  # Should stop before Yahoo


def main() -> None:
    """Run all test scenarios."""
    print("\n" + "=" * 60)
    print("MULTI-PROVIDER FALLBACK DEMO")
    print("Testing without real API calls")
    print("=" * 60)

    try:
        test_scenario_1_primary_succeeds()
        test_scenario_2_fallback_on_rate_limit()
        test_scenario_3_all_fail()
        test_scenario_4_caching()
        test_scenario_5_provider_priority()

        print("\n" + "=" * 60)
        print("✅ ALL SCENARIOS PASSED!")
        print("=" * 60)
        print("\nThe multi-provider fallback system is working correctly:")
        print("  • Primary provider succeeds → uses it immediately")
        print("  • Primary rate-limited → falls back to secondary")
        print("  • All providers fail → raises clean error")
        print("  • Caching prevents redundant API calls")
        print("  • Providers tried in priority order")
        print()

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
