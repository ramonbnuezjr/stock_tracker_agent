#!/usr/bin/env python3
"""Security smoke test: Verify command injection patterns are rejected.

This script demonstrates that the enhanced validation prevents malicious
input from being processed, protecting against command injection attacks.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.models.validators import validate_stock_symbol
from src.config import Settings


def test_malicious_symbols() -> int:
    """Test that malicious symbols are rejected by validation.

    Returns:
        Exit code (0 if all tests pass, 1 if any fail).
    """
    print("🔒 Security Validation Smoke Test")
    print("=" * 60)
    print()

    # Test cases: (symbol, should_reject, description)
    test_cases = [
        # Valid symbols (should pass)
        ("AAPL", False, "Valid symbol"),
        ("NVDA", False, "Valid symbol"),
        ("BRK.B", False, "Valid class share"),
        ("^NDXT", False, "Valid index"),
        
        # Command injection patterns (should reject)
        ("AAPL; rm -rf /", True, "Shell command separator"),
        ("AAPL | cat", True, "Pipe operator"),
        ("AAPL & echo", True, "Background operator"),
        ("AAPL`whoami`", True, "Command substitution (backticks)"),
        ("$(ls)", True, "Command substitution (dollar)"),
        ("AAPL;rm", True, "Shell command (short)"),
        ("AAPL&&cat", True, "Logical AND"),
        
        # Path traversal (should reject)
        ("../../etc/passwd", True, "Path traversal"),
        ("/etc/passwd", True, "Absolute path"),
        ("C:\\Windows", True, "Windows path"),
        
        # Other dangerous patterns
        ("AAPL < file", True, "Input redirection"),
        ("AAPL > file", True, "Output redirection"),
        ("AAPL(ls)", True, "Command substitution (parens)"),
    ]

    print("Testing symbol validation...")
    print()

    passed = 0
    failed = 0

    for symbol, should_reject, description in test_cases:
        try:
            result = validate_stock_symbol(symbol)
            
            if should_reject:
                print(f"❌ FAIL: {description}")
                print(f"   Symbol: '{symbol}'")
                print(f"   Expected: REJECTED")
                print(f"   Actual: ACCEPTED -> '{result}'")
                print()
                failed += 1
            else:
                print(f"✅ PASS: {description}")
                print(f"   Symbol: '{symbol}' -> '{result}'")
                print()
                passed += 1
                
        except ValueError as e:
            if should_reject:
                print(f"✅ PASS: {description}")
                print(f"   Symbol: '{symbol}'")
                print(f"   Rejected: {str(e)}")
                print()
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Symbol: '{symbol}'")
                print(f"   Expected: ACCEPTED")
                print(f"   Actual: REJECTED -> {str(e)}")
                print()
                failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print()

    if failed > 0:
        print("❌ Security validation test FAILED")
        print("   Some malicious patterns were not rejected!")
        return 1
    else:
        print("✅ Security validation test PASSED")
        print("   All malicious patterns were correctly rejected.")
        return 0


def test_config_validation() -> int:
    """Test that Settings validation rejects malicious symbols.

    Returns:
        Exit code (0 if all tests pass, 1 if any fail).
    """
    print()
    print("🔒 Testing Settings Configuration Validation")
    print("=" * 60)
    print()

    malicious_configs = [
        ("AAPL,NVDA; rm -rf /", "Command injection in symbol list"),
        ("AAPL | cat", "Pipe operator in single symbol"),
        ("AAPL,../../etc/passwd", "Path traversal in symbol list"),
    ]

    print("Attempting to create Settings with malicious symbols...")
    print()

    passed = 0
    failed = 0

    for malicious_symbols, description in malicious_configs:
        try:
            # Try to create Settings with malicious input
            # This should fail during validation
            settings = Settings(stock_symbols=malicious_symbols)
            
            print(f"❌ FAIL: {description}")
            print(f"   Input: '{malicious_symbols}'")
            print(f"   Expected: REJECTED during Settings creation")
            print(f"   Actual: ACCEPTED -> {settings.stock_symbols}")
            print()
            failed += 1
            
        except ValueError as e:
            print(f"✅ PASS: {description}")
            print(f"   Input: '{malicious_symbols}'")
            print(f"   Rejected: {str(e)}")
            print()
            passed += 1
        except Exception as e:
            # Pydantic might raise ValidationError
            print(f"✅ PASS: {description}")
            print(f"   Input: '{malicious_symbols}'")
            print(f"   Rejected: {type(e).__name__}: {str(e)}")
            print()
            passed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print()

    if failed > 0:
        print("❌ Configuration validation test FAILED")
        return 1
    else:
        print("✅ Configuration validation test PASSED")
        return 0


def main() -> int:
    """Run all security validation tests.

    Returns:
        Exit code (0 if all tests pass, 1 if any fail).
    """
    symbol_test_result = test_malicious_symbols()
    config_test_result = test_config_validation()

    print()
    print("=" * 60)
    if symbol_test_result == 0 and config_test_result == 0:
        print("✅ ALL SECURITY TESTS PASSED")
        print()
        print("The application correctly rejects:")
        print("  - Command injection patterns (;, |, &, `, $)")
        print("  - Path traversal patterns (../, /, \\)")
        print("  - Shell operators and redirection")
        print("  - Malicious input in configuration")
        print()
        print("Valid symbols (AAPL, BRK.B, ^NDXT) are accepted.")
        return 0
    else:
        print("❌ SOME SECURITY TESTS FAILED")
        print()
        print("Security validation may not be working correctly!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
