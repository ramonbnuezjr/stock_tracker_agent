# Project Instructions

## Overview

**Stock Tracker** is a Python application for tracking stock prices and portfolio performance. The application prioritizes simplicity, correctness, and local-first execution.

---

## Supported Features

- Fetch current stock prices by ticker symbol
- Retrieve historical price data
- Track portfolio holdings and performance
- Calculate gains/losses
- Export data in standard formats (CSV, JSON)

---

## Explicit Non-Goals

The following are **out of scope** for this project:

- Real-time trading or order execution
- Financial advice or recommendations
- User authentication or multi-tenancy
- Mobile applications
- Cloud deployment (local-first priority)
- Machine learning predictions
- Social features or sharing

---

## Key Dependencies

| Dependency | Purpose |
|------------|---------|
| `yfinance` | Stock data retrieval |
| `pydantic` | Data validation and settings |
| `pytest` | Testing framework |
| `pytest-cov` | Coverage reporting |
| `black` | Code formatting |
| `mypy` | Static type checking |
| `ruff` | Linting |

---

## Cursor Behavior Guidelines

### Do
- Follow all rules in `.cursor/rules/`
- Reference `architecture.md` for component placement
- Check `roadmap.md` before implementing features
- Write tests before implementation (TDD)
- Update documentation for meaningful changes
- Ask clarifying questions when requirements are ambiguous

### Don't
- Generate code that violates security rules
- Skip type hints or docstrings
- Implement features outside the roadmap without discussion
- Create cloud-dependent functionality
- Add dependencies without explicit approval
- Generate placeholder or stub implementations

### When Uncertain
1. State the uncertainty clearly
2. Propose options with trade-offs
3. Wait for clarification before proceeding

---

## File Organization

```
stock_tracker/
├── .cursor/           # Cursor configuration and docs
├── src/               # Source code
│   ├── __init__.py
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── utils/         # Utilities
├── tests/             # Test files
│   ├── __init__.py
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── requirements.txt   # Dependencies
├── pyproject.toml     # Project configuration
└── README.md          # User documentation
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `CACHE_TTL` | No | Cache time-to-live in seconds |
| `DATA_DIR` | No | Directory for local data storage |

---

## Quick Reference

- **Run tests**: `pytest`
- **Format code**: `black src tests`
- **Type check**: `mypy src`
- **Lint**: `ruff check src tests`
