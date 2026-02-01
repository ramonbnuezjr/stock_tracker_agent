"""Shared pytest fixtures and mocks."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock

import pytest

from src.config import NotificationChannel, Settings
from src.models.alert import Alert, Explanation
from src.models.market_data import PriceQuote
from src.models.stock import PriceChange, PricePoint
from src.services.market_data_service import MarketDataService


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean environment variables before each test."""
    for key in list(os.environ.keys()):
        if key.startswith(("STOCK_", "PRICE_", "NOTIFICATION_", "SMTP_")):
            monkeypatch.delenv(key, raising=False)
        if key.startswith(("LLAMA_", "TWILIO_", "NOTIFY_", "LOG_", "DATA_")):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def sample_stock_prices() -> Dict[str, float]:
    """Sample stock prices for testing threshold detection."""
    return {
        "previous": 100.0,
        "current": 102.5,
    }


@pytest.fixture
def sample_threshold() -> float:
    """Sample threshold for testing (1.5%)."""
    return 0.015


@pytest.fixture
def sample_price_point() -> PricePoint:
    """Create a sample price point."""
    return PricePoint(
        symbol="AAPL",
        price=Decimal("150.00"),
        currency="USD",
        timestamp=datetime(2026, 1, 24, 12, 0, 0),
    )


@pytest.fixture
def sample_price_change() -> PriceChange:
    """Create a sample price change."""
    return PriceChange(
        symbol="AAPL",
        previous_price=Decimal("100.00"),
        current_price=Decimal("105.00"),
        change_amount=Decimal("5.00"),
        change_percent=Decimal("5.00"),
        threshold_exceeded=True,
        previous_timestamp=datetime(2026, 1, 23),
        current_timestamp=datetime(2026, 1, 24),
    )


@pytest.fixture
def sample_explanation() -> Explanation:
    """Create a sample explanation."""
    return Explanation(
        text="Apple stock rose following strong earnings report.",
        news_headlines=["Apple beats Q4 estimates"],
        model="llama.cpp",
        generated_at=datetime(2026, 1, 24, 12, 0, 0),
    )


@pytest.fixture
def sample_alert(sample_explanation: Explanation) -> Alert:
    """Create a sample alert with explanation."""
    return Alert(
        symbol="AAPL",
        change_percent=Decimal("5.0"),
        change_amount=Decimal("7.50"),
        previous_price=Decimal("150.00"),
        current_price=Decimal("157.50"),
        explanation=sample_explanation,
        timestamp=datetime(2026, 1, 24, 12, 0, 0),
    )


@pytest.fixture
def temp_data_dir() -> Path:
    """Create a temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def console_settings(temp_data_dir: Path) -> Settings:
    """Create settings for console notifications."""
    return Settings(
        notification_channel=NotificationChannel.CONSOLE,
        stock_symbols="AAPL,NVDA,MSFT",
        data_dir=temp_data_dir,
    )


@pytest.fixture
def mock_yfinance_adapter() -> MagicMock:
    """Create a mock YFinance adapter."""
    mock = MagicMock()
    mock.get_current_price.return_value = PricePoint(
        symbol="AAPL",
        price=Decimal("150.00"),
        timestamp=datetime.utcnow(),
    )
    mock.get_prices.return_value = {
        "AAPL": PricePoint(
            symbol="AAPL",
            price=Decimal("150.00"),
            timestamp=datetime.utcnow(),
        ),
    }
    return mock


@pytest.fixture
def mock_llama_cpp_adapter() -> MagicMock:
    """Create a mock LlamaCpp adapter."""
    mock = MagicMock()
    mock.generate.return_value = "Stock moved due to market conditions."
    mock.is_available.return_value = True
    return mock


@pytest.fixture
def mock_news_adapter() -> MagicMock:
    """Create a mock news adapter."""
    mock = MagicMock()
    mock.get_headlines_text.return_value = [
        "Apple announces new product",
        "Tech stocks rally",
    ]
    return mock


@pytest.fixture
def mock_market_data_service() -> MagicMock:
    """Create a mock MarketDataService."""
    mock = MagicMock(spec=MarketDataService)
    mock.get_latest_price.return_value = PriceQuote(
        symbol="AAPL",
        price=Decimal("150.00"),
        timestamp=datetime.utcnow(),
        provider_name="test",
    )
    return mock
