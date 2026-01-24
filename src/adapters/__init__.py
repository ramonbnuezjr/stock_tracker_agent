"""Infrastructure adapters for external services."""

from src.adapters.yfinance_adapter import YFinanceAdapter
from src.adapters.news_adapter import NewsAdapter
from src.adapters.ollama_adapter import OllamaAdapter
from src.adapters.email_adapter import EmailAdapter
from src.adapters.storage_adapter import StorageAdapter

__all__ = [
    "YFinanceAdapter",
    "NewsAdapter",
    "OllamaAdapter",
    "EmailAdapter",
    "StorageAdapter",
]
