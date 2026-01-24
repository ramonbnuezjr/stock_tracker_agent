"""Unit tests for explanation service."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.ollama_adapter import OllamaError
from src.models.stock import PriceChange
from src.services.explanation_service import ExplanationService


class TestExplanationService:
    """Tests for the ExplanationService."""

    @pytest.fixture
    def price_change(self) -> PriceChange:
        """Create a sample price change."""
        return PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            change_amount=Decimal("5.00"),
            change_percent=Decimal("5.00"),
            previous_timestamp=datetime(2026, 1, 23),
            current_timestamp=datetime(2026, 1, 24),
        )

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_generate_explanation(
        self,
        mock_adapter_class: MagicMock,
        price_change: PriceChange,
    ) -> None:
        """Test generating an explanation."""
        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = (
            "Apple stock rose 5% following strong earnings."
        )
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService(model="test-model")
        explanation = service.generate_explanation(
            price_change,
            headlines=["Apple beats earnings estimates"],
        )

        assert "Apple stock rose" in explanation.text
        assert explanation.model == "test-model"
        assert len(explanation.news_headlines) == 1

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_generate_explanation_no_headlines(
        self,
        mock_adapter_class: MagicMock,
        price_change: PriceChange,
    ) -> None:
        """Test explanation generation with no headlines."""
        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = (
            "The stock moved without clear news catalyst."
        )
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        explanation = service.generate_explanation(price_change, headlines=[])

        assert explanation.news_headlines == []
        mock_adapter.generate.assert_called_once()
        # Check that prompt mentions no headlines
        call_kwargs = mock_adapter.generate.call_args
        assert "No recent news" in call_kwargs.kwargs.get(
            "prompt", call_kwargs.args[0] if call_kwargs.args else ""
        )

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_generate_explanation_llm_error_fallback(
        self,
        mock_adapter_class: MagicMock,
        price_change: PriceChange,
    ) -> None:
        """Test fallback explanation when LLM fails."""
        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = OllamaError("Connection refused")
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        explanation = service.generate_explanation(
            price_change,
            headlines=["Apple announces new iPhone"],
        )

        # Should get fallback explanation
        assert explanation.model == "fallback"
        assert "AAPL" in explanation.text
        assert "5.00%" in explanation.text

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_fallback_explanation_with_headlines(
        self,
        mock_adapter_class: MagicMock,
        price_change: PriceChange,
    ) -> None:
        """Test fallback includes first headline."""
        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = OllamaError("Error")
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        explanation = service.generate_explanation(
            price_change,
            headlines=["Apple announces new iPhone", "Tech stocks rally"],
        )

        assert "Apple announces new iPhone" in explanation.text

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_fallback_explanation_no_headlines(
        self,
        mock_adapter_class: MagicMock,
        price_change: PriceChange,
    ) -> None:
        """Test fallback with no headlines."""
        mock_adapter = MagicMock()
        mock_adapter.generate.side_effect = OllamaError("Error")
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        explanation = service.generate_explanation(price_change, headlines=[])

        assert "No specific news" in explanation.text

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_is_available(self, mock_adapter_class: MagicMock) -> None:
        """Test checking LLM availability."""
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        assert service.is_available() is True

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_explain_from_values(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test explanation from raw values."""
        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = "Stock increased due to news."
        mock_adapter_class.return_value = mock_adapter

        service = ExplanationService()
        explanation = service.explain_from_values(
            symbol="NVDA",
            previous_price=Decimal("200.00"),
            current_price=Decimal("220.00"),
            headlines=["NVIDIA announces new GPU"],
        )

        assert "Stock increased" in explanation.text

    @patch("src.services.explanation_service.OllamaAdapter")
    def test_negative_change_direction(
        self,
        mock_adapter_class: MagicMock,
    ) -> None:
        """Test explanation for negative price change."""
        mock_adapter = MagicMock()
        mock_adapter.generate.return_value = "Stock fell due to earnings miss."
        mock_adapter_class.return_value = mock_adapter

        price_change = PriceChange(
            symbol="AAPL",
            previous_price=Decimal("100.00"),
            current_price=Decimal("95.00"),
            change_amount=Decimal("-5.00"),
            change_percent=Decimal("-5.00"),
        )

        service = ExplanationService()
        service.generate_explanation(price_change, headlines=[])

        # Check that prompt uses "down" direction
        call_args = mock_adapter.generate.call_args
        prompt = call_args.kwargs.get(
            "prompt", call_args.args[0] if call_args.args else ""
        )
        assert "down" in prompt
