"""
Tests for notification delivery.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.email_adapter import EmailAdapter, EmailError
from src.config import NotificationChannel, Settings
from src.models.alert import Alert, Explanation
from src.services.notification_service import NotificationService


class TestNotificationDispatch:
    """Tests for notification dispatch functionality."""

    @pytest.fixture
    def alert_with_explanation(self) -> Alert:
        """Create an alert with all required fields."""
        return Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
            explanation=Explanation(
                text="Apple stock rose due to strong earnings.",
                news_headlines=["Apple beats Q4 estimates"],
                model="llama.cpp",
                generated_at=datetime(2026, 1, 24, 12, 0, 0),
            ),
            timestamp=datetime(2026, 1, 24, 12, 0, 0),
        )

    def test_notification_payload_contains_required_fields(
        self,
        alert_with_explanation: Alert,
    ) -> None:
        """
        Notification payload must include symbol, change percentage,
        explanation text, and timestamp.
        """
        alert = alert_with_explanation
        message = alert.format_message()

        # Check all required fields are present
        assert alert.symbol in message  # Symbol
        assert "5.00%" in message  # Change percentage
        assert alert.explanation is not None
        assert alert.explanation.text in message  # Explanation text
        assert alert.timestamp is not None  # Timestamp exists

        # Also verify the Alert model has all required fields
        assert alert.symbol == "AAPL"
        assert alert.change_percent == Decimal("5.0")
        assert alert.explanation.text == "Apple stock rose due to strong earnings."
        assert alert.timestamp == datetime(2026, 1, 24, 12, 0, 0)

    def test_sms_notification_formats_plain_text(
        self,
        alert_with_explanation: Alert,
    ) -> None:
        """
        SMS notifications must be plain-text and human-readable.
        """
        short_message = alert_with_explanation.format_short()

        # Should be plain text (no HTML)
        assert "<" not in short_message
        assert ">" not in short_message

        # Should be under 160 characters for SMS
        assert len(short_message) <= 160

        # Should be human-readable with key info
        assert "AAPL" in short_message
        assert "5.0%" in short_message or "5%" in short_message

    def test_notification_failure_does_not_crash_execution(
        self,
        temp_data_dir: Path,
        alert_with_explanation: Alert,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Notification errors should be logged but not crash the run.
        """
        # Create settings with email channel but make email fail
        settings = Settings(
            notification_channel=NotificationChannel.EMAIL,
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
            notify_email="recipient@test.com",
            data_dir=temp_data_dir,
        )

        with patch.object(EmailAdapter, "send") as mock_send:
            mock_send.side_effect = EmailError("SMTP connection failed")

            service = NotificationService(settings)
            # Should not raise, should fall back to console
            result = service.send_alert(alert_with_explanation)

            # Should succeed via fallback
            assert result is True

            # Should have printed to console (fallback)
            captured = capsys.readouterr()
            assert "AAPL" in captured.out

    def test_console_notification_outputs_correctly(
        self,
        temp_data_dir: Path,
        alert_with_explanation: Alert,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Console notifications should output to stdout.
        """
        settings = Settings(
            notification_channel=NotificationChannel.CONSOLE,
            data_dir=temp_data_dir,
        )

        service = NotificationService(settings)
        result = service.send_alert(alert_with_explanation)

        assert result is True

        captured = capsys.readouterr()
        assert "STOCK ALERT" in captured.out
        assert "AAPL" in captured.out
        assert "5.00%" in captured.out
        assert "strong earnings" in captured.out

    def test_email_notification_formats_correctly(
        self,
        temp_data_dir: Path,
        alert_with_explanation: Alert,
    ) -> None:
        """
        Email notifications should have proper subject and body.
        """
        settings = Settings(
            notification_channel=NotificationChannel.EMAIL,
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
            notify_email="recipient@test.com",
            data_dir=temp_data_dir,
        )

        service = NotificationService(settings)

        # Check subject formatting
        subject = service._format_email_subject(alert_with_explanation)
        assert "AAPL" in subject
        assert "UP" in subject
        assert "5.0%" in subject

        # Check HTML body formatting
        html = service._format_html_body(alert_with_explanation)
        assert "AAPL" in html
        assert "157.50" in html
        assert "150.00" in html
        assert "#22c55e" in html  # Green color for positive

    def test_negative_change_email_format(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Negative changes should show red color and DOWN direction.
        """
        alert = Alert(
            symbol="NVDA",
            change_percent=Decimal("-3.5"),
            change_amount=Decimal("-17.50"),
            previous_price=Decimal("500.00"),
            current_price=Decimal("482.50"),
            timestamp=datetime.utcnow(),
        )

        settings = Settings(
            notification_channel=NotificationChannel.EMAIL,
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
            notify_email="recipient@test.com",
            data_dir=temp_data_dir,
        )

        service = NotificationService(settings)

        subject = service._format_email_subject(alert)
        assert "DOWN" in subject
        assert "-3.5%" in subject

        html = service._format_html_body(alert)
        assert "#ef4444" in html  # Red color for negative

    def test_multiple_alerts_sent(
        self,
        temp_data_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Multiple alerts should all be sent.
        """
        alerts = [
            Alert(
                symbol="AAPL",
                change_percent=Decimal("5.0"),
                change_amount=Decimal("7.50"),
                previous_price=Decimal("150.00"),
                current_price=Decimal("157.50"),
            ),
            Alert(
                symbol="NVDA",
                change_percent=Decimal("-3.0"),
                change_amount=Decimal("-15.00"),
                previous_price=Decimal("500.00"),
                current_price=Decimal("485.00"),
            ),
        ]

        settings = Settings(
            notification_channel=NotificationChannel.CONSOLE,
            data_dir=temp_data_dir,
        )

        service = NotificationService(settings)
        sent_count = service.send_alerts(alerts)

        assert sent_count == 2

        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "NVDA" in captured.out

    def test_test_notification_works(
        self,
        temp_data_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Test notification should send successfully.
        """
        settings = Settings(
            notification_channel=NotificationChannel.CONSOLE,
            data_dir=temp_data_dir,
        )

        service = NotificationService(settings)
        result = service.test_notification()

        assert result is True

        captured = capsys.readouterr()
        assert "TEST" in captured.out
