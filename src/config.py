"""Application configuration via environment variables."""

from __future__ import annotations

import os
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.models.validators import validate_stock_symbol
from src.security_logger import get_security_logger


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    CONSOLE = "console"
    EMAIL = "email"
    SMS = "sms"  # Twilio SMS
    EMAIL_SMS = "email_sms"  # Email-to-SMS via carrier gateway
    APPLE_MESSAGES = "apple_messages"  # macOS Messages app
    AUTO = "auto"  # Automatic: Twilio → Apple Messages → Console


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Args:
        stock_symbols: Comma-separated list of stock symbols to track.
        price_threshold: Percentage change threshold for alerts.
        notification_channel: Channel to send notifications through.
        smtp_host: SMTP server hostname for email notifications.
        smtp_port: SMTP server port.
        smtp_user: SMTP username/email.
        smtp_password: SMTP password or app password.
        notify_email: Email address to send notifications to.
        ollama_model: Ollama model name for explanations.
        ollama_host: Ollama API host URL.
        data_dir: Directory for local data storage.
        log_level: Logging verbosity level.

    Returns:
        A validated Settings instance.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Stock tracking
    stock_symbols: str = Field(
        default="AAPL,NVDA,MSFT",
        description="Comma-separated list of stock symbols",
    )
    price_threshold: Annotated[
        Decimal, Field(gt=0, description="Percentage threshold for alerts")
    ] = Decimal("1.5")

    # Notifications
    notification_channel: NotificationChannel = Field(
        default=NotificationChannel.CONSOLE,
        description="Notification delivery channel",
    )

    # Email settings
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587, gt=0, lt=65536)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    notify_email: str = Field(default="")

    # Twilio SMS settings
    enable_twilio: bool = Field(
        default=False,
        description="Enable Twilio as primary SMS channel",
    )
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    twilio_from_number: str = Field(default="")
    notify_phone: str = Field(default="")

    # Email-to-SMS settings (carrier gateway)
    sms_carrier: str = Field(
        default="att",
        description="Carrier for email-to-SMS (att, verizon, tmobile, etc.)",
    )

    # Market data provider API keys
    finnhub_api_key: str = Field(
        default="",
        description="Finnhub API key (free tier: 60 calls/min)",
    )
    twelve_data_api_key: str = Field(
        default="",
        description="Twelve Data API key (free tier: 800 calls/day)",
    )
    alpha_vantage_api_key: str = Field(
        default="",
        description="Alpha Vantage API key (free tier: 25 calls/day)",
    )

    # LLM settings
    ollama_model: str = Field(
        default="mistral:7b",
        description="Ollama model for generating explanations",
    )
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama API host URL",
    )

    # Storage
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for local data storage",
    )

    # Logging
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging verbosity",
    )

    @field_validator("stock_symbols")
    @classmethod
    def validate_symbols(cls, v: str) -> str:
        """Validate and normalize stock symbols.

        Validates each symbol using shared validator to prevent injection
        attacks and ensure security. This is the entry point for all symbol
        input from environment variables. Security violations are logged.

        Args:
            v: Comma-separated symbols string.

        Returns:
            Normalized, validated uppercase symbols string.

        Raises:
            ValueError: If no valid symbols provided or any symbol is invalid.
        """
        security_logger = get_security_logger()

        if not v or not v.strip():
            security_logger.log_validation_rejection(
                input_value=v,
                reason="Empty stock symbols configuration",
                context={
                    "validation_type": "settings_stock_symbols",
                    "rule": "non_empty",
                    "source": "environment_variable",
                },
            )
            raise ValueError("At least one stock symbol is required")

        # Parse and validate each symbol
        validated_symbols = []
        for symbol_str in v.split(","):
            symbol_str = symbol_str.strip()
            if symbol_str:
                try:
                    # Use shared validator for security and consistency
                    # Security logging happens inside validate_stock_symbol
                    validated = validate_stock_symbol(symbol_str)
                    validated_symbols.append(validated)
                except ValueError as e:
                    # Additional context for Settings-level validation
                    security_logger.log_validation_rejection(
                        input_value=symbol_str,
                        reason=f"Symbol validation failed: {str(e)}",
                        context={
                            "validation_type": "settings_stock_symbols",
                            "source": "environment_variable",
                            "symbol_list": v,
                        },
                    )
                    raise

        if not validated_symbols:
            security_logger.log_validation_rejection(
                input_value=v,
                reason="No valid symbols after parsing",
                context={
                    "validation_type": "settings_stock_symbols",
                    "source": "environment_variable",
                },
            )
            raise ValueError("At least one valid stock symbol is required")

        return ",".join(validated_symbols)

    @property
    def symbols_list(self) -> list[str]:
        """Get stock symbols as a list.

        Returns:
            List of uppercase stock symbols.
        """
        return [s.strip() for s in self.stock_symbols.split(",")]

    def validate_email_config(self) -> bool:
        """Check if email configuration is complete.

        Returns:
            True if all required email settings are present.
        """
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.notify_email,
        ])

    def validate_sms_config(self) -> bool:
        """Check if SMS configuration is complete.

        Returns:
            True if all required SMS settings are present.
        """
        return all([
            self.twilio_account_sid,
            self.twilio_auth_token,
            self.twilio_from_number,
            self.notify_phone,
        ])

    def validate_email_sms_config(self) -> bool:
        """Check if Email-to-SMS configuration is complete.

        Returns:
            True if all required settings are present.
        """
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.notify_phone,
            self.sms_carrier,
        ])

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists.

        Returns:
            Path to the data directory.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        The application Settings instance.
    """
    return Settings()
