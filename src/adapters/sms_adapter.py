"""SMS adapter using Twilio API."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SMSError(Exception):
    """Error sending SMS."""

    pass


class SMSAdapter:
    """Adapter for SMS notifications via Twilio.

    Args:
        account_sid: Twilio account SID.
        auth_token: Twilio auth token.
        from_number: Twilio phone number to send from.

    Returns:
        An SMSAdapter instance.
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
    ) -> None:
        """Initialize the Twilio SMS adapter.

        Args:
            account_sid: Twilio account SID.
            auth_token: Twilio auth token.
            from_number: Phone number to send from.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self._client: Optional[object] = None

    def _get_client(self) -> object:
        """Lazily initialize the Twilio client.

        Returns:
            Twilio Client instance.

        Raises:
            SMSError: If twilio package is not installed.
        """
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                raise SMSError(
                    "Twilio package not installed. Run: pip install twilio"
                )
        return self._client

    def send(self, to_number: str, message: str) -> bool:
        """Send an SMS message via Twilio.

        Args:
            to_number: Recipient phone number (E.164 format recommended).
            message: Message text.

        Returns:
            True if message was sent.

        Raises:
            SMSError: If sending fails.
        """
        try:
            client = self._get_client()

            # Ensure numbers are in E.164 format
            to_formatted = self._format_e164(to_number)
            from_formatted = self._format_e164(self.from_number)

            logger.debug(
                "Sending SMS from %s to %s",
                from_formatted,
                to_formatted,
            )

            # Send via Twilio
            msg = client.messages.create(
                body=message,
                from_=from_formatted,
                to=to_formatted,
            )

            logger.info(
                "SMS sent via Twilio. SID: %s, Status: %s",
                msg.sid,
                msg.status,
            )
            return True

        except SMSError:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error("Twilio SMS failed: %s", error_msg)
            raise SMSError(f"Twilio error: {error_msg}")

    def _format_e164(self, phone: str) -> str:
        """Format phone number to E.164 format.

        Args:
            phone: Phone number in any format.

        Returns:
            Phone number in E.164 format (+1XXXXXXXXXX).
        """
        import re

        # Remove non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Add country code if missing
        if len(digits) == 10:
            digits = "1" + digits

        return f"+{digits}"

    def is_configured(self) -> bool:
        """Check if Twilio is properly configured.

        Returns:
            True if all credentials are set.
        """
        return all([
            self.account_sid,
            self.auth_token,
            self.from_number,
        ])

    def test_connection(self) -> bool:
        """Test Twilio API connection.

        Returns:
            True if connection is successful.
        """
        try:
            client = self._get_client()
            # Verify account by fetching account info
            account = client.api.accounts(self.account_sid).fetch()
            logger.info(
                "Twilio connection OK. Account status: %s",
                account.status,
            )
            return True
        except Exception as e:
            logger.error("Twilio connection test failed: %s", e)
            return False
