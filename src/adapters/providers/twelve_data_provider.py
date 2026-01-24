"""Twelve Data provider adapter."""

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


class TwelveDataProvider:
    """Twelve Data market data provider.

    Args:
        api_key: Twelve Data API key.

    Returns:
        A TwelveDataProvider instance.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the Twelve Data provider.

        Args:
            api_key: Twelve Data API key.
        """
        self.provider_name = "twelve_data"
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com/price"

    def get_latest_price(self, symbol: str) -> PriceQuote:
        """Fetch the latest price from Twelve Data.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A PriceQuote with normalized price data.

        Raises:
            RateLimitError: If Twelve Data rate limits the request.
            ProviderUnavailableError: If Twelve Data is unavailable.
        """
        if not self.api_key:
            raise ProviderUnavailableError(
                self.provider_name,
                "API key not configured",
            )

        try:
            params = {
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

            # Check for error in response
            if "status" in data and data["status"] == "error":
                error_msg = data.get("message", "Unknown error")
                if "limit" in error_msg.lower() or "quota" in error_msg.lower():
                    raise RateLimitError(
                        self.provider_name,
                        error_msg,
                    )
                raise ProviderUnavailableError(
                    self.provider_name,
                    error_msg,
                )

            price_str = data.get("price")
            if not price_str:
                raise ProviderUnavailableError(
                    self.provider_name,
                    f"No price data for {symbol}",
                )

            price = Decimal(price_str)

            logger.debug(
                "Twelve Data: %s = %s",
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
                "Twelve Data request error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
        except Exception as e:
            logger.error(
                "Twelve Data error for %s: %s",
                symbol,
                e,
            )
            raise ProviderUnavailableError(
                self.provider_name,
                str(e),
            )
