# Stock Tracker

A local-first stock monitoring agent that detects meaningful price movements and generates LLM-powered explanations.

## Features

- Monitor multiple stock symbols for price changes
- Configurable percentage threshold for alerts
- LLM-generated explanations connecting price movements to news
- Console and email notifications
- SQLite storage for price history
- Runs periodically via cron (no background service)

## Requirements

- Python 3.10 or higher
- Ollama (for LLM explanations)
- 8GB RAM recommended

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/ramonbnuezjr/stock_tracker_agent.git
cd stock_tracker_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Ollama

```bash
# macOS
brew install ollama

# Or download from https://ollama.ai

# Pull a model
ollama pull mistral:7b

# Start the server
ollama serve
```

### 3. Configure (Optional)

```bash
# Copy example config
cp .env.example .env

# Edit with your settings
nano .env
```

### 4. Run

```bash
# Check stock prices and send alerts
python -m src.main check

# Show current configuration
python -m src.main status

# Send a test notification
python -m src.main test
```

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `STOCK_SYMBOLS` | `AAPL,NVDA,MSFT` | Comma-separated stock symbols |
| `PRICE_THRESHOLD` | `1.5` | Alert threshold (percentage) |
| `NOTIFICATION_CHANNEL` | `console` | `console` or `email` |
| `OLLAMA_MODEL` | `mistral:7b` | LLM model for explanations |

For email notifications:

```bash
NOTIFICATION_CHANNEL=email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=recipient@email.com
```

## Cron Setup

Run every 30 minutes during market hours:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
*/30 9-16 * * 1-5 cd /path/to/stock_tracker && /path/to/venv/bin/python -m src.main check >> /var/log/stock_tracker.log 2>&1
```

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific test file
pytest tests/unit/test_price_service.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Type checking
mypy src

# Linting
ruff check src tests

# All checks
black --check src tests && mypy src && ruff check src tests
```

## Project Structure

```
stock_tracker/
├── src/
│   ├── main.py          # CLI entry point
│   ├── config.py        # Configuration
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic
│   └── adapters/        # External integrations
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── .cursor/             # Project documentation
├── data/                # Local storage (gitignored)
└── requirements.txt     # Dependencies
```

## How It Works

1. **Price Check**: Fetches current prices via yfinance
2. **Threshold Detection**: Compares against previous price in SQLite
3. **News Gathering**: Fetches recent headlines via Google News RSS
4. **Explanation**: Generates 2-3 sentence explanation via Ollama
5. **Notification**: Sends alert via configured channel
6. **Logging**: Saves execution metadata to SQLite

## Example Output

```
============================================================
STOCK ALERT
============================================================
📈 AAPL is up +2.34% ($178.50 → $182.68)

Apple shares rose following the company's announcement of
record iPhone sales in Q4. Analysts cited strong demand
in emerging markets as a key driver.
============================================================
```

## License

Private use only.
