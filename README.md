# Stock Tracker

A local-first stock monitoring agent that detects meaningful price movements and generates LLM-powered explanations.

## Features

- Monitor multiple stock symbols for price changes
- **Multi-provider market data** with automatic fallback (Finnhub, Twelve Data, Alpha Vantage, Yahoo Finance)
- Configurable percentage threshold for alerts
- LLM-generated explanations connecting price movements to news
- Multiple notification channels: Twilio SMS, Apple Messages, Email, Console
- Automatic fallback: Twilio → Apple Messages → Console
- SQLite storage for price history
- 60-second price caching to reduce API calls
- **Runs automatically on macOS** via launchd service
- Runs periodically via cron (no background service)
- **Security logging** for validation rejections and security violations

## Requirements

- Python 3.9 or higher
- macOS (for launchd service) or Linux (for cron)
- Phi-3 Mini (or other GGUF) via llama-cpp-python for LLM explanations
- 8GB RAM recommended (quantized Phi-3 Mini fits comfortably)
- Optional: API keys for market data providers (Finnhub, Twelve Data, Alpha Vantage)

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/ramonbnuezjr/stock_tracker_agent.git
cd stock_tracker_agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install LLM (Phi-3 Mini via llama-cpp-python)

```bash
# Install llama-cpp-python (CPU + Metal on Mac M2)
pip install -r requirements.txt

# On Mac M2 for GPU acceleration, reinstall with Metal:
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# Download Phi-3 Mini GGUF and set LLAMA_MODEL_PATH in .env (one-time):
./venv/bin/python scripts/download_phi3_mini.py
```

The download script fetches the Q4 quantized model (~2.2 GB) from Hugging Face to `./models/` and updates `.env`. Alternatively, download a GGUF manually and set `LLAMA_MODEL_PATH` in `.env`.

### 3. Configure

```bash
# Copy example config
cp .env.example .env

# Edit with your settings
nano .env
```

### 4. Install as macOS Service (Recommended)

```bash
# Install as launchd service (runs automatically)
./scripts/install_service.sh

# The service will run every 30 minutes during market hours
```

### 5. Manual Run (Alternative)

```bash
# Check stock prices and send alerts
python -m src.main check

# Show current configuration
python -m src.main status

# Send a test notification
python -m src.main test
```

## macOS Service Management

After installing the service:

```bash
# Check service status
launchctl list | grep com.ramonbnuezjr.stocktracker

# View logs
tail -f logs/stock_tracker.log

# Stop service
launchctl unload ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Start service
launchctl load ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Uninstall service
./scripts/uninstall_service.sh
```

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `STOCK_SYMBOLS` | `AAPL,NVDA,MSFT,...` | Comma-separated stock symbols (default: 15 tech/defense stocks) |
| `PRICE_THRESHOLD` | `1.5` | Alert threshold (percentage) |
| `NOTIFICATION_CHANNEL` | `auto` | `auto`, `sms`, `apple_messages`, `email`, `console` |
| `LLAMA_MODEL_PATH` | (required) | Path to GGUF model (e.g. Phi-3 Mini) |
| `LLAMA_N_CTX` | `2048` | Context window size |
| `LLAMA_N_GPU_LAYERS` | `-1` | GPU layers (-1 = Metal on Mac M2) |

### Market Data Providers (Multi-Provider Fallback)

The system automatically tries providers in priority order with fallback:

1. **Finnhub** (60 calls/min free) - `FINNHUB_API_KEY=`
2. **Twelve Data** (800 calls/day free) - `TWELVE_DATA_API_KEY=`
3. **Alpha Vantage** (25 calls/day free) - `ALPHA_VANTAGE_API_KEY=`
4. **Yahoo Finance** (always available, no key needed)

Only configure API keys for providers you want to use. Yahoo Finance works as final fallback.

### Notifications

For email notifications:

```bash
NOTIFICATION_CHANNEL=email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=recipient@email.com
```

For SMS (Twilio):

```bash
NOTIFICATION_CHANNEL=auto
ENABLE_TWILIO=true
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
NOTIFY_PHONE=+15551234567
```

For Apple Messages (macOS):

```bash
NOTIFICATION_CHANNEL=apple_messages
NOTIFY_PHONE=+15551234567
```

## Cron Setup (Alternative to launchd)

Run every 30 minutes during market hours:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
*/30 9-16 * * 1-5 cd /path/to/stock_tracker && /path/to/venv/bin/python -m src.main check >> /var/log/stock_tracker.log 2>&1
```

## Development

### Running from Cursor

**Important**: Cursor's sandbox blocks network access. To run smoke tests:

1. Use Cursor's **Integrated Terminal** (bottom panel)
2. Run commands directly: `./venv/bin/python -m src.main check`
3. This runs on your Mac with full network access

See `.cursor/sandbox_execution.md` for details on Cursor's sandbox limitations.

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific test file
pytest tests/test_threshold_detection.py -v
```

#### Test success and failure

**Success:** When all tests pass, pytest exits with code `0` and prints a line like `66 passed, 1 warning in X.XXs`. With coverage you also see a coverage summary.

**Failure scenarios:**

