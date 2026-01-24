"""Pytest configuration and fixtures."""

import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean environment variables before each test."""
    # Remove any stock tracker env vars that might interfere
    for key in list(os.environ.keys()):
        if key.startswith(("STOCK_", "PRICE_", "NOTIFICATION_", "SMTP_")):
            monkeypatch.delenv(key, raising=False)
        if key.startswith(("OLLAMA_", "TWILIO_", "NOTIFY_", "LOG_", "DATA_")):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def sample_price() -> dict:
    """Sample price data for tests."""
    return {
        "symbol": "AAPL",
        "price": "150.00",
        "currency": "USD",
    }
