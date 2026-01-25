"""Tests for stock symbol validation security."""

import pytest

from src.models.validators import validate_stock_symbol


class TestSymbolValidation:
    """Test cases for symbol validation security."""

    def test_valid_symbols(self):
        """Valid symbols should pass validation."""
        assert validate_stock_symbol("AAPL") == "AAPL"
        assert validate_stock_symbol("NVDA") == "NVDA"
        assert validate_stock_symbol("MSFT") == "MSFT"
        assert validate_stock_symbol("aapl") == "AAPL"  # Lowercase normalized

    def test_class_shares(self):
        """Class shares with dots should be allowed."""
        assert validate_stock_symbol("BRK.B") == "BRK.B"
        assert validate_stock_symbol("GOOGL") == "GOOGL"

    def test_indices(self):
        """Index symbols with carets should be allowed."""
        assert validate_stock_symbol("^NDXT") == "^NDXT"
        assert validate_stock_symbol("^GSPC") == "^GSPC"

    def test_hyphenated_symbols(self):
        """Hyphenated symbols should be allowed."""
        assert validate_stock_symbol("BRK-A") == "BRK-A"

    def test_rejects_command_injection_patterns(self):
        """Should reject symbols that could be used for command injection."""
        dangerous = [
            "AAPL; ls",  # Shell command separator
            "AAPL | cat",  # Pipe operator
            "AAPL & echo",  # Background operator
            "AAPL`whoami`",  # Command substitution
            "$(ls)",  # Command substitution
            "AAPL;rm",  # Shell command separator (short)
            "AAPL&&cat",  # Logical AND (short)
        ]

        for symbol in dangerous:
            # Should raise ValueError for any reason (length, prohibited chars, etc.)
            with pytest.raises(ValueError):
                validate_stock_symbol(symbol)

    def test_rejects_path_traversal(self):
        """Should reject path traversal patterns."""
        dangerous = [
            "../../etc/passwd",
            "..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows",
        ]

        for symbol in dangerous:
            with pytest.raises(ValueError):
                validate_stock_symbol(symbol)

    def test_rejects_shell_operators(self):
        """Should reject shell operators."""
        dangerous = ["|", "&", ";", "`", "$", "(", ")", "<", ">"]

        for char in dangerous:
            with pytest.raises(ValueError):
                validate_stock_symbol(f"AAPL{char}")

    def test_rejects_empty_string(self):
        """Should reject empty strings."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_stock_symbol("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_stock_symbol("   ")

    def test_rejects_too_long(self):
        """Should reject symbols longer than 10 characters."""
        with pytest.raises(ValueError, match="10 characters"):
            validate_stock_symbol("A" * 11)

    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        assert validate_stock_symbol("  AAPL  ") == "AAPL"
        assert validate_stock_symbol("\tNVDA\n") == "NVDA"
