"""
Tests for detecting meaningful stock price movement.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from src.models.stock import PriceChange, PricePoint
from src.services.price_service import PriceService


class TestThresholdDetection:
    """Tests for threshold detection functionality."""

    def test_threshold_exceeded_returns_true(
        self,
        sample_stock_prices: Dict[str, float],
        sample_threshold: float,
    ) -> None:
        """
        Returns True when price movement exceeds configured threshold.
        """
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal(str(sample_stock_prices["previous"])),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal(str(sample_stock_prices["current"])),
            timestamp=datetime(2026, 1, 24),
        )

        # 2.5% change with 1.5% threshold
        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal(str(sample_threshold * 100)),  # Convert to percentage
        )

        assert change.threshold_exceeded is True
        assert change.change_percent == Decimal("2.5")

    def test_threshold_not_exceeded_returns_false(
        self,
        sample_threshold: float,
    ) -> None:
        """
        Returns False when price movement is below threshold.
        """
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("100.50"),  # Only 0.5% change
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal(str(sample_threshold * 100)),
        )

        assert change.threshold_exceeded is False
        assert change.change_percent == Decimal("0.5")

    def test_zero_or_negative_prices_are_rejected(self) -> None:
        """
        Invalid price inputs should be rejected explicitly.
        """
        # Zero price should raise
        with pytest.raises(ValueError):
            PricePoint(
                symbol="AAPL",
                price=Decimal("0"),
                timestamp=datetime.utcnow(),
            )

        # Negative price should raise
        with pytest.raises(ValueError):
            PricePoint(
                symbol="AAPL",
                price=Decimal("-50.00"),
                timestamp=datetime.utcnow(),
            )

        # PriceChange should also reject invalid prices
        with pytest.raises(ValueError):
            PriceChange(
                symbol="AAPL",
                previous_price=Decimal("0"),
                current_price=Decimal("100.00"),
                change_amount=Decimal("100.00"),
                change_percent=Decimal("100.00"),
            )

    def test_negative_price_change_detection(self) -> None:
        """
        Negative price changes should also trigger threshold detection.
        """
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("95.00"),  # -5% change
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal("1.5"),
        )

        assert change.threshold_exceeded is True
        assert change.change_percent == Decimal("-5.00")
        assert change.direction == "down"

    def test_exact_threshold_triggers_alert(self) -> None:
        """
        Price change exactly at threshold should trigger alert.
        """
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("101.50"),  # Exactly 1.5%
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal("1.5"),
        )

        assert change.threshold_exceeded is True

    def test_price_service_filters_threshold_breaches(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Price service should correctly filter threshold breaches.
        """
        with patch("src.services.price_service.YFinanceAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_class.return_value = mock_adapter

            service = PriceService(
                data_dir=temp_data_dir,
                threshold=Decimal("2.0"),  # 2% threshold
            )

            # Store initial prices
            mock_adapter.get_prices.return_value = {
                "AAPL": PricePoint(
                    symbol="AAPL",
                    price=Decimal("100.00"),
                    timestamp=datetime(2026, 1, 23),
                ),
                "NVDA": PricePoint(
                    symbol="NVDA",
                    price=Decimal("200.00"),
                    timestamp=datetime(2026, 1, 23),
                ),
            }
            service.get_price_changes(["AAPL", "NVDA"])

            # New prices: AAPL +3% (breach), NVDA +1% (no breach)
            mock_adapter.get_prices.return_value = {
                "AAPL": PricePoint(
                    symbol="AAPL",
                    price=Decimal("103.00"),
                    timestamp=datetime(2026, 1, 24),
                ),
                "NVDA": PricePoint(
                    symbol="NVDA",
                    price=Decimal("202.00"),
                    timestamp=datetime(2026, 1, 24),
                ),
            }
            breaches = service.get_threshold_breaches(["AAPL", "NVDA"])

            assert len(breaches) == 1
            assert breaches[0].symbol == "AAPL"
            assert breaches[0].threshold_exceeded is True

    def test_direction_property(self) -> None:
        """
        Direction property should correctly identify up/down/unchanged.
        """
        up_change = PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            change_amount=Decimal("5.00"),
            change_percent=Decimal("5.00"),
        )
        assert up_change.direction == "up"

        down_change = PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("95.00"),
            change_amount=Decimal("-5.00"),
            change_percent=Decimal("-5.00"),
        )
        assert down_change.direction == "down"

        no_change = PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("100.00"),
            change_amount=Decimal("0"),
            change_percent=Decimal("0"),
        )
        assert no_change.direction == "unchanged"
