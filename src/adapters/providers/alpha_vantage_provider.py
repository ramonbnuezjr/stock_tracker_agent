"""Alpha Vantage provider adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import requests

from src.adapters.market_data_exceptions import (
    ProviderUnavailableError,
    RateLimitError,
)
from src.models.market_data import PriceQuote

logger = logging.getLogger(__name__)


class AlphaVantageProvider:
    """Alpha Vantage market data provider.

    Args:
        api_key: Alpha Vantage API key.

    Returns:
        An AlphaVantageProvider instance.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the Alpha Vantage provider.

        Args:
            api_key: Alpha Vantage API key.
        """
        self.provider_name = "alpha_vantage"
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Fetch the latest price from Alpha Vantage.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            RateLimitError: If Alpha Vantage rate limits the request.
            ProviderUnavailableError: If Alpha Vantage is unavailable.
        """
        if not self.api_key:
            raise ProviderUnavailableError(
                self.provider_name,
                "API key not configured",
            )

        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key,
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10,
            )

            # Check for rate limiting
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError(
                    self.provider_name,
                    "API call frequency limit exceeded",
                )

            if response.status_code != HTTPStatus.OK:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"HTTP {response.status_code}",
                )

            data = response.json()

            # Check for API error messages
            if "Error Message" in data:
                raise ProviderUnavailableError(
                    self.provider_name,
                    data["Error Message"],
                )

            if "Note" in data:
                # Rate limit message
                raise RateLimitError(
                    self.provider_name,
                    data["Note"],
                )

            quote = data.get("Global Quote", {})
            if not quote:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"No data for {symbol}",
                )

            price_str = quote.get("05. price")
            if not price_str:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"No price data for {symbol}",
                )

            price = Decimal(price_str)

            logger.debug(
                "Alpha Vantage: %s = %s",
                symbol,
                price,
            )

            return PriceQuote(
                symbol=symbol.upper(),
                price=price,
                timestamp=datetime.utcnow(),
                provider_name=self.provider_name,
            )

        except RateLimitError:
            raise
        except ProviderUnavailableError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "Alpha Vantage request error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
        except Exception as e:
            logger.error(
                "Alpha Vantage error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
