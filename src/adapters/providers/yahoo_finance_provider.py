"""Yahoo Finance provider adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import yfinance as yf

from src.adapters.market_data_exceptions import (
    ProviderUnavailableError,
    RateLimitError,
)
from src.models.market_data import PriceQuote

logger = logging.getLogger(__name__)


class YahooFinanceProvider:
    """Yahoo Finance market data provider.

    Returns:
        A YahooFinanceProvider instance.
    """

    def __init__(self) -> None:
        """Initialize the Yahoo Finance provider."""
        self.provider_name = "yahoo_finance"

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Fetch the latest price from Yahoo Finance.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            RateLimitError: If Yahoo Finance rate limits the request.
            ProviderUnavailableError: If Yahoo Finance is unavailable.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Check for rate limiting (429 status)
            if isinstance(info, dict) and "error" in info:
                error_msg = str(info.get("error", ""))
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    logger.warning(
                        "Yahoo Finance rate limit for %s",
                        symbol,
                    )
                    raise RateLimitError(
                        self.provider_name,
                        "Too many requests",
                    )

            # Try different price fields in order of preference
            price = None
            for field in [
                "regularMarketPrice",
                "currentPrice",
                "previousClose",
            ]:
                if field in info and info[field] is not None:
                    price = info[field]
                    break

            if price is None:
                # Fallback: try to get from history
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise ProviderUnavailableError(
                        self.provider_name,
                        f"No price data available for {symbol}",
                    )
                price = float(hist["Close"].iloc[-1])

            logger.debug(
                "Yahoo Finance: %s = %s",
                symbol,
                price,
            )

            return PriceQuote(
                symbol=symbol.upper(),
                price=Decimal(str(price)),
                timestamp=datetime.utcnow(),
                provider_name=self.provider_name,
            )

        except RateLimitError:
            raise
        except ProviderUnavailableError:
            raise
        except Exception as e:
            error_str = str(e)
            # Check for rate limit indicators in exception
            if "429" in error_str or "Too Many Requests" in error_str:
                raise RateLimitError(
                    self.provider_name,
                    error_str,
                )
            logger.error(
                "Yahoo Finance error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
