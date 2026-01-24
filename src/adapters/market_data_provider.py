"""Market data provider interface."""

from __future__ import annotations

from typing import Protocol

from src.adapters.market_data_exceptions import (
    ProviderUnavailableError,
    RateLimitError,
)
from src.models.market_data import PriceQuote


class MarketDataProvider(Protocol):
    """Protocol for market data providers.

    All providers must implement get_latest_price().
    """

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Fetch the latest price for a stock symbol.

        Args:
            symbol: The stock ticker symbol (e.g., 'AAPL').

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            RateLimitError: If provider rate limit is exceeded.
            ProviderUnavailableError: If provider is unavailable.
        """
        ...
