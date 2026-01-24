# Product Requirements Document

## Problem Statement

Individual investors need a simple, local tool to track stock prices and monitor portfolio performance without relying on complex web applications, subscriptions, or cloud services.

---

## Core User Flow

```
1. User runs the application
2. User queries a stock symbol (e.g., "AAPL")
3. Application fetches and displays current price
4. User can add stocks to portfolio
5. User views portfolio summary with gains/losses
6. User exports data for personal records
```

---

## Target User

- Individual investor
- Comfortable with command-line tools
- Values privacy and local data storage
- Wants simplicity over features

---

## Explicit Non-Goals

- **Not a trading platform** — No buy/sell execution
- **Not financial advice** — No recommendations or predictions
- **Not a web app** — CLI only, no browser interface
- **Not multi-user** — Single user, local machine
- **Not real-time** — Delayed quotes are acceptable
- **Not cloud-based** — All data stored locally

---

## Success Criteria

### MVP (v0.1)
- User can fetch price for any valid stock symbol
- Response time < 3 seconds for cached data
- Clear error messages for invalid symbols
- Works offline with cached data

### Production (v1.0)
- User can track portfolio of multiple stocks
- User can view gains/losses over time
- User can export data to CSV/JSON
- Application is stable with no critical bugs
- Documentation enables self-service setup

---

## Constraints

- Python 3.10+ required
- No paid APIs or subscriptions
- No internet required for cached operations
- Single-threaded execution acceptable

---

## Dependencies

- `yfinance` for stock data (free, no API key)
- Standard Python libraries for core functionality
