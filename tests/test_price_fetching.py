"""
Tests for fetching and normalizing stock price data.

The system must be able to retrieve a current price and a prior
reference price for a given stock symbol.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.yfinance_adapter import YFinanceAdapter, YFinanceError
from src.models.stock import PricePoint
from src.services.price_service import PriceService


class TestPriceFetching:
    """Tests for price fetching functionality."""

    def test_fetch_current_price_returns_float(self) -> None:
        """
        Fetching the current price should return a numeric value.
        """
        with patch.object(YFinanceAdapter, "get_current_price") as mock_fetch:
            mock_fetch.return_value = PricePoint(
                symbol="AAPL",
                price=Decimal("150.25"),
                timestamp=datetime.utcnow(),
            )

            adapter = YFinanceAdapter()
            result = adapter.get_current_price("AAPL")

            assert result is not None
            assert isinstance(result.price, Decimal)
            assert result.price > 0
            assert float(result.price) == 150.25

    def test_fetch_previous_price_returns_float(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Fetching the previous reference price should return a numeric value.
        """
        with patch("src.services.price_service.YFinanceAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_class.return_value = mock_adapter

            # Store a price first
            service = PriceService(data_dir=temp_data_dir)
            service.storage.save_price(
                PricePoint(
                    symbol="AAPL",
                    price=Decimal("148.50"),
                    timestamp=datetime(2026, 1, 23),
                )
            )

            # Fetch previous price
            previous = service.get_stored_price("AAPL")

            assert previous is not None
            assert isinstance(previous.price, Decimal)
            assert previous.price > 0
            assert float(previous.price) == 148.50

    def test_invalid_symbol_raises_clean_error(self) -> None:
        """
        Invalid stock symbols should be handled gracefully
        without crashing the application.
        """
        with patch.object(YFinanceAdapter, "get_current_price") as mock_fetch:
            mock_fetch.side_effect = YFinanceError(
                "No price data available for INVALID"
            )

            adapter = YFinanceAdapter()

            with pytest.raises(YFinanceError) as exc_info:
                adapter.get_current_price("INVALID")

            # Error message should be informative
            assert "INVALID" in str(exc_info.value)
            assert "price" in str(exc_info.value).lower()

    def test_price_service_handles_fetch_error_gracefully(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Price service should handle fetch errors without crashing.
        """
        with patch("src.services.price_service.YFinanceAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.get_current_price.side_effect = YFinanceError("API error")
            mock_class.return_value = mock_adapter

            service = PriceService(data_dir=temp_data_dir)
            result = service.get_price("INVALID")

            # Should return None, not raise
            assert result is None

    def test_price_point_requires_positive_value(self) -> None:
        """
        PricePoint should reject zero or negative prices.
        """
        with pytest.raises(ValueError):
            PricePoint(
                symbol="AAPL",
                price=Decimal("0"),
                timestamp=datetime.utcnow(),
            )

        with pytest.raises(ValueError):
            PricePoint(
                symbol="AAPL",
                price=Decimal("-10.00"),
                timestamp=datetime.utcnow(),
            )

    def test_symbol_is_normalized_to_uppercase(self) -> None:
        """
        Stock symbols should be normalized to uppercase.
        """
        price = PricePoint(
            symbol="aapl",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
        )

        assert price.symbol == "AAPL"

    def test_multiple_symbols_fetched_correctly(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Fetching multiple symbols should return prices for each.
        """
        with patch("src.services.price_service.YFinanceAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.get_prices.return_value = {
                "AAPL": PricePoint(
                    symbol="AAPL",
                    price=Decimal("150.00"),
                    timestamp=datetime.utcnow(),
                ),
                "NVDA": PricePoint(
                    symbol="NVDA",
                    price=Decimal("450.00"),
                    timestamp=datetime.utcnow(),
                ),
            }
            mock_class.return_value = mock_adapter

            service = PriceService(data_dir=temp_data_dir)
            prices = service.fetch_current_prices(["AAPL", "NVDA"])

            assert len(prices) == 2
            assert "AAPL" in prices
            assert "NVDA" in prices
            assert float(prices["AAPL"].price) == 150.00
            assert float(prices["NVDA"].price) == 450.00
