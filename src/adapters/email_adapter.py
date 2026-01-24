"""Email adapter for sending notifications via SMTP."""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Error sending email."""

    pass


class EmailAdapter:
    """Adapter for sending email notifications via SMTP.

    Args:
        host: SMTP server hostname.
        port: SMTP server port.
        username: SMTP username.
        password: SMTP password or app password.
        use_tls: Whether to use TLS encryption.

    Returns:
        An EmailAdapter instance.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ) -> None:
        """Initialize the email adapter.

        Args:
            host: SMTP server hostname.
            port: SMTP server port.
            username: SMTP username.
            password: SMTP password.
            use_tls: Whether to use TLS (default: True).
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body: Plain text email body.
            html_body: Optional HTML email body.

        Returns:
            True if email was sent successfully.

        Raises:
            EmailError: If sending fails.
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = to_email

            # Attach plain text
            msg.attach(MIMEText(body, "plain"))

            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Create secure context
            context = ssl.create_default_context()

            # Send email
            logger.debug("Connecting to SMTP server %s:%d", self.host, self.port)

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_email, msg.as_string())

            logger.info("Email sent successfully to %s", to_email)
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed: %s", e)
            raise EmailError(f"Authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", e)
            raise EmailError(f"SMTP error: {e}")
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            raise EmailError(f"Failed to send email: {e}")

    def test_connection(self) -> bool:
        """Test SMTP connection without sending.

        Returns:
            True if connection and authentication succeed.
        """
        try:
            context = ssl.create_default_context()

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
                server.noop()

            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error("SMTP connection test failed: %s", e)
            return False
