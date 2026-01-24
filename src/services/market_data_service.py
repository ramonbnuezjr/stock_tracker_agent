"""Market data service with multi-provider fallback and caching."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.adapters.market_data_exceptions import MarketDataUnavailableError
from src.adapters.market_data_provider import MarketDataProvider
from src.models.market_data import PriceQuote

logger = logging.getLogger(__name__)


class _CacheEntry:
    """Internal cache entry for price quotes.

    Args:
        quote: The cached price quote.
        expires_at: When the cache entry expires.
    """

    def __init__(self, quote: PriceQuote, expires_at: datetime) -> None:
        """Initialize cache entry.

        Args:
            quote: The price quote to cache.
            expires_at: Expiration timestamp.
        """
        self.quote = quote
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if cache entry is expired.

        Returns:
            True if expired, False otherwise.
        """
        return datetime.utcnow() >= self.expires_at


class MarketDataService:
    """Service for fetching market data with provider fallback.

    Orchestrates multiple market data providers with automatic fallback
    on rate limits or failures. Includes caching to prevent redundant
    API calls.

    Args:
        providers: Ordered list of providers to try (priority order).
        cache_ttl_seconds: Cache TTL in seconds (default: 60).

    Returns:
        A MarketDataService instance.
    """

    def __init__(
        self,
        providers: List[MarketDataProvider],
        cache_ttl_seconds: int = 60,
    ) -> None:
        """Initialize the market data service.

        Args:
            providers: Ordered list of providers (highest priority first).
            cache_ttl_seconds: Cache TTL in seconds.
        """
        self.providers = providers
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: Dict[str, _CacheEntry] = {}

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Get the latest price for a symbol with fallback.

        Checks cache first, then tries providers in order until
        one succeeds. Falls back on rate limits or failures.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            MarketDataUnavailableError: If all providers fail.
        """
        symbol_upper = symbol.upper()

        # Check cache first
        cached = self._get_from_cache(symbol_upper)
        if cached:
            logger.debug(
                "Cache hit for %s (provider: %s)",
                symbol_upper,
                cached.provider_name,
            )
            return cached

        # Try providers in order
        last_error: Optional[Exception] = None

        for provider in self.providers:
            provider_name = getattr(provider, "provider_name", "unknown")
            try:
                logger.debug(
                    "Trying %s for %s",
                    provider_name,
                    symbol_upper,
                )
                quote = provider.get_latest_price(symbol_upper)

                # Cache successful result
                self._cache_quote(quote)

                logger.info(
                    "Price fetched for %s via %s: %s",
                    symbol_upper,
                    provider_name,
                    quote.price,
                )
                return quote

            except Exception as e:
                # Log fallback attempt
                error_type = type(e).__name__
                logger.warning(
                    "%s failed for %s (%s), trying next provider",
                    provider_name,
                    symbol_upper,
                    error_type,
                )
                last_error = e
                continue

        # All providers failed
        error_msg = "All providers failed"
        if last_error:
            error_msg += f": {last_error}"

        logger.error(
            "Unable to fetch price for %s: %s",
            symbol_upper,
            error_msg,
        )
        raise MarketDataUnavailableError(symbol_upper, error_msg)

    def _get_from_cache(self, symbol: str) -> Optional[PriceQuote]:
        """Get quote from cache if valid.

        Args:
            symbol: The stock symbol.

        Returns:
            Cached quote if valid, None otherwise.
        """
        entry = self._cache.get(symbol)
        if entry and not entry.is_expired():
            return entry.quote

        # Remove expired entry
        if entry:
            del self._cache[symbol]

        return None

    def _cache_quote(self, quote: PriceQuote) -> None:
        """Cache a price quote.

        Args:
            quote: The quote to cache.
        """
        expires_at = datetime.utcnow() + self.cache_ttl
        self._cache[quote.symbol] = _CacheEntry(quote, expires_at)

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._cache.clear()
        logger.debug("Price cache cleared")
