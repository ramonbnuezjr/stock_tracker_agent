"""Price service for fetching and comparing stock prices."""

import logging
from decimal import Decimal
from pathlib import Path

from src.adapters.storage_adapter import StorageAdapter
from src.adapters.yfinance_adapter import YFinanceAdapter, YFinanceError
from src.models.stock import PriceChange, PricePoint

logger = logging.getLogger(__name__)


class PriceService:
    """Service for fetching stock prices and detecting threshold breaches.

    Args:
        data_dir: Directory for local data storage.
        threshold: Percentage threshold for price change alerts.

    Returns:
        A PriceService instance.
    """

    def __init__(
        self,
        data_dir: Path,
        threshold: Decimal = Decimal("1.5"),
    ) -> None:
        """Initialize the price service.

        Args:
            data_dir: Directory for local data storage.
            threshold: Percentage threshold for alerts (default: 1.5%).
        """
        self.threshold = threshold
        self.storage = StorageAdapter(data_dir)
        self.yfinance = YFinanceAdapter()

    def fetch_current_prices(
        self,
        symbols: list[str],
    ) -> dict[str, PricePoint]:
        """Fetch current prices for a list of symbols.

        Args:
            symbols: List of stock ticker symbols.

        Returns:
            Dictionary mapping symbols to their current PricePoints.
        """
        logger.info("Fetching prices for %d symbols", len(symbols))
        return self.yfinance.get_prices(symbols)

    def get_price_changes(
        self,
        symbols: list[str],
    ) -> list[PriceChange]:
        """Fetch prices and calculate changes from previous values.

        Args:
            symbols: List of stock ticker symbols.

        Returns:
            List of PriceChange objects for all symbols.
        """
        changes: list[PriceChange] = []

        # Fetch current prices
        current_prices = self.fetch_current_prices(symbols)

        for symbol in symbols:
            symbol = symbol.upper()

            if symbol not in current_prices:
                logger.warning("No current price for %s, skipping", symbol)
                continue

            current = current_prices[symbol]

            # Get previous price from storage
            previous = self.storage.get_latest_price(symbol)

            # Save current price
            self.storage.save_price(current)

            if previous is None:
                logger.info(
                    "No previous price for %s, storing current: %s",
                    symbol,
                    current.price,
                )
                continue

            # Calculate change
            change = PriceChange.calculate(
                symbol=symbol,
                previous=previous,
                current=current,
                threshold=self.threshold,
            )
            changes.append(change)

            logger.info(
                "%s: %s -> %s (%.2f%%)",
                symbol,
                previous.price,
                current.price,
                change.change_percent,
            )

        return changes

    def get_threshold_breaches(
        self,
        symbols: list[str],
    ) -> list[PriceChange]:
        """Get price changes that exceed the threshold.

        Args:
            symbols: List of stock ticker symbols.

        Returns:
            List of PriceChange objects that exceeded the threshold.
        """
        all_changes = self.get_price_changes(symbols)
        breaches = [c for c in all_changes if c.threshold_exceeded]

        if breaches:
            logger.info(
                "%d threshold breaches detected: %s",
                len(breaches),
                ", ".join(c.symbol for c in breaches),
            )
        else:
            logger.info("No threshold breaches detected")

        return breaches

    def get_price(self, symbol: str) -> PricePoint | None:
        """Get the current price for a single symbol.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The current PricePoint or None if fetch failed.
        """
        try:
            return self.yfinance.get_current_price(symbol)
        except YFinanceError:
            return None

    def get_stored_price(self, symbol: str) -> PricePoint | None:
        """Get the most recent stored price for a symbol.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The stored PricePoint or None if not found.
        """
        return self.storage.get_latest_price(symbol)

    def get_price_history(
        self,
        symbol: str,
        limit: int = 100,
    ) -> list[PricePoint]:
        """Get stored price history for a symbol.

        Args:
            symbol: The stock ticker symbol.
            limit: Maximum number of records to return.

        Returns:
            List of PricePoint objects, most recent first.
        """
        return self.storage.get_price_history(symbol, limit)
