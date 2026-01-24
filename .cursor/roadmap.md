# Project Roadmap

## Version Overview

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | 🚧 In Progress | MVP — Core functionality |
| v0.2 | 📋 Planned | Hardening and polish |
| v1.0 | 📋 Planned | Production-ready release |

---

## v0.1 — MVP

**Goal**: Minimal working product with core stock tracking functionality.

### Features
- [ ] Fetch current stock price by symbol
- [ ] Fetch historical prices (date range)
- [ ] Basic error handling for invalid symbols
- [ ] Local caching to reduce API calls
- [ ] CLI interface for basic operations

### Technical Requirements
- [ ] Project structure established
- [ ] Core models defined (Stock, Price)
- [ ] Data provider abstraction
- [ ] Unit tests for all components
- [ ] Basic documentation

### Definition of Done
- User can query any valid stock symbol
- Results are cached locally
- Invalid symbols return clear error messages
- Test coverage ≥90%

---

## v0.2 — Hardening

**Goal**: Improve reliability, usability, and code quality.

### Features
- [ ] Portfolio tracking (add/remove holdings)
- [ ] Calculate portfolio value
- [ ] Calculate gains/losses
- [ ] Export portfolio to CSV
- [ ] Configuration file support

### Technical Requirements
- [ ] Integration tests added
- [ ] Error messages improved
- [ ] Performance profiling
- [ ] Dependency audit
- [ ] Documentation expanded

### Definition of Done
- Users can track a portfolio
- Exports work reliably
- No known bugs
- All code documented

---

## v1.0 — Production Ready

**Goal**: Stable, well-documented, ready for general use.

### Features
- [ ] Historical portfolio tracking
- [ ] Dividend tracking
- [ ] Multiple export formats (JSON, CSV)
- [ ] Configurable cache TTL
- [ ] Comprehensive help system

### Technical Requirements
- [ ] Full test coverage
- [ ] Security audit complete
- [ ] Performance optimized
- [ ] Installation documented
- [ ] Changelog complete

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

---

## Scope Change Process

To add features not in this roadmap:

1. Document the proposed feature
2. Assess impact on existing roadmap
3. Update this document before implementation
4. Ensure alignment with project goals

Cursor must verify roadmap alignment before implementing new features.
