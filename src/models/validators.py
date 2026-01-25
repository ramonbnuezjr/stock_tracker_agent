"""Shared validation functions for stock symbols and related data."""

from __future__ import annotations

from src.security_logger import get_security_logger


def validate_stock_symbol(symbol: str) -> str:
    """Validate and normalize a stock symbol.

    Ensures symbol is uppercase, alphanumeric, and allows common
    special characters for indices and class shares (dots, carets, hyphens).

    Args:
        symbol: The stock symbol to validate.

    Returns:
        The validated, uppercase, stripped symbol.

    Raises:
        ValueError: If symbol is invalid or contains prohibited characters.

    Examples:
        >>> validate_stock_symbol("aapl")
        'AAPL'
        >>> validate_stock_symbol("BRK.B")
        'BRK.B'
        >>> validate_stock_symbol("^NDXT")
        '^NDXT'
        >>> validate_stock_symbol("rm -rf /")
        Traceback (most recent call last):
        ...
        ValueError: Symbol must be alphanumeric (dots, ^, - allowed)
    """
    cleaned = symbol.upper().strip()

    security_logger = get_security_logger()

    if not cleaned:
        reason = "Empty symbol"
        security_logger.log_validation_rejection(
            input_value=symbol,
            reason=reason,
            context={"validation_type": "stock_symbol", "rule": "non_empty"},
        )
        raise ValueError("Symbol cannot be empty")

    if len(cleaned) > 10:
        reason = "Symbol exceeds maximum length (10 characters)"
        security_logger.log_validation_rejection(
            input_value=symbol,
            reason=reason,
            context={
                "validation_type": "stock_symbol",
                "rule": "max_length",
                "length": len(cleaned),
            },
        )
        raise ValueError("Symbol must be 10 characters or less")

    # Allow alphanumeric plus common special characters for:
    # - Class shares: BRK.B, GOOGL
    # - Indices: ^NDXT, ^GSPC
    # - Hyphenated: BRK-A
    allowed_chars = set(".^-")
    if not all(c.isalnum() or c in allowed_chars for c in cleaned):
        reason = "Prohibited characters detected (non-alphanumeric, not in allowed set)"
        security_logger.log_validation_rejection(
            input_value=symbol,
            reason=reason,
            context={
                "validation_type": "stock_symbol",
                "rule": "alphanumeric_with_allowed",
                "allowed_chars": ".^-",
            },
        )
        raise ValueError(
            "Symbol must be alphanumeric (dots, ^, - allowed). "
            "Prohibited characters detected."
        )

    # Security: Prevent command injection patterns
    # Reject if it looks like shell commands or paths
    dangerous_patterns = ["/", "\\", "|", "&", ";", "`", "$", "(", ")", "<", ">"]
    detected_patterns = [p for p in dangerous_patterns if p in cleaned]
    if detected_patterns:
        reason = f"Command injection pattern detected: {', '.join(detected_patterns)}"
        security_logger.log_validation_rejection(
            input_value=symbol,
            reason=reason,
            context={
                "validation_type": "stock_symbol",
                "rule": "command_injection_prevention",
                "detected_patterns": detected_patterns,
                "threat_type": "command_injection",
            },
        )
        raise ValueError(
            "Symbol contains prohibited characters that could be used for "
            "command injection"
        )

    return cleaned
