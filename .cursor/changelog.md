# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Expanded stock tracking to 12 tech stocks (from 3)
- New symbols: AVGO, AMD, INTC, AMZN, GOOG, META, TSM, MU, ASML

### Changed
- Default `STOCK_SYMBOLS` now includes 12 tech stocks
- Updated `.env.example` with expanded symbol list
- Updated README configuration documentation

---

## [0.5.0] - 2026-01-25

### Added
- Security logging for rejected validation attempts
- Dedicated security logger (`src/security_logger.py`)
- Shared symbol validation function (`src/models/validators.py`)
- Security log file (`logs/security.log`) for tracking violations
- Comprehensive security validation tests (`tests/test_symbol_validation.py`)
- Security validation smoke test script (`scripts/test_security_validation.py`)
- `SECURITY_LOGGING.md` documentation

### Changed
- Enhanced symbol validation across all models (Stock, PricePoint, PriceChange, PriceQuote, Alert)
- Settings validation now validates each symbol individually
- Improved security posture with command injection prevention
- All models now use shared validator for consistency

### Security
- Rejects command injection patterns (;, |, &, `, $, etc.)
- Rejects path traversal patterns (../, /, \)
- Logs all validation rejections to security log
- Sanitizes input for safe logging (prevents log injection)

---

## [0.4.0] - 2026-01-24

### Added
- macOS launchd service setup for automatic execution
- Service installation script (`scripts/install_service.sh`)
- Service uninstallation script (`scripts/uninstall_service.sh`)
- Test script for Apple Messages notifications (`scripts/test_imessage_notification.py`)
- `SETUP_MACOS.md` guide for macOS service setup
- Service management documentation in README

### Changed
- Updated README with macOS service management commands
- Updated `.gitignore` to exclude logs/ and data/ directories

### Technical
- Service runs every 30 minutes automatically
- Plist file generated dynamically with project paths
- Service can be managed via launchctl commands

---

## [0.3.0] - 2026-01-24

### Added
- Multi-provider market data strategy with automatic fallback
- `PriceQuote` model for normalized market data across providers
- Four market data providers:
  - `FinnhubProvider` (60 calls/min free tier)
  - `TwelveDataProvider` (800 calls/day free tier)
  - `AlphaVantageProvider` (25 calls/day free tier)
  - `YahooFinanceProvider` (always available, last resort)
- `MarketDataService` orchestrator with provider priority ordering
- 60-second price caching to prevent redundant API calls
- Graceful fallback on rate limits and provider failures
- Provider-specific exception handling (`RateLimitError`, `ProviderUnavailableError`)

### Changed
- `PriceService` now uses `MarketDataService` instead of direct `YFinanceAdapter`
- Provider priority: Finnhub → Twelve Data → Alpha Vantage → Yahoo Finance
- Updated configuration with API key support for all providers
- Improved error handling with clean fallback chain

### Technical
- New models: `PriceQuote`, market data exceptions
- New services: `MarketDataService`, `market_data_factory`
- New adapters: `providers/` directory with 4 provider implementations
- 56 tests passing (15 new fallback tests + updated existing tests)
- Demo script: `test_fallback_demo.py` for testing without API calls

---

## [0.2.0] - 2026-01-24

### Added
- Twilio SMS adapter for notifications
- Apple Messages adapter (macOS local fallback via AppleScript)
- Email-to-SMS adapter via carrier gateways
- Automatic notification channel selection (AUTO mode)
- Fallback chain: Twilio → Apple Messages → Console
- `ENABLE_TWILIO` configuration flag
- `NOTIFICATION_CHANNEL=auto` option

### Changed
- Notification service now supports multiple channels with fallback
- Updated `.env.example` with new Twilio and messaging options
- Improved phone number normalization (strips country code for US)

### Technical
- New adapters: `sms_adapter.py`, `apple_messages_adapter.py`, `email_sms_adapter.py`
- Added `twilio` dependency
- 46 tests passing (41 core + 5 notification channel tests)

---

## [0.1.0] - 2026-01-24

### Added
- Core stock price tracking via yfinance
- Threshold-based alert detection
- LLM-powered explanations via Ollama
- News headline fetching via Google News RSS
- SQLite storage for price history and execution logs
- Console notification output
- Email notification support via SMTP
- CLI interface with commands: check, test, status
- Comprehensive unit test suite
- Integration test suite
- Full documentation in .cursor/

### Technical
- Pydantic models for data validation
- pydantic-settings for configuration
- Adapter pattern for external services
- Service layer for business logic
- Type hints throughout codebase
- Black formatting, mypy type checking, ruff linting

---

## [0.0.1] - 2026-01-24

### Added
- Control skeleton initialized
- `.cursor/rules/` with standards, security, and workflow rules
- `.cursor/` control documents (instructions, architecture, roadmap)
- Root documentation (PRD.md, README.md)
- `.cursorignore` configuration
