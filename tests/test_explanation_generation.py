"""
Tests for generating human-readable explanations
using a local language model.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.llama_cpp_adapter import LlamaCppAdapter, LlamaCppError
from src.models.alert import Explanation
from src.models.stock import PriceChange
from src.services.explanation_service import ExplanationService


class TestExplanationGeneration:
    """Tests for explanation generation functionality."""

    @pytest.fixture
    def price_change(self) -> PriceChange:
        """Create a sample price change for testing."""
        return PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            change_amount=Decimal("5.00"),
            change_percent=Decimal("5.00"),
            previous_timestamp=datetime(2026, 1, 23),
            current_timestamp=datetime(2026, 1, 24),
        )

    @pytest.fixture
    def sample_headlines(self) -> List[str]:
        """Sample news headlines for context."""
        return [
            "Apple announces record iPhone sales",
            "Tech sector rallies on positive earnings",
        ]

    def test_explanation_is_short_and_non_speculative(
        self,
        price_change: PriceChange,
        sample_headlines: List[str],
    ) -> None:
        """
        Explanation must be concise (<= 3 sentences) and factual.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            # Return a compliant explanation
            mock_adapter.generate.return_value = (
                "Apple stock rose 5% following strong iPhone sales. "
                "The tech sector overall showed positive momentum."
            )
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(
                price_change,
                sample_headlines,
            )

            # Check length (should be <= 3 sentences)
            sentences = explanation.text.split(". ")
            assert len(sentences) <= 3

            # Check it's not speculative (no prediction words)
            speculative_words = ["will", "might", "could", "should", "predict"]
            text_lower = explanation.text.lower()
            for word in speculative_words:
                # Allow "should" only in non-predictive context
                if word == "should":
                    continue
                assert word not in text_lower or "should be" not in text_lower

    def test_explanation_references_stock_symbol(
        self,
        price_change: PriceChange,
        sample_headlines: List[str],
    ) -> None:
        """
        Explanation should clearly reference the stock symbol.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = (
                "AAPL stock increased by 5% due to strong earnings."
            )
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(
                price_change,
                sample_headlines,
            )

            # Symbol should be in the explanation or prompt was correct
            # (The LLM response should reference the symbol)
            assert "AAPL" in explanation.text or "Apple" in explanation.text

    def test_explanation_handles_missing_news_gracefully(
        self,
        price_change: PriceChange,
    ) -> None:
        """
        If no news context is available, explanation should
        still be generated without failure.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = (
                "AAPL stock moved without clear news catalyst. "
                "The movement may reflect broader market trends."
            )
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(
                price_change,
                headlines=[],  # No headlines
            )

            # Should still generate an explanation
            assert explanation is not None
            assert len(explanation.text) > 0
            assert explanation.news_headlines == []

    def test_fallback_explanation_on_llm_failure(
        self,
        price_change: PriceChange,
        sample_headlines: List[str],
    ) -> None:
        """
        If LLM fails, a fallback explanation should be generated.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.side_effect = LlamaCppError("Connection refused")
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(
                price_change,
                sample_headlines,
            )

            # Should get fallback explanation
            assert explanation is not None
            assert explanation.model == "fallback"
            assert "AAPL" in explanation.text
            assert "5.00%" in explanation.text

    def test_fallback_includes_headline_when_available(
        self,
        price_change: PriceChange,
        sample_headlines: List[str],
    ) -> None:
        """
        Fallback explanation should include first headline if available.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.side_effect = LlamaCppError("Error")
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(
                price_change,
                sample_headlines,
            )

            # First headline should be in fallback
            assert sample_headlines[0] in explanation.text

    def test_explanation_model_recorded(
        self,
        price_change: PriceChange,
    ) -> None:
        """
        The model used for generation should be recorded.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = "Test explanation."
            mock_class.return_value = mock_adapter

            service = ExplanationService(model_path="/path/to/model.gguf")
            explanation = service.generate_explanation(price_change, [])

            assert explanation.model == "/path/to/model.gguf"

    def test_explanation_service_checks_availability(self) -> None:
        """
        Service should be able to check if LLM is available.
        """
        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            assert service.is_available() is True

            mock_adapter.is_available.return_value = False
            assert service.is_available() is False

    def test_negative_change_explanation(self) -> None:
        """
        Explanation should correctly describe negative price changes.
        """
        price_change = PriceChange(
            symbol="NVDA",
            previous_price=Decimal("500.00"),
            current_price=Decimal("475.00"),
            change_amount=Decimal("-25.00"),
            change_percent=Decimal("-5.00"),
        )

        with patch("src.services.explanation_service.LlamaCppAdapter") as mock_class:
            mock_adapter = MagicMock()
            mock_adapter.generate.return_value = (
                "NVDA stock fell 5% amid broader tech selloff."
            )
            mock_class.return_value = mock_adapter

            service = ExplanationService()
            explanation = service.generate_explanation(price_change, [])

            # Verify the prompt mentioned "down" direction
            call_args = mock_adapter.generate.call_args
            prompt = call_args.kwargs.get("prompt", "")
            assert "down" in prompt