- **Assertion failure** — One or more tests fail. Pytest prints `FAILED` for each failing test, the file:line and traceback, then a short summary. Exit code is `1`. Example (from this project):

  ```
  tests/test_threshold_detection.py::TestThresholdDetection::test_threshold_exceeded_returns_true FAILED [ 14%]
  ...
  tests/test_threshold_detection.py:49: in test_threshold_exceeded_returns_true
      assert False
  E   assert False
  ...
  short test summary info
  FAILED tests/test_threshold_detection.py::TestThresholdDetection::test_threshold_exceeded_returns_true - assert False
  1 failed, 6 passed, 1 warning in 0.17s
  ```

- **Import or collection error** — A missing module, syntax error, or bad import in `conftest.py` or a test file causes pytest to fail during collection. No tests run; you see an `ImportError` or `ModuleNotFoundError` and exit code `2` (or similar).

- **Fixture or setup failure** — A fixture used by a test raises an exception. The test is reported as `FAILED` and the traceback points to the fixture or `conftest.py`, not the test body.

**How to see a failure:** Temporarily change an assertion in one test (e.g. in `tests/test_threshold_detection.py` add `assert False` at the start of a test), run `pytest tests/test_threshold_detection.py -v`, then revert the change.

#### Smoke tests (LLM and performance)

To run smoke tests that **include the model** (Phi-3 Mini via llama-cpp-python) and observe how your Mac Mini behaves:

1. Set `LLAMA_MODEL_PATH` in `.env` (or run `./venv/bin/python scripts/download_phi3_mini.py` once).
2. Open **Stats** (or another system monitor) and watch CPU and memory.
3. Run the LLM smoke test (generates explanations for **all monitored stocks** from `STOCK_SYMBOLS`):

   ```bash
   ./venv/bin/python scripts/smoke_test_llm.py
   ```

   The script loads the model on first use, then generates one explanation per symbol. You’ll see CPU/RAM spike during load and inference; later runs reuse the loaded model. To test iMessage: set NOTIFY_PHONE in .env and run ./venv/bin/python scripts/test_imessage_notification.py; ensure Messages is signed in on your Mac. Use this to confirm the Mac Mini’s behavior under the real LLM workload.

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
├── scripts/              # Setup and utility scripts (download_phi3_mini, smoke_test_llm, test_imessage_notification)
├── models/               # GGUF models (gitignored; created by download_phi3_mini.py)
├── .cursor/             # Project documentation
├── data/                # Local storage (gitignored)
└── logs/                # Application logs (gitignored)
```

## How It Works

1. **Price Check**: Fetches current prices via multi-provider system (Finnhub → Twelve Data → Alpha Vantage → Yahoo Finance)
2. **Caching**: 60-second cache prevents redundant API calls
3. **Threshold Detection**: Compares against previous price in SQLite
4. **If threshold breached** (>1.5% change):
   - **News Gathering**: Fetches recent headlines via Google News RSS
   - **Explanation**: Generates 2-3 sentence explanation via Phi-3 Mini / llama.cpp (like: "Nvidia down 1.89% due to geopolitical risks in China, a modest data center revenue miss...")
   - **Notification**: Sends alert via configured channel (with automatic fallback)
5. **Logging**: Saves execution metadata to SQLite

**Note**: Explanations only appear when price movements exceed the threshold. On the first run, prices are stored but no alerts are sent (no previous prices to compare). Subsequent runs will detect and explain meaningful movements.

## Example Output

### When Threshold Breach Detected:

```
============================================================
STOCK ALERT
============================================================
📉 NVDA is down -1.89% ($187.68 → $184.13)

Nvidia stock declined due to geopolitical risks in China,
a modest data center revenue miss, lofty valuation concerns,
and broader sentiment that the AI frenzy may be overheating.
============================================================
```

**SMS/Apple Messages Format:**
```
⬇️ NVDA down 1.89%
$187.68 → $184.13

Nvidia stock declined due to geopolitical risks in China,
a modest data center revenue miss, lofty valuation concerns,
and broader sentiment that the AI frenzy may be overheating.
```

### First Run (No Previous Prices):

On the first run, prices are fetched and stored, but no alerts are sent:

```
2026-01-24 15:39:17 [INFO] Price fetched for AAPL via finnhub: 248.05
2026-01-24 15:39:17 [INFO] No previous price for AAPL, storing current: 248.05
2026-01-24 15:39:17 [INFO] No threshold breaches detected
```

Subsequent runs will compare against stored prices and generate explanations when thresholds are exceeded.

## Security

### Input Validation

All stock symbols are validated to prevent command injection and other security threats:

- Valid symbols: `AAPL`, `NVDA`, `BRK.B`, `^NDXT`
- Rejected patterns: command injection (`;`, `|`, `&`), path traversal (`../`, `/`), shell operators

### Security Logging

Security violations are logged to `logs/security.log`:

- Validation rejections
- Command injection attempts
- Path traversal attempts
- All violations include sanitized input and context

View security logs:
```bash
tail -f logs/security.log
```

See `SECURITY_LOGGING.md` for detailed documentation.

## License

Private use only.
