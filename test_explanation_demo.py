#!/usr/bin/env python3
"""Demo script showing what the explanation output looks like."""

from decimal import Decimal
from datetime import datetime

from src.models.alert import Alert, Explanation
from src.models.stock import PriceChange

# Simulate a threshold breach
breach = PriceChange(
    symbol="NVDA",
    previous_price=Decimal("187.68"),
    current_price=Decimal("184.13"),  # Down 1.89%
    change_amount=Decimal("-3.55"),
    change_percent=Decimal("-1.89"),
    threshold_exceeded=True,
    previous_timestamp=datetime(2026, 1, 24, 15, 39),
    current_timestamp=datetime(2026, 1, 24, 15, 45),
)

# Simulate an explanation (what the LLM would generate)
explanation = Explanation(
    text=(
        "Nvidia stock declined due to geopolitical risks in China, "
        "a modest data center revenue miss, lofty valuation concerns, "
        "and broader sentiment that the AI frenzy may be overheating."
    ),
    news_headlines=[
        "Nvidia faces China trade restrictions",
        "Data center revenue below expectations",
    ],
    model="mistral:7b",
    generated_at=datetime.utcnow(),
)

# Create alert
alert = Alert(
    symbol="NVDA",
    change_percent=breach.change_percent,
    change_amount=breach.change_amount,
    previous_price=breach.previous_price,
    current_price=breach.current_price,
    explanation=explanation,
    timestamp=breach.current_timestamp,
)

print("\n" + "=" * 60)
print("STOCK ALERT (Console Output)")
print("=" * 60)
print(alert.format_message())
print("=" * 60)

print("\n" + "=" * 60)
print("SMS/Apple Messages Format")
print("=" * 60)
print(alert.format_short())
print("=" * 60)

print("\n" + "=" * 60)
print("What You'll See in Apple Messages:")
print("=" * 60)
print(f"⬇️ {alert.symbol} down {abs(alert.change_percent):.2f}%")
print(f"${alert.previous_price:.2f} → ${alert.current_price:.2f}")
print()
print(alert.explanation.text)
print("=" * 60)
print()
