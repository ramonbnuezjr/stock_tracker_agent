# Project Roadmap

## Version Overview

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | ✅ Complete | MVP — Core functionality |
| v0.2 | ✅ Complete | SMS & Messaging channels |
| v0.3 | ✅ Complete | Multi-provider market data |
| v0.4 | ✅ Complete | macOS service setup |
| v1.0 | 📋 Planned | Production-ready release |

---

## v0.1 — MVP ✅

**Goal**: Minimal working product with stock monitoring and LLM explanations.

### Features
- [x] Fetch current stock price by symbol
- [x] Detect price changes exceeding threshold
- [x] Fetch news headlines for context
- [x] Generate LLM explanations via Ollama
- [x] Local caching with SQLite
- [x] Console notification output
- [x] Email notification support
- [x] CLI interface (check, test, status)

### Technical Requirements
- [x] Project structure established
- [x] Core models defined (Stock, PricePoint, PriceChange, Alert)
- [x] Data provider abstraction (yfinance adapter)
- [x] News provider abstraction (RSS adapter)
- [x] LLM abstraction (Ollama adapter)
- [x] Storage abstraction (SQLite adapter)
- [x] Unit tests for all components
- [x] Integration tests for full flow
- [x] Documentation complete

### Definition of Done
- User can track any valid stock symbol
- Threshold breaches trigger explanations
- Results are persisted locally
- Invalid symbols return clear errors
- Test coverage ≥90% for services

---

## v0.2 — SMS & Messaging ✅

**Goal**: Add SMS notifications with multiple channel support.

### Features
- [x] SMS notifications via Twilio
- [x] Apple Messages fallback (macOS)
- [x] Email-to-SMS via carrier gateways
- [x] Automatic channel selection (AUTO mode)
- [x] Fallback chain: Twilio → Apple Messages → Console
- [ ] Batch multiple alerts into single notification (deferred to v1.0)

### Technical Requirements
- [x] Twilio adapter implementation
- [x] Apple Messages adapter (AppleScript)
- [x] Email-to-SMS adapter (MMS gateways)
- [x] Notification service fallback logic
- [x] Phone number normalization
- [ ] A2P 10DLC registration (deferred — personal use only)

### Definition of Done
- [x] SMS notifications work via Apple Messages
- [x] Twilio adapter ready (pending A2P registration)
- [x] Fallback chain operational
- [x] All tests passing (46 tests)

---

## v0.3 — Multi-Provider Market Data ✅

**Goal**: Professional-grade market data reliability with graceful fallback.

### Features
- [x] Multi-provider market data strategy
- [x] Automatic fallback on rate limits and failures
- [x] Four provider support: Finnhub, Twelve Data, Alpha Vantage, Yahoo Finance
- [x] 60-second price caching
- [x] Provider priority ordering
- [x] Clean error handling

### Technical Requirements
- [x] `PriceQuote` normalized model
- [x] `MarketDataProvider` Protocol interface
- [x] Four provider adapters (thin, no retries, no fallback logic)
- [x] `MarketDataService` orchestrator
- [x] Exception hierarchy (RateLimitError, ProviderUnavailableError)
- [x] Integration with existing PriceService
- [x] Comprehensive test suite (15 new tests)

### Definition of Done
- [x] Fallback occurs when primary provider rate-limits
- [x] Secondary provider used correctly
- [x] Cache prevents redundant API calls
- [x] Failure is clean if all providers unavailable
- [x] Provider-specific errors don't leak upward
- [x] All tests passing (56 tests)

---

## v1.0 — Production Ready

**Goal**: Stable, well-documented, ready for general use.

### Features
- [ ] Multiple notification channels simultaneously
- [ ] Historical price chart generation
- [ ] Configurable alert cooldown
- [ ] Alert digest mode (daily summary)
- [ ] Source citation in explanations
- [ ] Comprehensive help system

### Technical Requirements
- [ ] Full test coverage maintained
- [ ] Security audit complete
- [ ] Performance optimized (<30s total)
- [ ] Installation documented (pip, brew)
- [ ] Changelog complete
- [ ] Man page or rich --help

### Definition of Done
- Application is stable and reliable
- Documentation covers all use cases
- No security vulnerabilities
- Easy to install and configure

---

## Out of Scope

The following will NOT be implemented:

- Real-time streaming data
- Trading functionality
- Cloud deployment
- Web interface
- Mobile apps
- User accounts
- Financial advice features
- Price prediction

---

## Scope Change Process

To add features not in this roadmap:

1. Document the proposed feature
2. Assess impact on existing roadmap
3. Update this document before implementation
4. Ensure alignment with project goals (PRD.md)

Cursor must verify roadmap alignment before implementing new features.
