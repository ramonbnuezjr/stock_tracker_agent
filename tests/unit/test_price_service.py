"""Unit tests for price service."""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.yfinance_adapter import YFinanceError
from src.models.stock import PricePoint
from src.services.price_service import PriceService


class TestPriceService:
    """Tests for the PriceService."""

    @pytest.fixture
    def temp_data_dir(self) -> Path:
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def price_service(self, temp_data_dir: Path) -> PriceService:
        """Create a price service instance."""
        return PriceService(
            data_dir=temp_data_dir,
            threshold=Decimal("1.5"),
        )

    def test_init(self, price_service: PriceService) -> None:
        """Test service initialization."""
        assert price_service.threshold == Decimal("1.5")
        assert price_service.storage is not None
        assert price_service.yfinance is not None

    @patch("src.services.price_service.YFinanceAdapter")
    def test_fetch_current_prices(
        self,
        mock_adapter_class: MagicMock,
        temp_data_dir: Path,
    ) -> None:
        """Test fetching current prices."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_adapter.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("150.00"),
                timestamp=datetime.utcnow(),
            ),
        }
        mock_adapter_class.return_value = mock_adapter

        service = PriceService(data_dir=temp_data_dir)
        prices = service.fetch_current_prices(["AAPL"])

        assert "AAPL" in prices
        assert prices["AAPL"].price == Decimal("150.00")

    @patch("src.services.price_service.YFinanceAdapter")
    def test_get_price_changes_first_run(
        self,
        mock_adapter_class: MagicMock,
        temp_data_dir: Path,
    ) -> None:
        """Test price changes on first run (no previous price)."""
        mock_adapter = MagicMock()
        mock_adapter.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("150.00"),
                timestamp=datetime.utcnow(),
            ),
        }
        mock_adapter_class.return_value = mock_adapter

        service = PriceService(data_dir=temp_data_dir)
        changes = service.get_price_changes(["AAPL"])

        # First run should have no changes (no previous price)
        assert len(changes) == 0

    @patch("src.services.price_service.YFinanceAdapter")
    def test_get_price_changes_with_previous(
        self,
        mock_adapter_class: MagicMock,
        temp_data_dir: Path,
    ) -> None:
        """Test price changes with previous price stored."""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        service = PriceService(
            data_dir=temp_data_dir,
            threshold=Decimal("1.0"),
        )

        # First call - store initial price
        mock_adapter.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            ),
        }
        service.get_price_changes(["AAPL"])

        # Second call - should detect change
        mock_adapter.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("105.00"),
                timestamp=datetime(2026, 1, 24),
            ),
        }
        changes = service.get_price_changes(["AAPL"])

        assert len(changes) == 1
        assert changes[0].symbol == "AAPL"
        assert changes[0].change_percent == Decimal("5.00")

    @patch("src.services.price_service.YFinanceAdapter")
    def test_get_threshold_breaches(
        self,
        mock_adapter_class: MagicMock,
        temp_data_dir: Path,
    ) -> None:
        """Test detecting threshold breaches."""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

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

        # New prices - AAPL exceeds threshold, NVDA does not
        mock_adapter.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("103.00"),  # +3%
                timestamp=datetime(2026, 1, 24),
            ),
            "NVDA": PricePoint(
                symbol="NVDA",
                price=Decimal("201.00"),  # +0.5%
                timestamp=datetime(2026, 1, 24),
            ),
        }
        breaches = service.get_threshold_breaches(["AAPL", "NVDA"])

        assert len(breaches) == 1
        assert breaches[0].symbol == "AAPL"
        assert breaches[0].threshold_exceeded is True

    @patch("src.services.price_service.YFinanceAdapter")
    def test_get_price_handles_error(
        self,
        mock_adapter_class: MagicMock,
        temp_data_dir: Path,
    ) -> None:
        """Test error handling when fetching price fails."""
        mock_adapter = MagicMock()
        mock_adapter.get_current_price.side_effect = YFinanceError("API error")
        mock_adapter_class.return_value = mock_adapter

        service = PriceService(data_dir=temp_data_dir)
        result = service.get_price("INVALID")

        assert result is None

    def test_get_stored_price(self, price_service: PriceService) -> None:
        """Test retrieving stored price."""
        # Store a price
        price_service.storage.save_price(
            PricePoint(
                symbol="AAPL",
                price=Decimal("150.00"),
                timestamp=datetime.utcnow(),
            )
        )

        stored = price_service.get_stored_price("AAPL")
        assert stored is not None
        assert stored.price == Decimal("150.00")

    def test_get_price_history(self, price_service: PriceService) -> None:
        """Test retrieving price history."""
        # Store multiple prices
        for i in range(5):
            price_service.storage.save_price(
                PricePoint(
                    symbol="AAPL",
                    price=Decimal(f"{150 + i}.00"),
                    timestamp=datetime(2026, 1, 20 + i),
                )
            )

        history = price_service.get_price_history("AAPL", limit=3)
        assert len(history) == 3
        # Most recent first
        assert history[0].price == Decimal("154.00")
