"""Email-to-SMS adapter using carrier gateways."""

from __future__ import annotations

import logging
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from typing import Dict, Optional

from src.models.alert import Alert

logger = logging.getLogger(__name__)


# Carrier gateway mappings (MMS gateways are more reliable)
CARRIER_GATEWAYS: Dict[str, str] = {
    "att": "mms.att.net",  # MMS gateway is more reliable than txt.att.net
    "verizon": "vzwpix.com",  # MMS gateway
    "tmobile": "tmomail.net",
    "sprint": "pm.sprint.com",  # MMS gateway
    "boost": "myboostmobile.com",
    "cricket": "mms.cricketwireless.net",
    "uscellular": "mms.uscc.net",
    "virgin": "vmpix.com",
    "metro": "mymetropcs.com",
}


class EmailSMSError(Exception):
    """Error sending Email-to-SMS."""

    pass


class EmailSMSAdapter:
    """Adapter for sending SMS via carrier email gateways.

    Uses email-to-SMS gateways to deliver text messages without
    requiring a paid SMS API like Twilio.

    Args:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_user: SMTP username/email.
        smtp_password: SMTP password or app password.
        carrier: Carrier name (att, verizon, tmobile, etc.).

    Returns:
        An EmailSMSAdapter instance.
    """

    SMS_MAX_LENGTH = 160

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        carrier: str,
        use_tls: bool = True,
    ) -> None:
        """Initialize the Email-to-SMS adapter.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_user: SMTP username.
            smtp_password: SMTP password.
            carrier: Carrier name for gateway lookup.
            use_tls: Whether to use TLS (default: True).
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.carrier = carrier.lower()
        self.use_tls = use_tls

    def normalize_phone(self, phone: str) -> str:
        """Remove non-digit characters and normalize to 10-digit US format.

        Args:
            phone: Phone number in any format.

        Returns:
            10-digit US phone number.
        """
        digits = re.sub(r"\D", "", phone)

        # Strip leading '1' country code if present (11 digits -> 10)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        return digits

    def get_gateway_address(self, phone: str) -> str:
        """Build carrier gateway email address.

        Args:
            phone: Phone number (will be normalized).

        Returns:
            Email address for carrier SMS gateway.

        Raises:
            EmailSMSError: If carrier is not supported.
        """
        normalized = self.normalize_phone(phone)
        gateway = CARRIER_GATEWAYS.get(self.carrier)

        if gateway is None:
            supported = ", ".join(CARRIER_GATEWAYS.keys())
            raise EmailSMSError(
                f"Unsupported carrier: {self.carrier}. "
                f"Supported: {supported}"
            )

        return f"{normalized}@{gateway}"

    def format_sms_message(self, alert: Alert) -> str:
        """Format alert as SMS-friendly plain text.

        Args:
            alert: The alert to format.

        Returns:
            Plain text message under 160 characters.
        """
        # Direction indicator
        direction = "↑" if alert.change_percent > 0 else "↓"
        sign = "+" if alert.change_percent > 0 else ""

        # Base message with symbol and change
        base = f"{alert.symbol} {direction}{sign}{alert.change_percent:.1f}%"
        base += f" ${alert.current_price:.2f}"

        # Calculate remaining space for explanation
        # Reserve space for " - " separator
        remaining = self.SMS_MAX_LENGTH - len(base) - 3

        if alert.explanation and remaining > 10:
            explain = alert.explanation.text[:remaining]
            # Truncate at word boundary if needed
            if len(alert.explanation.text) > remaining:
                if " " in explain:
                    explain = explain.rsplit(" ", 1)[0]
                explain += "..."
            base += f" - {explain}"

        return base[:self.SMS_MAX_LENGTH]

    def send(
        self,
        phone_number: str,
        alert: Alert,
    ) -> bool:
        """Send alert via Email-to-SMS gateway.

        Args:
            phone_number: Recipient phone number.
            alert: The alert to send.

        Returns:
            True if message was sent successfully.

        Raises:
            EmailSMSError: If sending fails.
        """
        try:
            # Build gateway address
            to_address = self.get_gateway_address(phone_number)

            # Format message
            message_text = self.format_sms_message(alert)

            # Create plain text email with subject (MMS gateways often require it)
            msg = MIMEText(message_text, "plain")
            msg["From"] = self.smtp_user
            msg["To"] = to_address
            msg["Subject"] = "Stock Alert"

            # Send via SMTP
            context = ssl.create_default_context()

            logger.debug(
                "Sending SMS via %s to %s",
                self.carrier,
                to_address,
            )

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_address, msg.as_string())

            logger.info(
                "SMS sent to %s via %s gateway",
                phone_number,
                self.carrier,
            )
            return True

        except EmailSMSError:
            raise
        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed: %s", e)
            raise EmailSMSError(f"Authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", e)
            raise EmailSMSError(f"SMTP error: {e}")
        except Exception as e:
            logger.error("Failed to send SMS: %s", e)
            raise EmailSMSError(f"Failed to send SMS: {e}")

    def test_connection(self) -> bool:
        """Test SMTP connection.

        Returns:
            True if connection and authentication succeed.
        """
        try:
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.noop()

            logger.info("Email-to-SMS connection test successful")
            return True

        except Exception as e:
            logger.error("Connection test failed: %s", e)
            return False
