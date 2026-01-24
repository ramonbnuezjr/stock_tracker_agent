# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

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
