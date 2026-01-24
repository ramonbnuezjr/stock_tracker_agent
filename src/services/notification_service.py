"""Notification service for sending stock alerts."""

from __future__ import annotations

import logging
import platform
from typing import List, Optional

from src.adapters.email_adapter import EmailAdapter, EmailError
from src.adapters.email_sms_adapter import EmailSMSAdapter, EmailSMSError
from src.adapters.sms_adapter import SMSAdapter, SMSError
from src.adapters.apple_messages_adapter import AppleMessagesAdapter, AppleMessagesError
from src.config import NotificationChannel, Settings
from src.models.alert import Alert

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Error sending notification."""

    pass


class NotificationService:
    """Service for sending stock alert notifications.

    Supports multiple channels with automatic fallback:
    - Twilio SMS (primary when enabled)
    - Apple Messages (local Mac fallback)
    - Console (final fallback)

    Args:
        settings: Application settings.

    Returns:
        A NotificationService instance.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the notification service.

        Args:
            settings: Application settings with notification config.
        """
        self.settings = settings
        self.channel = settings.notification_channel

        # Initialize adapters
        self._email_adapter: Optional[EmailAdapter] = None
        self._sms_adapter: Optional[SMSAdapter] = None
        self._email_sms_adapter: Optional[EmailSMSAdapter] = None
        self._apple_messages_adapter: Optional[AppleMessagesAdapter] = None

        # Handle AUTO channel - determine best available
        if self.channel == NotificationChannel.AUTO:
            self._setup_auto_channel()
        else:
            self._setup_explicit_channel()

    def _setup_auto_channel(self) -> None:
        """Configure automatic channel selection with fallback.

        Priority: Twilio → Apple Messages → Console
        """
        # Try Twilio first
        if self.settings.enable_twilio and self.settings.validate_sms_config():
            self._sms_adapter = SMSAdapter(
                account_sid=self.settings.twilio_account_sid,
                auth_token=self.settings.twilio_auth_token,
                from_number=self.settings.twilio_from_number,
            )
            self.channel = NotificationChannel.SMS
            logger.info("Auto-selected Twilio SMS as notification channel")
            return

        # Try Apple Messages on Mac
        if platform.system() == "Darwin" and self.settings.notify_phone:
            self._apple_messages_adapter = AppleMessagesAdapter(
                recipient=self.settings.notify_phone
            )
            if self._apple_messages_adapter.is_available():
                self.channel = NotificationChannel.APPLE_MESSAGES
                logger.info("Auto-selected Apple Messages as notification channel")
                return

        # Fallback to console
        self.channel = NotificationChannel.CONSOLE
        logger.info("Auto-selected Console as notification channel")

    def _setup_explicit_channel(self) -> None:
        """Configure explicitly selected channel."""
        if self.channel == NotificationChannel.EMAIL:
            if self.settings.validate_email_config():
                self._email_adapter = EmailAdapter(
                    host=self.settings.smtp_host,
                    port=self.settings.smtp_port,
                    username=self.settings.smtp_user,
                    password=self.settings.smtp_password,
                )
            else:
                logger.warning(
                    "Email channel selected but config incomplete, "
                    "falling back to console"
                )
                self.channel = NotificationChannel.CONSOLE

        elif self.channel == NotificationChannel.SMS:
            if self.settings.validate_sms_config():
                self._sms_adapter = SMSAdapter(
                    account_sid=self.settings.twilio_account_sid,
                    auth_token=self.settings.twilio_auth_token,
                    from_number=self.settings.twilio_from_number,
                )
            else:
                logger.warning(
                    "Twilio SMS channel selected but config incomplete, "
                    "falling back to console"
                )
                self.channel = NotificationChannel.CONSOLE

        elif self.channel == NotificationChannel.EMAIL_SMS:
            if self.settings.validate_email_sms_config():
                self._email_sms_adapter = EmailSMSAdapter(
                    smtp_host=self.settings.smtp_host,
                    smtp_port=self.settings.smtp_port,
                    smtp_user=self.settings.smtp_user,
                    smtp_password=self.settings.smtp_password,
                    carrier=self.settings.sms_carrier,
                )
            else:
                logger.warning(
                    "Email-to-SMS channel selected but config incomplete, "
                    "falling back to console"
                )
                self.channel = NotificationChannel.CONSOLE

        elif self.channel == NotificationChannel.APPLE_MESSAGES:
            if platform.system() == "Darwin" and self.settings.notify_phone:
                self._apple_messages_adapter = AppleMessagesAdapter(
                    recipient=self.settings.notify_phone
                )
                if not self._apple_messages_adapter.is_available():
                    logger.warning(
                        "Apple Messages not available, falling back to console"
                    )
                    self.channel = NotificationChannel.CONSOLE
            else:
                logger.warning(
                    "Apple Messages requires macOS, falling back to console"
                )
                self.channel = NotificationChannel.CONSOLE

    def send_alert(self, alert: Alert) -> bool:
        """Send a stock alert notification.

        Args:
            alert: The alert to send.

        Returns:
            True if notification was sent successfully.
        """
        logger.info(
            "Sending alert for %s via %s",
            alert.symbol,
            self.channel.value,
        )

        try:
            if self.channel == NotificationChannel.CONSOLE:
                return self._send_console(alert)
            elif self.channel == NotificationChannel.EMAIL:
                return self._send_email(alert)
            elif self.channel == NotificationChannel.SMS:
                return self._send_sms(alert)
            elif self.channel == NotificationChannel.EMAIL_SMS:
                return self._send_email_sms(alert)
            elif self.channel == NotificationChannel.APPLE_MESSAGES:
                return self._send_apple_messages(alert)
            else:
                logger.error("Unknown notification channel: %s", self.channel)
                return False
        except Exception as e:
            logger.error("Failed to send notification: %s", e)
            return False

    def _send_console(self, alert: Alert) -> bool:
        """Send alert to console output.

        Args:
            alert: The alert to display.

        Returns:
            Always True.
        """
        print("\n" + "=" * 60)
        print("STOCK ALERT")
        print("=" * 60)
        print(alert.format_message())
        print("=" * 60 + "\n")
        return True

    def _send_email(self, alert: Alert) -> bool:
        """Send alert via email.

        Args:
            alert: The alert to send.

        Returns:
            True if email was sent.
        """
        if self._email_adapter is None:
            logger.error("Email adapter not initialized")
            return self._send_console(alert)

        subject = self._format_email_subject(alert)
        body = alert.format_message()
        html_body = self._format_html_body(alert)

        try:
            return self._email_adapter.send(
                to_email=self.settings.notify_email,
                subject=subject,
                body=body,
                html_body=html_body,
            )
        except EmailError as e:
            logger.error("Email sending failed: %s", e)
            return self._send_console(alert)

    def _send_sms(self, alert: Alert) -> bool:
        """Send alert via Twilio SMS.

        Args:
            alert: The alert to send.

        Returns:
            True if SMS was sent.
        """
        if self._sms_adapter is None:
            logger.error("SMS adapter not initialized")
            return self._fallback_send(alert)

        try:
            return self._sms_adapter.send(
                to_number=self.settings.notify_phone,
                message=alert.format_short(),
            )
        except SMSError as e:
            logger.error("Twilio SMS failed: %s", e)
            return self._fallback_send(alert)

    def _send_email_sms(self, alert: Alert) -> bool:
        """Send alert via Email-to-SMS gateway.

        Args:
            alert: The alert to send.

        Returns:
            True if SMS was sent.
        """
        if self._email_sms_adapter is None:
            logger.error("Email-to-SMS adapter not initialized")
            return self._send_console(alert)

        try:
            return self._email_sms_adapter.send(
                phone_number=self.settings.notify_phone,
                alert=alert,
            )
        except EmailSMSError as e:
            logger.error("Email-to-SMS sending failed: %s", e)
            return self._send_console(alert)

    def _send_apple_messages(self, alert: Alert) -> bool:
        """Send alert via Apple Messages.

        Args:
            alert: The alert to send.

        Returns:
            True if message was sent.
        """
        if self._apple_messages_adapter is None:
            logger.error("Apple Messages adapter not initialized")
            return self._send_console(alert)

        try:
            return self._apple_messages_adapter.send(alert.format_short())
        except AppleMessagesError as e:
            logger.error("Apple Messages failed: %s", e)
            return self._send_console(alert)

    def _fallback_send(self, alert: Alert) -> bool:
        """Try fallback channels when primary fails.

        Fallback order: Apple Messages → Console

        Args:
            alert: The alert to send.

        Returns:
            True if any fallback succeeded.
        """
        # Try Apple Messages on Mac
        if platform.system() == "Darwin" and self.settings.notify_phone:
            try:
                adapter = AppleMessagesAdapter(recipient=self.settings.notify_phone)
                if adapter.is_available():
                    logger.info("Falling back to Apple Messages")
                    return adapter.send(alert.format_short())
            except AppleMessagesError as e:
                logger.warning("Apple Messages fallback failed: %s", e)

        # Final fallback to console
        logger.info("Falling back to console output")
        return self._send_console(alert)

    def _format_email_subject(self, alert: Alert) -> str:
        """Format email subject line.

        Args:
            alert: The alert.

        Returns:
            Formatted subject string.
        """
        direction = "UP" if alert.change_percent > 0 else "DOWN"
        sign = "+" if alert.change_percent > 0 else ""
        return (
            f"Stock Alert: {alert.symbol} {direction} "
            f"{sign}{alert.change_percent:.1f}%"
        )

    def _format_html_body(self, alert: Alert) -> str:
        """Format HTML email body.

        Args:
            alert: The alert.

        Returns:
            HTML formatted string.
        """
        direction_color = "#22c55e" if alert.change_percent > 0 else "#ef4444"
        sign = "+" if alert.change_percent > 0 else ""

        explanation_html = ""
        if alert.explanation:
            explanation_html = f"""
            <p style="margin-top: 20px; padding: 15px; background: #f5f5f5;
                      border-radius: 8px;">
                {alert.explanation.text}
            </p>
            """

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, sans-serif; padding: 20px;">
            <h2 style="margin-bottom: 10px;">
                {alert.direction_emoji} {alert.symbol}
            </h2>
            <p style="font-size: 24px; color: {direction_color};
                      margin: 10px 0;">
                {sign}{alert.change_percent:.2f}%
            </p>
            <p style="color: #666;">
                ${alert.previous_price:.2f} → ${alert.current_price:.2f}
            </p>
            {explanation_html}
            <hr style="margin-top: 30px; border: none;
                       border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #999;">
                Stock Tracker Alert • {alert.timestamp.strftime("%Y-%m-%d %H:%M UTC")}
            </p>
        </body>
        </html>
        """

    def send_alerts(self, alerts: List[Alert]) -> int:
        """Send multiple alerts.

        Args:
            alerts: List of alerts to send.

        Returns:
            Number of successfully sent notifications.
        """
        sent = 0
        for alert in alerts:
            if self.send_alert(alert):
                sent += 1
        return sent

    def test_notification(self) -> bool:
        """Send a test notification.

        Returns:
            True if test notification was sent.
        """
        from decimal import Decimal
        from datetime import datetime

        test_alert = Alert(
            symbol="TEST",
            change_percent=Decimal("2.5"),
            change_amount=Decimal("5.00"),
            previous_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            timestamp=datetime.utcnow(),
        )

        return self.send_alert(test_alert)
