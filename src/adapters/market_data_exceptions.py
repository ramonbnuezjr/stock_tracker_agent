"""Exceptions for market data providers."""

from __future__ import annotations


class MarketDataError(Exception):
    """Base exception for market data errors."""

    pass


class RateLimitError(MarketDataError):
    """Raised when a provider rate limit is exceeded.

    Args:
        provider: Name of the provider that rate-limited.
        message: Error message.
    """

    def __init__(self, provider: str, message: str = "") -> None:
        """Initialize rate limit error.

        Args:
            provider: Provider name.
            message: Optional error message.
        """
        self.provider = provider
        msg = f"Rate limit exceeded for {provider}"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class ProviderUnavailableError(MarketDataError):
    """Raised when a provider is unavailable or returns an error.

    Args:
        provider: Name of the provider that failed.
        message: Error message.
    """

    def __init__(self, provider: str, message: str = "") -> None:
        """Initialize provider unavailable error.

        Args:
            provider: Provider name.
            message: Optional error message.
        """
        self.provider = provider
        msg = f"Provider {provider} unavailable"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class MarketDataUnavailableError(MarketDataError):
    """Raised when all providers fail to return data.

    Args:
        symbol: Stock symbol that failed.
        message: Error message.
    """

    def __init__(self, symbol: str, message: str = "") -> None:
        """Initialize market data unavailable error.

        Args:
            symbol: Stock symbol.
            message: Optional error message.
        """
        self.symbol = symbol
        msg = f"Market data unavailable for {symbol}"
        if message:
            msg += f": {message}"
        super().__init__(msg)
