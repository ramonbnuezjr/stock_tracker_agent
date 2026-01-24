"""
Tests for notification channel implementations.

Email-to-SMS uses carrier gateways to deliver SMS via email:
- AT&T: number@txt.att.net
- Verizon: number@vtext.com
- T-Mobile: number@tmomail.net
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.alert import Alert, Explanation


class TestEmailSMSChannel:
    """Tests for Email-to-SMS notification channel."""

    @pytest.fixture
    def sample_alert(self) -> Alert:
        """Create a sample alert for testing."""
        return Alert(
            symbol="AAPL",
            change_percent=Decimal("5.25"),
            change_amount=Decimal("7.88"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.88"),
            explanation=Explanation(
                text="Apple stock rose following strong iPhone sales in Q4.",
                news_headlines=["Apple beats earnings estimates"],
                model="mistral:7b",
            ),
            timestamp=datetime(2026, 1, 24, 12, 0, 0),
        )

    def test_email_sms_channel_formats_message_for_carrier_gateway(
        self,
        sample_alert: Alert,
    ) -> None:
        """
        Email-to-SMS notifications should:
        - Use plain text only
        - Stay under SMS length limits (160 chars)
        - Include symbol + % change + explanation
        """
        from src.adapters.email_sms_adapter import EmailSMSAdapter

        adapter = EmailSMSAdapter(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            carrier="att",
        )

        message = adapter.format_sms_message(sample_alert)

        # Must be plain text (no HTML)
        assert "<" not in message
        assert ">" not in message

        # Must be under SMS limit
        assert len(message) <= 160

        # Must include key info
        assert "AAPL" in message
        assert "5.2" in message or "5.25" in message  # % change

    def test_email_sms_builds_correct_gateway_address(self) -> None:
        """
        Gateway address should match carrier format (MMS gateways).
        """
        from src.adapters.email_sms_adapter import EmailSMSAdapter

        adapter = EmailSMSAdapter(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            carrier="att",
        )

        # Test AT&T MMS gateway
        address = adapter.get_gateway_address("5551234567")
        assert address == "5551234567@mms.att.net"

        # Test Verizon MMS gateway
        adapter.carrier = "verizon"
        address = adapter.get_gateway_address("5551234567")
        assert address == "5551234567@vzwpix.com"

        # Test T-Mobile gateway
        adapter.carrier = "tmobile"
        address = adapter.get_gateway_address("5551234567")
        assert address == "5551234567@tmomail.net"

    def test_email_sms_strips_non_digits_from_phone(self) -> None:
        """
        Phone numbers should be normalized to 10-digit US format.
        """
        from src.adapters.email_sms_adapter import EmailSMSAdapter

        adapter = EmailSMSAdapter(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            carrier="att",
        )

        # Various phone formats should normalize to 10 digits
        assert adapter.normalize_phone("(555) 123-4567") == "5551234567"
        assert adapter.normalize_phone("+1-555-123-4567") == "5551234567"  # Strips country code
        assert adapter.normalize_phone("1-555-123-4567") == "5551234567"   # Strips country code
        assert adapter.normalize_phone("555.123.4567") == "5551234567"

    def test_email_sms_sends_via_smtp(
        self,
        sample_alert: Alert,
    ) -> None:
        """
        Email-to-SMS should send via SMTP to carrier gateway.
        """
        from src.adapters.email_sms_adapter import EmailSMSAdapter

        with patch("src.adapters.email_sms_adapter.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            adapter = EmailSMSAdapter(
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                smtp_user="test@gmail.com",
                smtp_password="password",
                carrier="att",
            )

            result = adapter.send(
                phone_number="5551234567",
                alert=sample_alert,
            )

            assert result is True
            mock_server.sendmail.assert_called_once()

            # Verify sent to correct MMS gateway
            call_args = mock_server.sendmail.call_args
            to_address = call_args[0][1]
            assert to_address == "5551234567@mms.att.net"

    def test_message_truncates_explanation_to_fit(
        self,
        sample_alert: Alert,
    ) -> None:
        """
        Long explanations should be truncated to fit SMS limit.
        """
        from src.adapters.email_sms_adapter import EmailSMSAdapter

        # Create alert with very long explanation
        long_alert = Alert(
            symbol="AAPL",
            change_percent=Decimal("5.25"),
            change_amount=Decimal("7.88"),
            previous_price=Decimal("150.00"),
            current_price=Decimal("157.88"),
            explanation=Explanation(
                text="A" * 200,  # Very long explanation
                news_headlines=[],
                model="test",
            ),
        )

        adapter = EmailSMSAdapter(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            carrier="att",
        )

        message = adapter.format_sms_message(long_alert)

        # Must still be under limit
        assert len(message) <= 160
