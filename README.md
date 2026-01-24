# Stock Tracker

A simple command-line tool for tracking stock prices and portfolio performance.

## Requirements

- Python 3.10 or higher
- pip (Python package manager)

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python -m src.main
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

Run tests with coverage enforcement:
```bash
pytest --cov=src --cov-fail-under=90
```

## Code Quality

Format code:
```bash
black src tests
```

Type checking:
```bash
mypy src
```

Linting:
```bash
ruff check src tests
```

Run all checks:
```bash
black --check src tests && mypy src && ruff check src tests && pytest --cov=src
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `CACHE_TTL` | No | `300` | Cache time-to-live in seconds |
| `DATA_DIR` | No | `./data` | Directory for local data storage |

Create a `.env` file in the project root to set these:
```
LOG_LEVEL=DEBUG
CACHE_TTL=600
DATA_DIR=/path/to/data
```

## Project Structure

```
stock_tracker/
├── .cursor/           # Cursor AI configuration
├── src/               # Source code
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── tests/             # Test files
├── data/              # Local data storage (gitignored)
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## License

Private use only.
