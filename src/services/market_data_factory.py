"""Factory for creating MarketDataService with configured providers."""

from __future__ import annotations

from typing import List

from src.adapters.market_data_provider import MarketDataProvider
from src.adapters.providers.alpha_vantage_provider import AlphaVantageProvider
from src.adapters.providers.finnhub_provider import FinnhubProvider
from src.adapters.providers.twelve_data_provider import TwelveDataProvider
from src.adapters.providers.yahoo_finance_provider import YahooFinanceProvider
from src.config import Settings
from src.services.market_data_service import MarketDataService


def create_market_data_service(settings: Settings) -> MarketDataService:
    """Create MarketDataService with providers in priority order.

    Provider priority (default):
    1. Finnhub (if API key configured)
    2. Twelve Data (if API key configured)
    3. Alpha Vantage (if API key configured)
    4. Yahoo Finance (always available, last resort)

    Args:
        settings: Application settings with API keys.

    Returns:
        A MarketDataService instance with configured providers.
    """
    providers: List[MarketDataProvider] = []

    # Priority 1: Finnhub
    if settings.finnhub_api_key:
        providers.append(FinnhubProvider(settings.finnhub_api_key))

    # Priority 2: Twelve Data
    if settings.twelve_data_api_key:
        providers.append(TwelveDataProvider(settings.twelve_data_api_key))

    # Priority 3: Alpha Vantage
    if settings.alpha_vantage_api_key:
        providers.append(AlphaVantageProvider(settings.alpha_vantage_api_key))

    # Priority 4: Yahoo Finance (always available as fallback)
    providers.append(YahooFinanceProvider())

    return MarketDataService(providers)
