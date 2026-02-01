"""Infrastructure adapters for external services."""

from src.adapters.yfinance_adapter import YFinanceAdapter
from src.adapters.news_adapter import NewsAdapter
from src.adapters.llama_cpp_adapter import LlamaCppAdapter
from src.adapters.email_adapter import EmailAdapter
from src.adapters.email_sms_adapter import EmailSMSAdapter
from src.adapters.sms_adapter import SMSAdapter
from src.adapters.apple_messages_adapter import AppleMessagesAdapter
from src.adapters.storage_adapter import StorageAdapter

__all__ = [
    "YFinanceAdapter",
    "NewsAdapter",
    "LlamaCppAdapter",
    "EmailAdapter",
    "EmailSMSAdapter",
    "SMSAdapter",
    "AppleMessagesAdapter",
    "StorageAdapter",
]
