"""Converter between PriceQuote and PricePoint models."""

from __future__ import annotations

from src.models.market_data import PriceQuote
from src.models.stock import PricePoint


def quote_to_price_point(quote: PriceQuote) -> PricePoint:
    """Convert a PriceQuote to a PricePoint.

    Args:
        quote: The PriceQuote to convert.

    Returns:
        A PricePoint with the same data.
    """
    return PricePoint(
        symbol=quote.symbol,
        price=quote.price,
        timestamp=quote.timestamp,
        currency="USD",  # Default, providers may not specify
    )
