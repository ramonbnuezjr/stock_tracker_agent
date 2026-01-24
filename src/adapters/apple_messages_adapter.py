"""Apple Messages adapter using AppleScript (macOS only)."""

from __future__ import annotations

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class AppleMessagesError(Exception):
    """Error sending Apple Messages."""

    pass


class AppleMessagesAdapter:
    """Adapter for sending messages via Apple Messages (iMessage/SMS).

    Uses AppleScript to send messages through the macOS Messages app.
    Works with both iMessage and SMS (if iPhone is linked).

    Args:
        recipient: Phone number or Apple ID email.

    Returns:
        An AppleMessagesAdapter instance.
    """

    def __init__(self, recipient: str) -> None:
        """Initialize the Apple Messages adapter.

        Args:
            recipient: Phone number or Apple ID to send to.
        """
        self.recipient = recipient
        self._is_macos: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Apple Messages is available on this system.

        Returns:
            True if running on macOS with Messages app.
        """
        if self._is_macos is None:
            self._is_macos = platform.system() == "Darwin"

        if not self._is_macos:
            return False

        # Check if Messages app exists
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Messages" to name'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def send(self, message: str) -> bool:
        """Send a message via Apple Messages.

        Args:
            message: The message text to send.

        Returns:
            True if message was sent.

        Raises:
            AppleMessagesError: If sending fails.
        """
        if not self.is_available():
            raise AppleMessagesError(
                "Apple Messages not available (macOS only)"
            )

        try:
            # Escape special characters for AppleScript
            escaped_message = self._escape_for_applescript(message)
            escaped_recipient = self._escape_for_applescript(self.recipient)

            # AppleScript to send message
            script = f'''
            tell application "Messages"
                set targetService to 1st account whose service type = iMessage
                set targetBuddy to participant "{escaped_recipient}" of targetService
                send "{escaped_message}" to targetBuddy
            end tell
            '''

            logger.debug("Sending via Apple Messages to %s", self.recipient)

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Try SMS service as fallback
                return self._send_via_sms_service(escaped_message, escaped_recipient)

            logger.info("Message sent via Apple Messages to %s", self.recipient)
            return True

        except subprocess.TimeoutExpired:
            logger.error("Apple Messages send timed out")
            raise AppleMessagesError("Message send timed out")
        except Exception as e:
            logger.error("Apple Messages failed: %s", e)
            raise AppleMessagesError(f"Failed to send: {e}")

    def _send_via_sms_service(self, message: str, recipient: str) -> bool:
        """Try sending via SMS service (requires iPhone).

        Args:
            message: Escaped message text.
            recipient: Escaped recipient.

        Returns:
            True if sent successfully.

        Raises:
            AppleMessagesError: If sending fails.
        """
        # Alternative script that works with SMS
        script = f'''
        tell application "Messages"
            set targetBuddy to buddy "{recipient}" of (service 1 whose service type is SMS)
            send "{message}" to targetBuddy
        end tell
        '''

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            error = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error("Apple Messages SMS fallback failed: %s", error)
            raise AppleMessagesError(f"Failed to send: {error}")

        logger.info("Message sent via Apple Messages SMS to %s", self.recipient)
        return True

    def _escape_for_applescript(self, text: str) -> str:
        """Escape special characters for AppleScript strings.

        Args:
            text: Text to escape.

        Returns:
            Escaped text safe for AppleScript.
        """
        # Escape backslashes first, then quotes
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        return text

    @staticmethod
    def is_local_mac() -> bool:
        """Check if running on a local Mac.

        Returns:
            True if running on macOS.
        """
        return platform.system() == "Darwin"
