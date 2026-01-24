"""Integration tests for end-to-end flow."""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import NotificationChannel, Settings
from src.models.alert import Alert, Explanation
from src.models.stock import PriceChange, PricePoint
from src.services.explanation_service import ExplanationService
from src.services.news_service import NewsService
from src.services.notification_service import NotificationService
from src.services.price_service import PriceService


class TestEndToEndFlow:
    """Integration tests for the complete application flow."""

    @pytest.fixture
    def temp_data_dir(self) -> Path:
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def settings(self, temp_data_dir: Path) -> Settings:
        """Create test settings."""
        return Settings(
            stock_symbols="AAPL,NVDA",
            price_threshold=Decimal("1.5"),
            notification_channel=NotificationChannel.CONSOLE,
            data_dir=temp_data_dir,
        )

    @patch("src.services.price_service.YFinanceAdapter")
    def test_full_flow_no_breach(
        self,
        mock_yfinance_class: MagicMock,
        settings: Settings,
    ) -> None:
        """Test full flow when no threshold is breached."""
        mock_yfinance = MagicMock()
        mock_yfinance_class.return_value = mock_yfinance

        # First run - store initial prices
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            ),
            "NVDA": PricePoint(
                symbol="NVDA",
                price=Decimal("200.00"),
                timestamp=datetime(2026, 1, 23),
            ),
        }

        price_service = PriceService(
            data_dir=settings.data_dir,
            threshold=settings.price_threshold,
        )

        # First run
        breaches = price_service.get_threshold_breaches(["AAPL", "NVDA"])
        assert len(breaches) == 0  # No previous prices

        # Second run - small change, no breach
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("100.50"),  # +0.5%
                timestamp=datetime(2026, 1, 24),
            ),
            "NVDA": PricePoint(
                symbol="NVDA",
                price=Decimal("201.00"),  # +0.5%
                timestamp=datetime(2026, 1, 24),
            ),
        }

        breaches = price_service.get_threshold_breaches(["AAPL", "NVDA"])
        assert len(breaches) == 0

    @patch("src.services.price_service.YFinanceAdapter")
    @patch("src.services.news_service.NewsAdapter")
    @patch("src.services.explanation_service.OllamaAdapter")
    def test_full_flow_with_breach(
        self,
        mock_ollama_class: MagicMock,
        mock_news_class: MagicMock,
        mock_yfinance_class: MagicMock,
        settings: Settings,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test full flow when threshold is breached."""
        # Setup mocks
        mock_yfinance = MagicMock()
        mock_yfinance_class.return_value = mock_yfinance

        mock_news = MagicMock()
        mock_news.get_headlines_text.return_value = [
            "Apple announces record earnings",
        ]
        mock_news_class.return_value = mock_news

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = (
            "Apple stock rose following strong Q4 earnings report."
        )
        mock_ollama_class.return_value = mock_ollama

        # Initialize services
        price_service = PriceService(
            data_dir=settings.data_dir,
            threshold=settings.price_threshold,
        )
        news_service = NewsService()
        explanation_service = ExplanationService()
        notification_service = NotificationService(settings)

        # First run - store initial prices
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            ),
        }
        price_service.get_threshold_breaches(["AAPL"])

        # Second run - large change, breach threshold
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("105.00"),  # +5%
                timestamp=datetime(2026, 1, 24),
            ),
        }

        breaches = price_service.get_threshold_breaches(["AAPL"])
        assert len(breaches) == 1
        assert breaches[0].symbol == "AAPL"
        assert breaches[0].threshold_exceeded is True

        # Get news and explanation
        headlines = news_service.get_headlines_text("AAPL")
        explanation = explanation_service.generate_explanation(
            breaches[0],
            headlines,
        )

        # Create and send alert
        alert = Alert(
            symbol=breaches[0].symbol,
            change_percent=breaches[0].change_percent,
            change_amount=breaches[0].change_amount,
            previous_price=breaches[0].previous_price,
            current_price=breaches[0].current_price,
            explanation=explanation,
        )

        success = notification_service.send_alert(alert)
        assert success is True

        # Verify console output
        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "5.00%" in captured.out

    @patch("src.services.price_service.YFinanceAdapter")
    def test_multiple_symbols_mixed_results(
        self,
        mock_yfinance_class: MagicMock,
        settings: Settings,
    ) -> None:
        """Test with multiple symbols, some breaching threshold."""
        mock_yfinance = MagicMock()
        mock_yfinance_class.return_value = mock_yfinance

        price_service = PriceService(
            data_dir=settings.data_dir,
            threshold=Decimal("2.0"),  # 2% threshold
        )

        # First run
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
            ),
            "NVDA": PricePoint(
                symbol="NVDA",
                price=Decimal("200.00"),
                timestamp=datetime(2026, 1, 23),
            ),
            "MSFT": PricePoint(
                symbol="MSFT",
                price=Decimal("300.00"),
                timestamp=datetime(2026, 1, 23),
            ),
        }
        price_service.get_threshold_breaches(["AAPL", "NVDA", "MSFT"])

        # Second run - mixed results
        mock_yfinance.get_prices.return_value = {
            "AAPL": PricePoint(
                symbol="AAPL",
                price=Decimal("103.00"),  # +3% - breach
                timestamp=datetime(2026, 1, 24),
            ),
            "NVDA": PricePoint(
                symbol="NVDA",
                price=Decimal("201.00"),  # +0.5% - no breach
                timestamp=datetime(2026, 1, 24),
            ),
            "MSFT": PricePoint(
                symbol="MSFT",
                price=Decimal("292.00"),  # -2.67% - breach
                timestamp=datetime(2026, 1, 24),
            ),
        }

        breaches = price_service.get_threshold_breaches(
            ["AAPL", "NVDA", "MSFT"]
        )

        assert len(breaches) == 2
        breach_symbols = {b.symbol for b in breaches}
        assert breach_symbols == {"AAPL", "MSFT"}

    def test_storage_persistence(self, settings: Settings) -> None:
        """Test that prices persist across service instances."""
        # Create first instance and store price
        with patch("src.services.price_service.YFinanceAdapter") as mock:
            mock_yfinance = MagicMock()
            mock_yfinance.get_prices.return_value = {
                "AAPL": PricePoint(
                    symbol="AAPL",
                    price=Decimal("100.00"),
                    timestamp=datetime(2026, 1, 23),
                ),
            }
            mock.return_value = mock_yfinance

            service1 = PriceService(data_dir=settings.data_dir)
            service1.get_price_changes(["AAPL"])

        # Create second instance and verify price is there
        with patch("src.services.price_service.YFinanceAdapter") as mock:
            mock_yfinance = MagicMock()
            mock_yfinance.get_prices.return_value = {
                "AAPL": PricePoint(
                    symbol="AAPL",
                    price=Decimal("105.00"),
                    timestamp=datetime(2026, 1, 24),
                ),
            }
            mock.return_value = mock_yfinance

            service2 = PriceService(data_dir=settings.data_dir)
            changes = service2.get_price_changes(["AAPL"])

            assert len(changes) == 1
            assert changes[0].previous_price == Decimal("100.00")
            assert changes[0].current_price == Decimal("105.00")
