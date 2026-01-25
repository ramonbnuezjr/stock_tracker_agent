"""Stock-related data models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.models.validators import validate_stock_symbol


class Stock(BaseModel):
    """Represents a stock with its basic information.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL').
        name: The company name (optional).

    Returns:
        A validated Stock instance.
    """

    symbol: str = Field(..., min_length=1, max_length=10)
    name: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase and alphanumeric.

        Uses shared validator to prevent injection attacks and ensure
        consistent validation across the codebase.

        Args:
            v: The symbol value to validate.

        Returns:
            The validated, uppercase, stripped symbol.

        Raises:
            ValueError: If symbol is invalid or contains prohibited characters.
        """
        return validate_stock_symbol(v)


class PricePoint(BaseModel):
    """A single price observation for a stock.

    Args:
        symbol: The stock ticker symbol.
        price: The stock price.
        timestamp: When this price was observed.
        currency: The currency code (default: USD).

    Returns:
        A validated PricePoint instance.
    """

    symbol: str = Field(..., min_length=1, max_length=10)
    price: Decimal = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    currency: str = Field(default="USD", max_length=3)

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase and validated.

        Uses shared validator for security and consistency.

        Args:
            v: The symbol value to validate.

        Returns:
            The validated, uppercase symbol.

        Raises:
            ValueError: If symbol is invalid or contains prohibited characters.
        """
        return validate_stock_symbol(v)

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        """Ensure currency is uppercase.

        Args:
            v: The currency value to validate.

        Returns:
            The uppercase currency code.
        """
        return v.upper().strip()


class PriceChange(BaseModel):
    """Represents a price change between two points.

    Args:
        symbol: The stock ticker symbol.
        previous_price: The earlier price point.
        current_price: The current price point.
        change_amount: The absolute price change.
        change_percent: The percentage change.
        threshold_exceeded: Whether the change exceeds the alert threshold.

    Returns:
        A validated PriceChange instance.
    """

    symbol: str = Field(..., min_length=1, max_length=10)
    previous_price: Decimal = Field(..., gt=0)
    current_price: Decimal = Field(..., gt=0)
    change_amount: Decimal
    change_percent: Decimal
    threshold_exceeded: bool = False
    previous_timestamp: Optional[datetime] = None
    current_timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase and validated.

        Uses shared validator for security and consistency.

        Args:
            v: The symbol value to validate.

        Returns:
            The validated, uppercase symbol.

        Raises:
            ValueError: If symbol is invalid or contains prohibited characters.
        """
        return validate_stock_symbol(v)

    @property
    def direction(self) -> str:
        """Get the direction of the price change.

        Returns:
            'up' if positive, 'down' if negative, 'unchanged' if zero.
        """
        if self.change_percent > 0:
            return "up"
        elif self.change_percent < 0:
            return "down"
        return "unchanged"

    @classmethod
    def calculate(
        cls,
        symbol: str,
        previous: PricePoint,
        current: PricePoint,
        threshold: Decimal,
    ) -> PriceChange:
        """Calculate price change between two price points.

        Args:
            symbol: The stock ticker symbol.
            previous: The earlier price point.
            current: The current price point.
            threshold: The percentage threshold for alerts.

        Returns:
            A PriceChange instance with calculated values.
        """
        change_amount = current.price - previous.price
        change_percent = (change_amount / previous.price) * 100
        threshold_exceeded = abs(change_percent) >= threshold

        return cls(
            symbol=symbol,
            previous_price=previous.price,
            current_price=current.price,
            change_amount=change_amount,
            change_percent=change_percent,
            threshold_exceeded=threshold_exceeded,
            previous_timestamp=previous.timestamp,
            current_timestamp=current.timestamp,
        )
