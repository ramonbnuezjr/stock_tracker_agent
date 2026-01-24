"""Notification service for sending stock alerts."""

from __future__ import annotations

import logging
from typing import List, Optional

from src.adapters.email_adapter import EmailAdapter, EmailError
from src.adapters.sms_adapter import SMSAdapter, SMSError
from src.config import NotificationChannel, Settings
from src.models.alert import Alert

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Error sending notification."""

    pass


class NotificationService:
    """Service for sending stock alert notifications.

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

        # Initialize adapters based on channel
        self._email_adapter: Optional[EmailAdapter] = None
        self._sms_adapter: Optional[SMSAdapter] = None

        if self.channel == NotificationChannel.EMAIL:
            if settings.validate_email_config():
                self._email_adapter = EmailAdapter(
                    host=settings.smtp_host,
                    port=settings.smtp_port,
                    username=settings.smtp_user,
                    password=settings.smtp_password,
                )
            else:
                logger.warning(
                    "Email channel selected but config incomplete, "
                    "falling back to console"
                )
                self.channel = NotificationChannel.CONSOLE

        elif self.channel == NotificationChannel.SMS:
            if settings.validate_sms_config():
                self._sms_adapter = SMSAdapter(
                    account_sid=settings.twilio_account_sid,
                    auth_token=settings.twilio_auth_token,
                    from_number=settings.twilio_from_number,
                )
            else:
                logger.warning(
                    "SMS channel selected but config incomplete, "
                    "falling back to console"
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

        Raises:
            NotificationError: If sending fails.
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
            # Fallback to console
            return self._send_console(alert)

    def _send_sms(self, alert: Alert) -> bool:
        """Send alert via SMS.

        Args:
            alert: The alert to send.

        Returns:
            True if SMS was sent.
        """
        if self._sms_adapter is None:
            logger.error("SMS adapter not initialized")
            return self._send_console(alert)

        try:
            return self._sms_adapter.send(
                to_number=self.settings.notify_phone,
                message=alert.format_short(),
            )
        except SMSError as e:
            logger.error("SMS sending failed: %s", e)
            # Fallback to console
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
