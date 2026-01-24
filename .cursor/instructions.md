# Project Instructions

## Overview

**Stock Tracker** is a local-first Python agent that monitors stock prices, detects meaningful movements, and generates LLM-powered explanations. It runs periodically via cron/launchd, sends notifications, and exits.

---

## Supported Features

- Fetch current stock prices by ticker symbol
- Detect price changes exceeding configurable thresholds
- Generate natural-language explanations using local LLM (Ollama)
- Send notifications via console or email
- Persist price history and execution metadata (SQLite)

---

## Explicit Non-Goals

The following are **out of scope** for this project:

- Real-time trading or order execution
- Financial advice or recommendations
- Price prediction or machine learning
- User authentication or multi-tenancy
- Web interface or mobile applications
- Cloud deployment (local-first priority)
- Portfolio optimization

---

## Key Dependencies

| Dependency | Purpose |
|------------|---------|
| `yfinance` | Stock data retrieval |
| `pydantic` | Data validation and models |
| `pydantic-settings` | Environment configuration |
| `ollama` | Local LLM integration |
| `feedparser` | RSS news fetching |
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
- Use fallbacks for external service failures
- Ask clarifying questions when requirements are ambiguous

### Don't

- Generate code that violates security rules
- Skip type hints or docstrings
- Implement features outside the roadmap without discussion
- Create cloud-dependent functionality
- Add dependencies without explicit approval
- Generate placeholder or stub implementations
- Use eval(), exec(), or pickle

### When Uncertain

1. State the uncertainty clearly
2. Propose options with trade-offs
3. Wait for clarification before proceeding

---

## File Organization

```
stock_tracker/
├── .cursor/           # Cursor configuration and docs
│   ├── rules/         # Coding standards and constraints
│   ├── instructions.md
│   ├── architecture.md
│   └── roadmap.md
├── src/               # Source code
│   ├── __init__.py
│   ├── main.py        # CLI entry point
│   ├── config.py      # Settings via pydantic-settings
│   ├── models/        # Pydantic data models
│   ├── services/      # Business logic
│   └── adapters/      # External service integrations
├── tests/             # Test files
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── data/              # Local data storage (gitignored)
├── requirements.txt   # Dependencies
├── pyproject.toml     # Project configuration
└── README.md          # User documentation
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STOCK_SYMBOLS` | No | `AAPL,NVDA,MSFT` | Comma-separated stock symbols |
| `PRICE_THRESHOLD` | No | `1.5` | Alert threshold (percentage) |
| `NOTIFICATION_CHANNEL` | No | `console` | `console`, `email`, or `sms` |
| `SMTP_HOST` | For email | - | SMTP server hostname |
| `SMTP_PORT` | For email | `587` | SMTP server port |
| `SMTP_USER` | For email | - | SMTP username |
| `SMTP_PASSWORD` | For email | - | SMTP password |
| `NOTIFY_EMAIL` | For email | - | Recipient email |
| `OLLAMA_MODEL` | No | `mistral:7b` | LLM model name |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama API URL |
| `DATA_DIR` | No | `./data` | Local storage directory |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

---

## Quick Reference

```bash
# Run a price check
python -m src.main check

# Send test notification
python -m src.main test

# Show configuration status
python -m src.main status

# Run with verbose logging
python -m src.main check -v

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Format code
black src tests

# Type check
mypy src

# Lint
ruff check src tests
```

---

## LLM Integration

The application uses Ollama for local LLM inference:

1. **Install Ollama**: https://ollama.ai
2. **Pull a model**: `ollama pull mistral:7b`
3. **Start server**: `ollama serve`

Supported models (8GB RAM compatible):
- `mistral:7b` (recommended)
- `llama3.2:3b` (smaller, faster)

If Ollama is unavailable, a fallback explanation is generated.

---

## Cron Setup Example

```bash
# Run every 30 minutes during market hours (9am-4pm ET, Mon-Fri)
*/30 9-16 * * 1-5 cd /path/to/stock_tracker && /path/to/venv/bin/python -m src.main check
```
