"""Unit tests for storage adapter."""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.adapters.storage_adapter import StorageAdapter
from src.models.stock import PricePoint


class TestStorageAdapter:
    """Tests for the StorageAdapter."""

    @pytest.fixture
    def temp_data_dir(self) -> Path:
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_data_dir: Path) -> StorageAdapter:
        """Create a storage adapter instance."""
        return StorageAdapter(temp_data_dir)

    def test_init_creates_database(self, storage: StorageAdapter) -> None:
        """Test that initialization creates the database file."""
        assert storage.db_path.exists()

    def test_save_and_get_latest_price(self, storage: StorageAdapter) -> None:
        """Test saving and retrieving a price."""
        price = PricePoint(
            symbol="AAPL",
            price=Decimal("150.00"),
            currency="USD",
            timestamp=datetime(2026, 1, 24, 12, 0, 0),
        )

        row_id = storage.save_price(price)
        assert row_id > 0

        retrieved = storage.get_latest_price("AAPL")
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.price == Decimal("150.00")
        assert retrieved.currency == "USD"

    def test_get_latest_price_not_found(self, storage: StorageAdapter) -> None:
        """Test getting price for non-existent symbol."""
        result = storage.get_latest_price("INVALID")
        assert result is None

    def test_get_previous_price(self, storage: StorageAdapter) -> None:
        """Test getting the second most recent price."""
        # Save two prices
        storage.save_price(
            PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            )
        )
        storage.save_price(
            PricePoint(
                symbol="AAPL",
                price=Decimal("105.00"),
                timestamp=datetime(2026, 1, 24),
            )
        )

        previous = storage.get_previous_price("AAPL")
        assert previous is not None
        assert previous.price == Decimal("100.00")

    def test_get_previous_price_only_one(
        self,
        storage: StorageAdapter,
    ) -> None:
        """Test previous price when only one price exists."""
        storage.save_price(
            PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            )
        )

        previous = storage.get_previous_price("AAPL")
        assert previous is None

    def test_get_price_history(self, storage: StorageAdapter) -> None:
        """Test getting price history."""
        for i in range(5):
            storage.save_price(
                PricePoint(
                    symbol="AAPL",
                    price=Decimal(f"{100 + i}.00"),
                    timestamp=datetime(2026, 1, 20 + i),
                )
            )

        history = storage.get_price_history("AAPL", limit=3)
        assert len(history) == 3
        # Most recent first
        assert history[0].price == Decimal("104.00")
        assert history[2].price == Decimal("102.00")

    def test_get_price_history_respects_limit(
        self,
        storage: StorageAdapter,
    ) -> None:
        """Test that price history respects limit."""
        for i in range(10):
            storage.save_price(
                PricePoint(
                    symbol="AAPL",
                    price=Decimal(f"{100 + i}.00"),
                    timestamp=datetime(2026, 1, i + 1),
                )
            )

        history = storage.get_price_history("AAPL", limit=5)
        assert len(history) == 5

    def test_log_execution(self, storage: StorageAdapter) -> None:
        """Test logging execution start and completion."""
        execution_id = storage.log_execution_start(["AAPL", "NVDA"])
        assert execution_id > 0

        storage.log_execution_complete(
            execution_id=execution_id,
            alerts_triggered=2,
            notifications_sent=2,
            success=True,
        )
        # No error means success

    def test_log_execution_with_error(self, storage: StorageAdapter) -> None:
        """Test logging execution with error."""
        execution_id = storage.log_execution_start(["AAPL"])

        storage.log_execution_complete(
            execution_id=execution_id,
            alerts_triggered=0,
            notifications_sent=0,
            success=False,
            error_message="Connection failed",
        )
        # No error means success

    def test_save_alert(self, storage: StorageAdapter) -> None:
        """Test saving an alert."""
        alert_id = storage.save_alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
            explanation="Strong earnings drove the increase.",
            notified=True,
        )
        assert alert_id > 0

    def test_symbol_case_insensitive(self, storage: StorageAdapter) -> None:
        """Test that symbol lookups are case insensitive."""
        storage.save_price(
            PricePoint(
                symbol="AAPL",
                price=Decimal("150.00"),
                timestamp=datetime(2026, 1, 24),
            )
        )

        # Should find with lowercase
        result = storage.get_latest_price("aapl")
        assert result is not None
        assert result.symbol == "AAPL"
