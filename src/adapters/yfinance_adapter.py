"""Yahoo Finance adapter for fetching stock prices."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

import yfinance as yf

from src.models.stock import PricePoint

logger = logging.getLogger(__name__)


class YFinanceError(Exception):
    """Error fetching data from Yahoo Finance."""

    pass


class YFinanceAdapter:
    """Adapter for fetching stock prices from Yahoo Finance.

    Returns:
        A YFinanceAdapter instance.
    """

    def __init__(self) -> None:
        """Initialize the Yahoo Finance adapter."""
        pass

    def get_current_price(self, symbol: str) -> PricePoint:
        """Fetch the current price for a stock symbol.

        Args:
            symbol: The stock ticker symbol (e.g., 'AAPL').

        Returns:
            A PricePoint with the current price.

        Raises:
            YFinanceError: If unable to fetch the price.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

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
                    raise YFinanceError(
                        f"No price data available for {symbol}"
                    )
                price = float(hist["Close"].iloc[-1])

            currency = info.get("currency", "USD")

            logger.debug(
                "Fetched price for %s: %s %s",
                symbol,
                price,
                currency,
            )

            return PricePoint(
                symbol=symbol.upper(),
                price=Decimal(str(price)),
                currency=currency,
                timestamp=datetime.utcnow(),
            )

        except YFinanceError:
            raise
        except Exception as e:
            logger.error("Failed to fetch price for %s: %s", symbol, e)
            raise YFinanceError(f"Failed to fetch price for {symbol}: {e}")

    def get_prices(self, symbols: list) -> Dict[str, PricePoint]:
        """Fetch current prices for multiple symbols.

        Args:
            symbols: List of stock ticker symbols.

        Returns:
            Dictionary mapping symbols to PricePoints.
        """
        results: Dict[str, PricePoint] = {}

        for symbol in symbols:
            try:
                results[symbol.upper()] = self.get_current_price(symbol)
            except YFinanceError as e:
                logger.warning("Skipping %s: %s", symbol, e)

        return results

    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid and has price data.

        Args:
            symbol: The stock ticker symbol to validate.

        Returns:
            True if the symbol is valid and has price data.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Check if we got meaningful data
            return (
                info is not None
                and "regularMarketPrice" in info
                and info["regularMarketPrice"] is not None
            )
        except Exception:
            return False

    def get_company_name(self, symbol: str) -> Optional[str]:
        """Get the company name for a symbol.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The company name or None if not found.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("longName") or info.get("shortName")
        except Exception:
            return None
