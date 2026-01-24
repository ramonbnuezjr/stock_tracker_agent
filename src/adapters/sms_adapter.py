"""SMS adapter placeholder for future Twilio integration."""

import logging

logger = logging.getLogger(__name__)


class SMSError(Exception):
    """Error sending SMS."""

    pass


class SMSAdapter:
    """Placeholder adapter for SMS notifications via Twilio.

    Note: This is a v0.2 feature and not fully implemented.

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
        """Initialize the SMS adapter.

        Args:
            account_sid: Twilio account SID.
            auth_token: Twilio auth token.
            from_number: Phone number to send from.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send(self, to_number: str, message: str) -> bool:
        """Send an SMS message.

        Args:
            to_number: Recipient phone number.
            message: Message text (max 160 chars recommended).

        Returns:
            True if message was sent.

        Raises:
            SMSError: If sending fails.
        """
        # TODO: Implement Twilio integration in v0.2
        logger.warning(
            "SMS sending not implemented. Message to %s: %s",
            to_number,
            message[:50],
        )
        raise SMSError("SMS adapter not implemented (v0.2 feature)")

    def is_configured(self) -> bool:
        """Check if SMS is properly configured.

        Returns:
            True if all credentials are set.
        """
        return all([
            self.account_sid,
            self.auth_token,
            self.from_number,
        ])
