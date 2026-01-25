"""Market data models for multi-provider support."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.models.validators import validate_stock_symbol


class PriceQuote(BaseModel):
    """Normalized price quote from any market data provider.

    Args:
        symbol: The stock ticker symbol.
        price: The stock price.
        timestamp: When this price was observed.
        provider_name: Name of the data provider.

    Returns:
        A validated PriceQuote instance.
    """

    symbol: str = Field(..., min_length=1, max_length=10)
    price: Decimal = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    provider_name: str = Field(..., min_length=1)

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

    @field_validator("provider_name")
    @classmethod
    def provider_lowercase(cls, v: str) -> str:
        """Normalize provider name to lowercase.

        Args:
            v: The provider name to validate.

        Returns:
            The lowercase provider name.
        """
        return v.lower().strip()
