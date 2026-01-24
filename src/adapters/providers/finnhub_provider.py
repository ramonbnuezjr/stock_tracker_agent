"""Finnhub provider adapter."""

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


class FinnhubProvider:
    """Finnhub market data provider.

    Args:
        api_key: Finnhub API key.

    Returns:
        A FinnhubProvider instance.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the Finnhub provider.

        Args:
            api_key: Finnhub API key.
        """
        self.provider_name = "finnhub"
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1/quote"

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Fetch the latest price from Finnhub.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            RateLimitError: If Finnhub rate limits the request.
            ProviderUnavailableError: If Finnhub is unavailable.
        """
        if not self.api_key:
            raise ProviderUnavailableError(
                self.provider_name,
                "API key not configured",
            )

        try:
            params = {
                "symbol": symbol,
                "token": self.api_key,
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

            # Check for error in response
            if "error" in data:
                error_msg = data["error"]
                if "limit" in error_msg.lower():
                    raise RateLimitError(
                        self.provider_name,
                        error_msg,
                    )
                raise ProviderUnavailableError(
                    self.provider_name,
                    error_msg,
                )

            # Finnhub returns 'c' for current price
            price = data.get("c")
            if price is None:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"No price data for {symbol}",
                )

            price_decimal = Decimal(str(price))

            logger.debug(
                "Finnhub: %s = %s",
                symbol,
                price_decimal,
            )

            return PriceQuote(
                symbol=symbol.upper(),
                price=price_decimal,
                timestamp=datetime.utcnow(),
                provider_name=self.provider_name,
            )

        except RateLimitError:
            raise
        except ProviderUnavailableError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "Finnhub request error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
        except Exception as e:
            logger.error(
                "Finnhub error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
