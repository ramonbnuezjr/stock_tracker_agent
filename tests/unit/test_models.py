"""Unit tests for data models."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.models.alert import Alert, Explanation
from src.models.stock import PriceChange, PricePoint, Stock


class TestStock:
    """Tests for the Stock model."""

    def test_create_stock(self) -> None:
        """Test creating a stock with valid data."""
        stock = Stock(symbol="AAPL", name="Apple Inc.")
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."

    def test_symbol_uppercase(self) -> None:
        """Test that symbol is automatically uppercased."""
        stock = Stock(symbol="aapl")
        assert stock.symbol == "AAPL"

    def test_symbol_stripped(self) -> None:
        """Test that symbol whitespace is stripped."""
        stock = Stock(symbol="  AAPL  ")
        assert stock.symbol == "AAPL"

    def test_symbol_with_dot(self) -> None:
        """Test symbols with dots (e.g., BRK.B)."""
        stock = Stock(symbol="BRK.B")
        assert stock.symbol == "BRK.B"

    def test_symbol_with_caret(self) -> None:
        """Test index symbols with caret (e.g., ^NDXT)."""
        stock = Stock(symbol="^NDXT")
        assert stock.symbol == "^NDXT"

    def test_invalid_symbol(self) -> None:
        """Test that invalid symbols are rejected."""
        with pytest.raises(ValueError):
            Stock(symbol="AAPL@123")

    def test_empty_symbol(self) -> None:
        """Test that empty symbols are rejected."""
        with pytest.raises(ValueError):
            Stock(symbol="")


class TestPricePoint:
    """Tests for the PricePoint model."""

    def test_create_price_point(self) -> None:
        """Test creating a price point with valid data."""
        price = PricePoint(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime(2026, 1, 24, 12, 0, 0),
        )
        assert price.symbol == "AAPL"
        assert price.price == Decimal("150.00")
        assert price.currency == "USD"

    def test_symbol_uppercase(self) -> None:
        """Test that symbol is uppercased."""
        price = PricePoint(symbol="aapl", price=Decimal("150.00"))
        assert price.symbol == "AAPL"

    def test_currency_uppercase(self) -> None:
        """Test that currency is uppercased."""
        price = PricePoint(
            symbol="AAPL",
            price=Decimal("150.00"),
            currency="usd",
        )
        assert price.currency == "USD"

    def test_negative_price_rejected(self) -> None:
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError):
            PricePoint(symbol="AAPL", price=Decimal("-10.00"))

    def test_zero_price_rejected(self) -> None:
        """Test that zero prices are rejected."""
        with pytest.raises(ValueError):
            PricePoint(symbol="AAPL", price=Decimal("0"))


class TestPriceChange:
    """Tests for the PriceChange model."""

    def test_calculate_positive_change(self) -> None:
        """Test calculating a positive price change."""
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("105.00"),
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal("1.0"),
        )

        assert change.symbol == "AAPL"
        assert change.change_amount == Decimal("5.00")
        assert change.change_percent == Decimal("5.00")
        assert change.threshold_exceeded is True
        assert change.direction == "up"

    def test_calculate_negative_change(self) -> None:
        """Test calculating a negative price change."""
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("95.00"),
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal("1.0"),
        )

        assert change.change_amount == Decimal("-5.00")
        assert change.change_percent == Decimal("-5.00")
        assert change.direction == "down"

    def test_threshold_not_exceeded(self) -> None:
        """Test when change is below threshold."""
        previous = PricePoint(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
        )
        current = PricePoint(
            symbol="AAPL",
            price=Decimal("100.50"),
            timestamp=datetime(2026, 1, 24),
        )

        change = PriceChange.calculate(
            symbol="AAPL",
            previous=previous,
            current=current,
            threshold=Decimal("1.0"),
        )

        assert change.threshold_exceeded is False

    def test_direction_unchanged(self) -> None:
        """Test direction when price is unchanged."""
        change = PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("100.00"),
            change_amount=Decimal("0"),
            change_percent=Decimal("0"),
        )
        assert change.direction == "unchanged"


class TestExplanation:
    """Tests for the Explanation model."""

    def test_create_explanation(self) -> None:
        """Test creating an explanation."""
        explanation = Explanation(
            text="The stock rose due to earnings beat.",
            news_headlines=["Apple beats Q4 estimates"],
            model="mistral:7b",
        )
        assert "earnings" in explanation.text
        assert len(explanation.news_headlines) == 1
        assert explanation.model == "mistral:7b"


class TestAlert:
    """Tests for the Alert model."""

    def test_create_alert(self) -> None:
        """Test creating an alert."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
        )
        assert alert.symbol == "AAPL"
        assert alert.direction == "up"
        assert alert.direction_emoji == "📈"

    def test_alert_direction_down(self) -> None:
        """Test alert with negative change."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("-3.0"),
            change_amount=Decimal("-4.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("145.50"),
        )
        assert alert.direction == "down"
        assert alert.direction_emoji == "📉"

    def test_format_message(self) -> None:
        """Test formatting alert as message."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
        )
        message = alert.format_message()
        assert "AAPL" in message
        assert "5.00%" in message
        assert "150.00" in message
        assert "157.50" in message

    def test_format_message_with_explanation(self) -> None:
        """Test formatting alert with explanation."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
            explanation=Explanation(
                text="Strong earnings drove the increase.",
                news_headlines=[],
                model="test",
            ),
        )
        message = alert.format_message()
        assert "Strong earnings" in message

    def test_format_short(self) -> None:
        """Test formatting alert as short message."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
        )
        short = alert.format_short()
        assert len(short) <= 160
        assert "AAPL" in short
