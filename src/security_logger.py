"""Security logging for tracking validation failures and security violations.

This module provides a dedicated security logger that writes to a separate
log file to track security events like rejected validation attempts.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional


class SecurityLogger:
    """Dedicated logger for security events.

    Writes security violations to a separate log file for monitoring
    and incident response. Logs are structured and sanitized to prevent
    log injection while providing useful context.

    Attributes:
        logger: The security logger instance.
        log_file: Path to the security log file.
    """

    _instance: Optional[SecurityLogger] = None
    _initialized: bool = False

    def __new__(cls, log_file: Optional[Path] = None) -> SecurityLogger:
        """Create singleton instance of SecurityLogger.

        Args:
            log_file: Optional path to security log file.
                     Defaults to ./logs/security.log

        Returns:
            The SecurityLogger singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_file: Optional[Path] = None) -> None:
        """Initialize the security logger.

        Args:
            log_file: Optional path to security log file.
        """
        if self._initialized:
            return

        # Set default log file path
        if log_file is None:
            log_dir = Path("./logs")
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / "security.log"
        else:
            self.log_file = log_file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create dedicated security logger
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.WARNING)  # Only WARNING and above

        # Prevent propagation to root logger
        self.logger.propagate = False

        # Create file handler for security log
        file_handler = logging.FileHandler(
            self.log_file,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.WARNING)

        # Structured format for security logs
        formatter = logging.Formatter(
            fmt="%(asctime)s [SECURITY] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self._initialized = True

    def log_validation_rejection(
        self,
        input_value: str,
        reason: str,
        context: Optional[dict] = None,
    ) -> None:
        """Log a rejected validation attempt.

        Logs security violations when malicious input is detected and
        rejected. Input is sanitized to prevent log injection.

        Args:
            input_value: The rejected input value (will be sanitized).
            reason: Why the validation failed.
            context: Optional additional context (source, user, etc.).
        """
        # Sanitize input to prevent log injection
        # Remove newlines, control characters, and limit length
        sanitized = self._sanitize_for_logging(input_value, max_length=100)

        # Build log message
        message_parts = [
            f"Validation rejected: {reason}",
            f"Input (sanitized): {sanitized}",
        ]

        if context:
            context_str = ", ".join(
                f"{k}={self._sanitize_for_logging(str(v), max_length=50)}"
                for k, v in context.items()
            )
            message_parts.append(f"Context: {context_str}")

        message = " | ".join(message_parts)

        self.logger.warning(message)

    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "WARNING",
        context: Optional[dict] = None,
    ) -> None:
        """Log a general security event.

        Args:
            event_type: Type of security event (e.g., "validation_rejection").
            description: Description of the event.
            severity: Severity level (WARNING, ERROR, CRITICAL).
            context: Optional additional context.
        """
        message_parts = [
            f"Event: {event_type}",
            f"Description: {description}",
        ]

        if context:
            context_str = ", ".join(
                f"{k}={self._sanitize_for_logging(str(v), max_length=50)}"
                for k, v in context.items()
            )
            message_parts.append(f"Context: {context_str}")

        message = " | ".join(message_parts)

        level = getattr(logging, severity.upper(), logging.WARNING)
        self.logger.log(level, message)

    @staticmethod
    def _sanitize_for_logging(value: str, max_length: int = 100) -> str:
        """Sanitize input for safe logging.

        Prevents log injection by removing dangerous characters and
        limiting length. Does not log full malicious payloads.

        Args:
            value: The value to sanitize.
            max_length: Maximum length of sanitized value.

        Returns:
            Sanitized string safe for logging.
        """
        if not value:
            return ""

        # Remove newlines and control characters
        sanitized = re.sub(r"[\r\n\t]", " ", value)
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        # Replace multiple spaces with single space
        sanitized = re.sub(r" +", " ", sanitized).strip()

        return sanitized


def get_security_logger(log_file: Optional[Path] = None) -> SecurityLogger:
    """Get the security logger singleton instance.

    Args:
        log_file: Optional path to security log file.

    Returns:
        The SecurityLogger instance.
    """
    return SecurityLogger(log_file)
