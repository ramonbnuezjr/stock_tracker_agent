# Project Roadmap

## Version Overview

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | ✅ Complete | MVP — Core functionality |
| v0.2 | 📋 Planned | Hardening and polish |
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

## v0.2 — Hardening

**Goal**: Improve reliability, add SMS notifications, enhance UX.

### Features
- [ ] SMS notifications via Twilio
- [ ] Batch multiple alerts into single notification
- [ ] Configurable news sources
- [ ] Price history CLI command
- [ ] Clear execution logs command
- [ ] Configuration validation command

### Technical Requirements
- [ ] Twilio adapter implementation
- [ ] Retry logic for transient failures
- [ ] Rate limiting for external APIs
- [ ] Improved error messages
- [ ] Performance profiling
- [ ] Dependency security audit

### Definition of Done
- SMS notifications work reliably
- No API rate limit errors
- All error messages are actionable
- No known bugs

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
