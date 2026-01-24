"""Alert and explanation data models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class Explanation(BaseModel):
    """An LLM-generated explanation for a price movement.

    Args:
        text: The explanation text (2-3 sentences).
        news_headlines: Headlines used to generate the explanation.
        model: The LLM model used for generation.
        generated_at: When the explanation was generated.

    Returns:
        A validated Explanation instance.
    """

    text: str = Field(..., min_length=1, max_length=1000)
    news_headlines: List[str] = Field(default_factory=list)
    model: str = Field(default="unknown")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(BaseModel):
    """A stock price alert with explanation.

    Args:
        symbol: The stock ticker symbol.
        change_percent: The percentage change that triggered the alert.
        change_amount: The absolute price change.
        previous_price: The price before the change.
        current_price: The current price.
        explanation: The LLM-generated explanation.
        timestamp: When the alert was created.
        notified: Whether the alert has been sent.

    Returns:
        A validated Alert instance.
    """

    symbol: str = Field(..., min_length=1, max_length=10)
    change_percent: Decimal
    change_amount: Decimal
    previous_price: Decimal = Field(..., gt=0)
    current_price: Decimal = Field(..., gt=0)
    explanation: Optional[Explanation] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = False

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

    @property
    def direction_emoji(self) -> str:
        """Get an emoji representing the direction.

        Returns:
            An up or down arrow emoji, or dash for unchanged.
        """
        if self.change_percent > 0:
            return "📈"
        elif self.change_percent < 0:
            return "📉"
        return "➖"

    def format_message(self) -> str:
        """Format the alert as a human-readable message.

        Returns:
            A formatted string suitable for notifications.
        """
        direction = "up" if self.change_percent > 0 else "down"
        sign = "+" if self.change_percent > 0 else ""

        message = (
            f"{self.direction_emoji} {self.symbol} is {direction} "
            f"{sign}{self.change_percent:.2f}% "
            f"(${self.previous_price:.2f} → ${self.current_price:.2f})"
        )

        if self.explanation:
            message += f"\n\n{self.explanation.text}"

        return message

    def format_short(self) -> str:
        """Format the alert as a short message for SMS.

        Returns:
            A short formatted string under 160 characters.
        """
        direction = "↑" if self.change_percent > 0 else "↓"
        sign = "+" if self.change_percent > 0 else ""

        base = (
            f"{self.symbol} {direction}{sign}{self.change_percent:.1f}% "
            f"${self.current_price:.2f}"
        )

        if self.explanation:
            # Truncate explanation to fit SMS
            max_explain = 160 - len(base) - 3  # 3 for " - "
            if max_explain > 20:
                explain = self.explanation.text[:max_explain]
                if len(self.explanation.text) > max_explain:
                    explain = explain.rsplit(" ", 1)[0] + "..."
                base += f" - {explain}"

        return base[:160]
