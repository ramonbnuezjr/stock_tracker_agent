# Security Logging

This document describes the security logging implementation for the Stock Tracker application.

## Overview

Security logging tracks validation failures and security violations to enable:
- **Threat Detection**: Identify attack patterns and malicious input attempts
- **Incident Response**: Understand what happened during security events
- **Compliance**: Maintain audit trails for security requirements
- **Forensics**: Investigate security incidents with detailed logs

## Implementation

### Security Logger

The `SecurityLogger` class (`src/security_logger.py`) provides:
- **Dedicated log file**: `logs/security.log` (separate from application logs)
- **Structured logging**: Consistent format with context information
- **Sanitization**: Input is sanitized to prevent log injection attacks
- **Singleton pattern**: Single logger instance across the application

### What Gets Logged

Security violations are logged when:

1. **Validation Rejections**:
   - Empty symbols
   - Symbols exceeding length limits
   - Prohibited characters detected
   - Command injection patterns detected
   - Path traversal attempts

2. **Context Information**:
   - Validation type (stock_symbol, settings_stock_symbols)
   - Validation rule violated
   - Source (environment_variable, user_input, etc.)
   - Detected patterns (for command injection)

### Log Format

Each security log entry includes:

```
TIMESTAMP [SECURITY] LEVEL: Validation rejected: REASON | Input (sanitized): INPUT | Context: KEY=VALUE, ...
```

**Example:**
```
2026-01-25 09:10:31 [SECURITY] WARNING: Validation rejected: Command injection pattern detected: ; | Input (sanitized): AAPL;rm | Context: validation_type=stock_symbol, rule=command_injection_prevention, detected_patterns=[';'], threat_type=command_injection
```

### Security Features

1. **Input Sanitization**:
   - Newlines and control characters removed
   - Length limited (max 100 chars for input, 50 for context)
   - Multiple spaces collapsed
   - Prevents log injection attacks

2. **Separate Log File**:
   - Security logs isolated from application logs
   - Easier to monitor and analyze
   - Can be forwarded to SIEM systems

3. **Structured Context**:
   - Machine-readable format
   - Enables automated analysis
   - Supports pattern detection

## Usage

Security logging is automatic. When validation fails, the security logger is invoked:

```python
from src.models.validators import validate_stock_symbol

# This will log to security.log if validation fails
try:
    symbol = validate_stock_symbol("AAPL; rm -rf /")
except ValueError:
    # Security violation logged automatically
    pass
```

## Monitoring

### View Security Logs

```bash
# View recent security violations
tail -f logs/security.log

# Count violations
wc -l logs/security.log

# Search for specific patterns
grep "command_injection" logs/security.log
```

### Log Rotation

Security logs should be rotated to prevent disk space issues:

```bash
# Example logrotate configuration
logs/security.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

## Best Practices

1. **Regular Review**: Review security logs regularly for patterns
2. **Alerting**: Set up alerts for repeated violations from same source
3. **Retention**: Keep logs for compliance requirements (typically 90 days)
4. **Access Control**: Restrict access to security logs
5. **Backup**: Include security logs in backup strategy

## Integration Points

Security logging is integrated at:

1. **Symbol Validation** (`src/models/validators.py`):
   - `validate_stock_symbol()` logs all rejections

2. **Configuration Validation** (`src/config.py`):
   - `Settings.validate_symbols()` logs configuration-level violations

3. **Future Extensions**:
   - Authentication failures
   - Authorization violations
   - Rate limit violations
   - Suspicious patterns

## Compliance

Security logging supports compliance with:
- **OWASP**: Input validation and security logging requirements
- **SOC 2**: Security monitoring and incident response
- **ISO 27001**: Security event logging requirements

## Notes

- Security logs are **not** included in git (see `.gitignore`)
- Logs contain sanitized input only (no full malicious payloads)
- Log level is WARNING (only security violations, not successful validations)
- Singleton pattern ensures consistent logging across the application
