"""Explanation service for generating LLM-powered stock movement explanations."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import List

from src.adapters.llama_cpp_adapter import LlamaCppAdapter, LlamaCppError
from src.models.alert import Explanation
from src.models.stock import PriceChange

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a financial news analyst. Your job is to explain \
stock price movements in plain, factual language.

Rules:
- Write 2-3 sentences maximum
- Be factual and objective
- Do not speculate or predict future prices
- Do not give investment advice
- If news is available, connect the price movement to relevant headlines
- If no clear reason is apparent, say so honestly
- Use simple language a non-expert can understand"""


USER_PROMPT_TEMPLATE = """Explain why {symbol} stock moved {direction} \
{change_percent:.2f}% (from ${previous_price:.2f} to ${current_price:.2f}).

Recent news headlines:
{headlines}

Provide a brief, factual explanation in 2-3 sentences."""


class ExplanationService:
    """Service for generating LLM-powered explanations of price movements.

    Uses Phi-3 Mini (or other GGUF) via llama-cpp-python in-process.

    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context window size.
        n_gpu_layers: GPU layers (-1 for Metal on Mac).

    Returns:
        An ExplanationService instance.
    """

    def __init__(
        self,
        model_path: str | None = None,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
    ) -> None:
        """Initialize the explanation service.

        Args:
            model_path: Path to the GGUF file (required for generation).
            n_ctx: Context size.
            n_gpu_layers: GPU layers (-1 for all on Metal).
        """
        self.model_path = model_path or ""
        self.model_label = self.model_path or "llama.cpp"
        self.adapter = LlamaCppAdapter(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
        )

    def generate_explanation(
        self,
        price_change: PriceChange,
        headlines: List[str],
    ) -> Explanation:
        """Generate an explanation for a price movement.

        Args:
            price_change: The price change to explain.
            headlines: Recent news headlines for context.

        Returns:
            An Explanation object with the generated text.
        """
        # Format headlines
        if headlines:
            headlines_text = "\n".join(f"- {h}" for h in headlines)
        else:
            headlines_text = "No recent news headlines available."

        # Build prompt
        direction = "up" if price_change.change_percent > 0 else "down"
        prompt = USER_PROMPT_TEMPLATE.format(
            symbol=price_change.symbol,
            direction=direction,
            change_percent=abs(price_change.change_percent),
            previous_price=price_change.previous_price,
            current_price=price_change.current_price,
            headlines=headlines_text,
        )

        logger.info(
            "Generating explanation for %s (%s%.2f%%)",
            price_change.symbol,
            "+" if price_change.change_percent > 0 else "",
            price_change.change_percent,
        )

        try:
            text = self.adapter.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=256,
            )

            return Explanation(
                text=text,
                news_headlines=headlines,
                model=self.model_label,
                generated_at=datetime.utcnow(),
            )

        except LlamaCppError as e:
            logger.error("Failed to generate explanation: %s", e)
            # Return a fallback explanation
            return self._fallback_explanation(price_change, headlines)

    def _fallback_explanation(
        self,
        price_change: PriceChange,
        headlines: List[str],
    ) -> Explanation:
        """Generate a fallback explanation when LLM is unavailable.

        Args:
            price_change: The price change to explain.
            headlines: Recent news headlines.

        Returns:
            A basic Explanation object.
        """
        direction = "increased" if price_change.change_percent > 0 else "decreased"

        if headlines:
            text = (
                f"{price_change.symbol} {direction} by "
                f"{abs(price_change.change_percent):.2f}%. "
                f"Recent headline: \"{headlines[0]}\""
            )
        else:
            text = (
                f"{price_change.symbol} {direction} by "
                f"{abs(price_change.change_percent):.2f}%. "
                "No specific news was found to explain this movement."
            )

        return Explanation(
            text=text,
            news_headlines=headlines,
            model="fallback",
            generated_at=datetime.utcnow(),
        )

    def is_available(self) -> bool:
        """Check if the LLM is available for generating explanations.

        Returns:
            True if the model path exists and llama-cpp-python is installed.
        """
        return self.adapter.is_available()

    def explain_from_values(
        self,
        symbol: str,
        previous_price: Decimal,
        current_price: Decimal,
        headlines: List[str],
    ) -> Explanation:
        """Generate explanation from raw values.

        Args:
            symbol: The stock ticker symbol.
            previous_price: The previous price.
            current_price: The current price.
            headlines: Recent news headlines.

        Returns:
            An Explanation object.
        """
        change_amount = current_price - previous_price
        change_percent = (change_amount / previous_price) * 100

        price_change = PriceChange(
            symbol=symbol,
            previous_price=previous_price,
            current_price=current_price,
            change_amount=change_amount,
            change_percent=change_percent,
        )

        return self.generate_explanation(price_change, headlines)
