#!/usr/bin/env python3
"""Test script to send an artificial stock alert via Apple Messages.

This creates a fake alert with artificial stock data to test the
notification system without waiting for real price movements.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.config import Settings, get_settings
from src.models.alert import Alert, Explanation
from src.services.notification_service import NotificationService


def create_test_alert() -> Alert:
    """Create an artificial stock alert for testing.

    Returns:
        An Alert with fake but realistic stock data.
    """
    # Create artificial price data
    symbol = "AAPL"
    previous_price = Decimal("250.00")
    current_price = Decimal("242.50")  # Down 3% (exceeds 1.5% threshold)
    change_amount = current_price - previous_price
    change_pct = (change_amount / previous_price) * 100

    # Create artificial explanation
    explanation = Explanation(
        text=(
            "Apple stock declined 3.0% due to concerns over iPhone sales "
            "in China, supply chain disruptions, and broader tech sector "
            "volatility. Analysts note increased competition and regulatory "
            "headwinds in key markets."
        ),
        generated_at=datetime.utcnow(),
        news_headlines=[
            "Apple faces iPhone sales slowdown in China",
            "Supply chain issues impact Q1 production",
            "Tech stocks slide on regulatory concerns",
        ],
    )

    # Create alert (Alert model expects fields directly, not nested)
    alert = Alert(
        symbol=symbol,
        change_percent=change_pct,
        change_amount=change_amount,
        previous_price=previous_price,
        current_price=current_price,
        explanation=explanation,
        timestamp=datetime.utcnow(),
    )

    return alert


def main() -> int:
    """Run the test notification.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("🧪 Testing Apple Messages Notification")
    print("=" * 60)

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return 1

    # Verify Apple Messages is configured
    if settings.notification_channel.value not in ["apple_messages", "auto"]:
        print(f"⚠️  Notification channel is set to: {settings.notification_channel.value}")
        print("   Setting to 'apple_messages' for this test...")
        settings.notification_channel = settings.notification_channel.__class__.APPLE_MESSAGES

    if not settings.notify_phone:
        print("❌ NOTIFY_PHONE not set in .env file")
        print("   Please set NOTIFY_PHONE=+1XXXXXXXXXX in your .env file")
        return 1

    print(f"📱 Sending test alert to: {settings.notify_phone}")
    print()

    # Create test alert
    alert = create_test_alert()
    print("📊 Test Alert Data:")
    print(f"   Symbol: {alert.symbol}")
    print(f"   Previous: ${alert.previous_price}")
    print(f"   Current: ${alert.current_price}")
    print(f"   Change: {alert.change_percent:.2f}%")
    print()

    # Initialize notification service
    try:
        notification_service = NotificationService(settings)
        print(f"✅ Notification service initialized")
        print(f"   Channel: {notification_service.channel.value}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize notification service: {e}")
        return 1

    # Send alert
    print("📤 Sending alert via Apple Messages...")
    try:
        success = notification_service.send_alert(alert)
        if success:
            print()
            print("✅ Alert sent successfully!")
            print()
            print("Check your iPhone for the message.")
            print()
            print("Expected message format:")
            print("-" * 60)
            print(f"⬇️ {alert.symbol} down {abs(alert.change_percent):.2f}%")
            print(f"${alert.previous_price} → ${alert.current_price}")
            print()
            if alert.explanation:
                print(alert.explanation.text)
            print("-" * 60)
            return 0
        else:
            print("❌ Failed to send alert (returned False)")
            return 1
    except Exception as e:
        print(f"❌ Error sending alert: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
