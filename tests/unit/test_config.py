"""Unit tests for configuration."""

import os
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from src.config import (
    LogLevel,
    NotificationChannel,
    Settings,
    get_settings,
)


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        # Clear any existing env vars
        for key in [
            "STOCK_SYMBOLS",
            "PRICE_THRESHOLD",
            "NOTIFICATION_CHANNEL",
        ]:
            os.environ.pop(key, None)

        settings = Settings()

        assert settings.stock_symbols == "AAPL,NVDA,MSFT"
        assert settings.price_threshold == Decimal("1.5")
        assert settings.notification_channel == NotificationChannel.CONSOLE
        assert settings.log_level == LogLevel.INFO

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override defaults."""
        monkeypatch.setenv("STOCK_SYMBOLS", "GOOG,AMZN")
        monkeypatch.setenv("PRICE_THRESHOLD", "2.5")
        monkeypatch.setenv("NOTIFICATION_CHANNEL", "email")

        settings = Settings()

        assert settings.stock_symbols == "GOOG,AMZN"
        assert settings.price_threshold == Decimal("2.5")
        assert settings.notification_channel == NotificationChannel.EMAIL

    def test_symbols_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test symbols_list property."""
        monkeypatch.setenv("STOCK_SYMBOLS", "AAPL, NVDA, MSFT")

        settings = Settings()
        symbols = settings.symbols_list

        assert len(symbols) == 3
        assert "AAPL" in symbols
        assert "NVDA" in symbols
        assert "MSFT" in symbols

    def test_symbols_uppercase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that symbols are uppercased."""
        monkeypatch.setenv("STOCK_SYMBOLS", "aapl,nvda")

        settings = Settings()

        assert settings.stock_symbols == "AAPL,NVDA"

    def test_empty_symbols_rejected(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that empty symbols are rejected."""
        monkeypatch.setenv("STOCK_SYMBOLS", "")

        with pytest.raises(ValueError):
            Settings()

    def test_validate_email_config_complete(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test email config validation when complete."""
        monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "test@test.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password")
        monkeypatch.setenv("NOTIFY_EMAIL", "recipient@test.com")

        settings = Settings()

        assert settings.validate_email_config() is True

    def test_validate_email_config_incomplete(self) -> None:
        """Test email config validation when incomplete."""
        settings = Settings()  # Using defaults

        assert settings.validate_email_config() is False

    def test_validate_sms_config_incomplete(self) -> None:
        """Test SMS config validation when incomplete."""
        settings = Settings()

        assert settings.validate_sms_config() is False

    def test_ensure_data_dir(self) -> None:
        """Test that ensure_data_dir creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "test_data"

            settings = Settings(data_dir=data_path)
            result = settings.ensure_data_dir()

            assert result == data_path
            assert data_path.exists()

    def test_log_level_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test all log level values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            monkeypatch.setenv("LOG_LEVEL", level)
            settings = Settings()
            assert settings.log_level.value == level

    def test_notification_channel_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test all notification channel values."""
        for channel in ["console", "email", "sms"]:
            monkeypatch.setenv("NOTIFICATION_CHANNEL", channel)
            settings = Settings()
            assert settings.notification_channel.value == channel

    def test_get_settings_function(self) -> None:
        """Test get_settings helper function."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_case_insensitive_env_vars(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that env vars are case insensitive."""
        monkeypatch.setenv("stock_symbols", "TEST")

        settings = Settings()

        assert "TEST" in settings.stock_symbols

    def test_invalid_threshold_rejected(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that invalid threshold values are rejected."""
        monkeypatch.setenv("PRICE_THRESHOLD", "-1.0")

        with pytest.raises(ValueError):
            Settings()

    def test_ollama_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Ollama configuration."""
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
        monkeypatch.setenv("OLLAMA_HOST", "http://custom:11434")

        settings = Settings()

        assert settings.ollama_model == "llama3.2:3b"
        assert settings.ollama_host == "http://custom:11434"
