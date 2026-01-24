"""Unit tests for notification service."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.config import NotificationChannel, Settings
from src.models.alert import Alert, Explanation
from src.services.notification_service import NotificationService


class TestNotificationService:
    """Tests for the NotificationService."""

    @pytest.fixture
    def console_settings(self) -> Settings:
        """Create settings for console notifications."""
        return Settings(
            notification_channel=NotificationChannel.CONSOLE,
            stock_symbols="AAPL",
        )

    @pytest.fixture
    def email_settings(self) -> Settings:
        """Create settings for email notifications."""
        return Settings(
            notification_channel=NotificationChannel.EMAIL,
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password123",
            notify_email="recipient@test.com",
            stock_symbols="AAPL",
        )

    @pytest.fixture
    def sample_alert(self) -> Alert:
        """Create a sample alert."""
        return Alert(
            symbol="AAPL",
            change_percent=Decimal("5.0"),
            change_amount=Decimal("7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
            explanation=Explanation(
                text="Strong earnings drove the increase.",
                news_headlines=["Apple beats Q4 estimates"],
                model="test",
            ),
            timestamp=datetime(2026, 1, 24, 12, 0, 0),
        )

    def test_init_console_channel(self, console_settings: Settings) -> None:
        """Test initialization with console channel."""
        service = NotificationService(console_settings)
        assert service.channel == NotificationChannel.CONSOLE

    def test_init_email_channel(self, email_settings: Settings) -> None:
        """Test initialization with email channel."""
        service = NotificationService(email_settings)
        assert service.channel == NotificationChannel.EMAIL
        assert service._email_adapter is not None

    def test_init_email_incomplete_falls_back(self) -> None:
        """Test that incomplete email config falls back to console."""
        settings = Settings(
            notification_channel=NotificationChannel.EMAIL,
            smtp_host="",  # Missing required field
            stock_symbols="AAPL",
        )
        service = NotificationService(settings)
        assert service.channel == NotificationChannel.CONSOLE

    def test_send_console_alert(
        self,
        console_settings: Settings,
        sample_alert: Alert,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test sending alert to console."""
        service = NotificationService(console_settings)
        result = service.send_alert(sample_alert)

        assert result is True
        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "5.00%" in captured.out
        assert "Strong earnings" in captured.out

    @patch("src.adapters.email_adapter.smtplib.SMTP")
    def test_send_email_alert(
        self,
        mock_smtp: MagicMock,
        email_settings: Settings,
        sample_alert: Alert,
    ) -> None:
        """Test sending alert via email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = NotificationService(email_settings)
        result = service.send_alert(sample_alert)

        assert result is True
        mock_server.sendmail.assert_called_once()

    @patch("src.adapters.email_adapter.smtplib.SMTP")
    def test_send_email_alert_failure_falls_back(
        self,
        mock_smtp: MagicMock,
        email_settings: Settings,
        sample_alert: Alert,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that email failure falls back to console."""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP error")

        service = NotificationService(email_settings)
        result = service.send_alert(sample_alert)

        # Should fall back to console and succeed
        assert result is True
        captured = capsys.readouterr()
        assert "AAPL" in captured.out

    def test_send_alerts_multiple(
        self,
        console_settings: Settings,
        sample_alert: Alert,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test sending multiple alerts."""
        alerts = [sample_alert, sample_alert]

        service = NotificationService(console_settings)
        sent = service.send_alerts(alerts)

        assert sent == 2
        captured = capsys.readouterr()
        assert captured.out.count("AAPL") == 2

    def test_format_email_subject_up(
        self,
        email_settings: Settings,
        sample_alert: Alert,
    ) -> None:
        """Test email subject formatting for positive change."""
        service = NotificationService(email_settings)
        subject = service._format_email_subject(sample_alert)

        assert "AAPL" in subject
        assert "UP" in subject
        assert "+5.0%" in subject

    def test_format_email_subject_down(
        self,
        email_settings: Settings,
    ) -> None:
        """Test email subject formatting for negative change."""
        alert = Alert(
            symbol="NVDA",
            change_percent=Decimal("-3.5"),
            change_amount=Decimal("-7.00"),
            previous_price=Decimal("200.00"),
            current_price=Decimal("193.00"),
        )

        service = NotificationService(email_settings)
        subject = service._format_email_subject(alert)

        assert "NVDA" in subject
        assert "DOWN" in subject
        assert "-3.5%" in subject

    def test_format_html_body(
        self,
        email_settings: Settings,
        sample_alert: Alert,
    ) -> None:
        """Test HTML email body formatting."""
        service = NotificationService(email_settings)
        html = service._format_html_body(sample_alert)

        assert "AAPL" in html
        assert "150.00" in html
        assert "157.50" in html
        assert "Strong earnings" in html
        # Check for green color for positive change
        assert "#22c55e" in html

    def test_format_html_body_negative(
        self,
        email_settings: Settings,
    ) -> None:
        """Test HTML formatting for negative change."""
        alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("-5.0"),
            change_amount=Decimal("-7.50"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("142.50"),
        )

        service = NotificationService(email_settings)
        html = service._format_html_body(alert)

        # Check for red color for negative change
        assert "#ef4444" in html

    def test_test_notification(
        self,
        console_settings: Settings,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test sending a test notification."""
        service = NotificationService(console_settings)
        result = service.test_notification()

        assert result is True
        captured = capsys.readouterr()
        assert "TEST" in captured.out
