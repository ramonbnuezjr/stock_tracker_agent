"""Main entry point for stock tracker application."""

import argparse
import logging
import socket
import sys
from datetime import datetime

from src.config import Settings, get_settings
from src.models.alert import Alert
from src.services.explanation_service import ExplanationService
from src.services.market_data_factory import create_market_data_service
from src.services.news_service import NewsService
from src.services.notification_service import NotificationService
from src.services.price_service import PriceService
from src.adapters.storage_adapter import StorageAdapter


def check_network_connectivity() -> bool:
    """Check if network connectivity is available.

    Detects sandboxed environments (like Cursor's sandbox) that block
    DNS resolution and network access.

    Returns:
        True if network is available, False if sandboxed.
    """
    try:
        socket.gethostbyname("google.com")
        return True
    except Exception:
        return False


def setup_logging(level: str) -> None:
    """Configure logging for the application.

    Args:
        level: The logging level (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_check(settings: Settings) -> int:
    """Run a stock price check and send alerts.

    Args:
        settings: Application settings.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = logging.getLogger(__name__)
    start_time = datetime.utcnow()

    # Preflight check: Detect sandboxed environment
    if not check_network_connectivity():
        logger.warning(
            "Network unavailable. Running in sandboxed environment. "
            "Live market data will fail. Use terminal to run smoke tests."
        )
        logger.warning(
            "See .cursor/sandbox_execution.md for details on Cursor's "
            "sandbox limitations."
        )

    # Initialize storage for execution logging
    storage = StorageAdapter(settings.ensure_data_dir())
    execution_id = storage.log_execution_start(settings.symbols_list)

    alerts_triggered = 0
    notifications_sent = 0

    try:
        logger.info("Starting stock check for: %s", settings.stock_symbols)
        logger.info("Threshold: %.2f%%", settings.price_threshold)

        # Initialize market data service with multi-provider fallback
        market_data_service = create_market_data_service(settings)

        # Initialize services
        price_service = PriceService(
            data_dir=settings.ensure_data_dir(),
            threshold=settings.price_threshold,
            market_data_service=market_data_service,
        )
        news_service = NewsService()
        explanation_service = ExplanationService(
            model_path=settings.llama_model_path,
            n_ctx=settings.llama_n_ctx,
            n_gpu_layers=settings.llama_n_gpu_layers,
        )
        notification_service = NotificationService(settings)

        # Check for threshold breaches
        breaches = price_service.get_threshold_breaches(settings.symbols_list)

        if not breaches:
            logger.info("No threshold breaches detected")
            storage.log_execution_complete(
                execution_id=execution_id,
                alerts_triggered=0,
                notifications_sent=0,
                success=True,
            )
            return 0

        alerts_triggered = len(breaches)
        logger.info("Found %d threshold breaches", alerts_triggered)

        # Process each breach
        alerts: list[Alert] = []

        for breach in breaches:
            logger.info(
                "Processing alert for %s: %.2f%%",
                breach.symbol,
                breach.change_percent,
            )

            # Fetch news
            headlines = news_service.get_headlines_text(
                breach.symbol,
                max_headlines=5,
            )

            # Generate explanation
            explanation = explanation_service.generate_explanation(
                breach,
                headlines,
            )

            # Create alert
            alert = Alert(
                symbol=breach.symbol,
                change_percent=breach.change_percent,
                change_amount=breach.change_amount,
                previous_price=breach.previous_price,
                current_price=breach.current_price,
                explanation=explanation,
                timestamp=datetime.utcnow(),
            )
            alerts.append(alert)

            # Save alert to storage
            storage.save_alert(
                symbol=alert.symbol,
                change_percent=alert.change_percent,
                change_amount=alert.change_amount,
                previous_price=alert.previous_price,
                current_price=alert.current_price,
                explanation=explanation.text,
            )

        # Send notifications
        notifications_sent = notification_service.send_alerts(alerts)
        logger.info("Sent %d notifications", notifications_sent)

        # Log execution completion
        storage.log_execution_complete(
            execution_id=execution_id,
            alerts_triggered=alerts_triggered,
            notifications_sent=notifications_sent,
            success=True,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("Check completed in %.2f seconds", duration)

        return 0

    except Exception as e:
        logger.error("Error during stock check: %s", e, exc_info=True)
        storage.log_execution_complete(
            execution_id=execution_id,
            alerts_triggered=alerts_triggered,
            notifications_sent=notifications_sent,
            success=False,
            error_message=str(e),
        )
        return 1


def run_test(settings: Settings) -> int:
    """Send a test notification.

    Args:
        settings: Application settings.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = logging.getLogger(__name__)
    logger.info("Sending test notification via %s", settings.notification_channel)

    notification_service = NotificationService(settings)
    success = notification_service.test_notification()

    return 0 if success else 1


def run_status(settings: Settings) -> int:
    """Display current configuration and status.

    Args:
        settings: Application settings.

    Returns:
        Exit code (always 0).
    """
    print("\nStock Tracker Status")
    print("=" * 40)
    print(f"Symbols: {settings.stock_symbols}")
    print(f"Threshold: {settings.price_threshold}%")
    print(f"Notification: {settings.notification_channel.value}")
    print(f"LLM Model: {settings.llama_model_path or '(not set)'}")
    print(f"Data Dir: {settings.data_dir}")
    print(f"Log Level: {settings.log_level.value}")

    # Check LLM availability
    explanation_service = ExplanationService(
        model_path=settings.llama_model_path,
        n_ctx=settings.llama_n_ctx,
        n_gpu_layers=settings.llama_n_gpu_layers,
    )
    llm_available = explanation_service.is_available()
    print(f"LLM Available: {'Yes' if llm_available else 'No'}")

    if not llm_available:
        print("  -> Set LLAMA_MODEL_PATH to your Phi-3 Mini GGUF file")
        print("  -> Install: pip install llama-cpp-python")
        print("  -> On Mac M2: CMAKE_ARGS=\"-DGGML_METAL=on\" pip install llama-cpp-python")

    # Check notification config
    if settings.notification_channel.value == "email":
        email_ok = settings.validate_email_config()
        print(f"Email Config: {'Complete' if email_ok else 'Incomplete'}")

    print("=" * 40 + "\n")
    return 0


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = argparse.ArgumentParser(
        description="Stock Tracker - Monitor prices with LLM explanations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stock-tracker check        Run a price check and send alerts
  stock-tracker test         Send a test notification
  stock-tracker status       Show current configuration

Environment variables:
  STOCK_SYMBOLS       Comma-separated stock symbols (default: AAPL,NVDA,MSFT)
  PRICE_THRESHOLD     Alert threshold percentage (default: 1.5)
  NOTIFICATION_CHANNEL  console, email, or sms (default: console)
  LLAMA_MODEL_PATH    Path to GGUF model for explanations (e.g. Phi-3 Mini)
        """,
    )

    parser.add_argument(
        "command",
        choices=["check", "test", "status"],
        help="Command to run",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        return 1

    # Setup logging
    log_level = "DEBUG" if args.verbose else settings.log_level.value
    setup_logging(log_level)

    # Run command
    if args.command == "check":
        return run_check(settings)
    elif args.command == "test":
        return run_test(settings)
    elif args.command == "status":
        return run_status(settings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
