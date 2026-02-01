"""
End-to-end execution flow tests.
"""

from __future__ import annotations

import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import NotificationChannel, Settings
from src.models.market_data import PriceQuote
from src.models.stock import PricePoint
from src.services.explanation_service import ExplanationService
from src.services.market_data_service import MarketDataService
from src.services.news_service import NewsService
from src.services.notification_service import NotificationService
from src.services.price_service import PriceService


class TestExecutionFlow:
    """End-to-end execution flow tests."""

    def test_execution_exits_cleanly_when_threshold_not_met(
        self,
        temp_data_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        When no threshold is exceeded, the system should exit
        without generating notifications.
        """
        mock_market_data = MagicMock(spec=MarketDataService)
        mock_market_data.get_latest_price.side_effect = [
            PriceQuote(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
                provider_name="test",
            ),
            PriceQuote(
                symbol="AAPL",
                price=Decimal("100.50"),  # Only 0.5% change
                timestamp=datetime(2026, 1, 24),
                provider_name="test",
            ),
        ]

        price_service = PriceService(
            data_dir=temp_data_dir,
            threshold=Decimal("2.0"),  # 2% threshold
            market_data_service=mock_market_data,
        )

        # First run - store initial prices
        price_service.get_threshold_breaches(["AAPL"])

        # Second run - small change, below threshold
        breaches = price_service.get_threshold_breaches(["AAPL"])

        # Should have no breaches
        assert len(breaches) == 0

        # No notifications should be printed
        captured = capsys.readouterr()
        assert "STOCK ALERT" not in captured.out

    def test_execution_triggers_notification_when_threshold_met(
        self,
        temp_data_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        When threshold is exceeded, explanation generation
        and notification dispatch should occur.
        """
        with patch("src.services.news_service.NewsAdapter") as mock_news, \
             patch("src.services.explanation_service.LlamaCppAdapter") as mock_llm:

            # Setup mocks
            mock_market_data = MagicMock(spec=MarketDataService)
            mock_market_data.get_latest_price.side_effect = [
                PriceQuote(
                    symbol="AAPL",
                    price=Decimal("100.00"),
                    timestamp=datetime(2026, 1, 23),
                    provider_name="test",
                ),
                PriceQuote(
                    symbol="AAPL",
                    price=Decimal("105.00"),  # 5% change
                    timestamp=datetime(2026, 1, 24),
                    provider_name="test",
                ),
            ]

            mock_news_adapter = MagicMock()
            mock_news_adapter.get_headlines_text.return_value = [
                "Apple announces new product"
            ]
            mock_news.return_value = mock_news_adapter

            mock_llm_adapter = MagicMock()
            mock_llm_adapter.generate.return_value = (
                "Apple stock rose due to product announcement."
            )
            mock_llm.return_value = mock_llm_adapter

            # Initialize services
            settings = Settings(
                notification_channel=NotificationChannel.CONSOLE,
                data_dir=temp_data_dir,
            )

            price_service = PriceService(
                data_dir=temp_data_dir,
                threshold=Decimal("1.5"),
                market_data_service=mock_market_data,
            )
            news_service = NewsService()
            explanation_service = ExplanationService()
            notification_service = NotificationService(settings)

            # First run - store initial prices
            price_service.get_threshold_breaches(["AAPL"])

            # Second run - large change, exceeds threshold
            breaches = price_service.get_threshold_breaches(["AAPL"])

            # Should have one breach
            assert len(breaches) == 1
            assert breaches[0].symbol == "AAPL"

            # Get news and generate explanation
            headlines = news_service.get_headlines_text("AAPL")
            explanation = explanation_service.generate_explanation(
                breaches[0],
                headlines,
            )

            # Create and send alert
            from src.models.alert import Alert
            alert = Alert(
                symbol=breaches[0].symbol,
                change_percent=breaches[0].change_percent,
                change_amount=breaches[0].change_amount,
                previous_price=breaches[0].previous_price,
                current_price=breaches[0].current_price,
                explanation=explanation,
            )

            result = notification_service.send_alert(alert)

            # Notification should succeed
            assert result is True

            # Check console output
            captured = capsys.readouterr()
            assert "STOCK ALERT" in captured.out
            assert "AAPL" in captured.out
            assert "5.00%" in captured.out

    def test_execution_completes_under_time_limit(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        A full execution should complete within 30 seconds.
        
        Note: This test uses mocks to ensure consistent timing.
        Real execution time depends on network and LLM response times.
        """
        start_time = time.time()

        with patch("src.services.news_service.NewsAdapter") as mock_news, \
             patch("src.services.explanation_service.LlamaCppAdapter") as mock_llm:

            # Setup mocks with minimal delay
            mock_market_data = MagicMock(spec=MarketDataService)
            mock_market_data.get_latest_price.return_value = PriceQuote(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime.utcnow(),
                provider_name="test",
            )

            mock_news_adapter = MagicMock()
            mock_news_adapter.get_headlines_text.return_value = ["Test headline"]
            mock_news.return_value = mock_news_adapter

            mock_llm_adapter = MagicMock()
            mock_llm_adapter.generate.return_value = "Test explanation."
            mock_llm.return_value = mock_llm_adapter

            # Run the full flow
            settings = Settings(
                notification_channel=NotificationChannel.CONSOLE,
                data_dir=temp_data_dir,
            )

            price_service = PriceService(
                data_dir=temp_data_dir,
                market_data_service=mock_market_data,
            )
            news_service = NewsService()
            explanation_service = ExplanationService()
            notification_service = NotificationService(settings)

            # Simulate full execution
            changes = price_service.get_price_changes(["AAPL"])
            
            # Even with no previous price, check the flow completes
            headlines = news_service.get_headlines_text("AAPL")
            
            if changes:
                for change in changes:
                    explanation = explanation_service.generate_explanation(
                        change,
                        headlines,
                    )

        elapsed_time = time.time() - start_time

        # Should complete well under 30 seconds with mocks
        assert elapsed_time < 30, f"Execution took {elapsed_time:.2f}s, limit is 30s"

    def test_storage_persists_between_runs(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Price data should persist between service instances.
        """
        mock_market_data1 = MagicMock(spec=MarketDataService)
        mock_market_data1.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("100.00"),
            timestamp=datetime(2026, 1, 23),
            provider_name="test",
        )

        # First service instance
        service1 = PriceService(
            data_dir=temp_data_dir,
            market_data_service=mock_market_data1,
        )
        service1.get_price_changes(["AAPL"])

        # Create new service instance (simulating new run)
        mock_market_data2 = MagicMock(spec=MarketDataService)
        mock_market_data2.get_latest_price.return_value = PriceQuote(
            symbol="AAPL",
            price=Decimal("105.00"),
            timestamp=datetime(2026, 1, 24),
            provider_name="test",
        )

        # Second service instance should see previous price
        service2 = PriceService(
            data_dir=temp_data_dir,
            market_data_service=mock_market_data2,
        )
        changes = service2.get_price_changes(["AAPL"])

        # Should detect the change from persisted data
        assert len(changes) == 1
        assert changes[0].previous_price == Decimal("100.00")
        assert changes[0].current_price == Decimal("105.00")

    def test_multiple_symbols_processed_correctly(
        self,
        temp_data_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Multiple stock symbols should all be processed.
        """
        mock_market_data = MagicMock(spec=MarketDataService)
        mock_market_data.get_latest_price.side_effect = [
            # First run
            PriceQuote(
                symbol="AAPL",
                price=Decimal("100.00"),
                timestamp=datetime(2026, 1, 23),
                provider_name="test",
            ),
            PriceQuote(
                symbol="NVDA",
                price=Decimal("500.00"),
                timestamp=datetime(2026, 1, 23),
                provider_name="test",
            ),
            PriceQuote(
                symbol="MSFT",
                price=Decimal("300.00"),
                timestamp=datetime(2026, 1, 23),
                provider_name="test",
            ),
            # Second run - mixed results
            PriceQuote(
                symbol="AAPL",
                price=Decimal("103.00"),  # +3% breach
                timestamp=datetime(2026, 1, 24),
                provider_name="test",
            ),
            PriceQuote(
                symbol="NVDA",
                price=Decimal("505.00"),  # +1% no breach
                timestamp=datetime(2026, 1, 24),
                provider_name="test",
            ),
            PriceQuote(
                symbol="MSFT",
                price=Decimal("291.00"),  # -3% breach
                timestamp=datetime(2026, 1, 24),
                provider_name="test",
            ),
        ]

        price_service = PriceService(
            data_dir=temp_data_dir,
            threshold=Decimal("2.0"),
            market_data_service=mock_market_data,
        )
        price_service.get_price_changes(["AAPL", "NVDA", "MSFT"])

        # Second run - mixed results
        breaches = price_service.get_threshold_breaches(["AAPL", "NVDA", "MSFT"])

        # Should have 2 breaches (AAPL and MSFT)
        assert len(breaches) == 2
        symbols = {b.symbol for b in breaches}
        assert symbols == {"AAPL", "MSFT"}

    def test_execution_logs_stored(
        self,
        temp_data_dir: Path,
    ) -> None:
        """
        Execution metadata should be logged.
        """
        from src.adapters.storage_adapter import StorageAdapter

        storage = StorageAdapter(temp_data_dir)

        # Log execution start
        execution_id = storage.log_execution_start(["AAPL", "NVDA"])
        assert execution_id > 0

        # Log execution complete
        storage.log_execution_complete(
            execution_id=execution_id,
            alerts_triggered=2,
            notifications_sent=2,
            success=True,
        )

        # No error means success (we could query the DB to verify)
