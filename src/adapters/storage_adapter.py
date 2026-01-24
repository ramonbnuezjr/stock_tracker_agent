"""SQLite storage adapter for price history and execution metadata."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Generator, List, Optional

from src.models.stock import PricePoint


class StorageAdapter:
    """SQLite storage adapter for persisting price data and execution logs.

    Args:
        data_dir: Directory to store the database file.

    Returns:
        A StorageAdapter instance.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize the storage adapter.

        Args:
            data_dir: Directory to store the database file.
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "stock_tracker.db"
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection context manager.

        Yields:
            A sqlite3 Connection object.
        """
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Price history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price TEXT NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_symbol_timestamp
                ON price_history (symbol, timestamp DESC)
            """)

            # Execution log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    symbols_checked TEXT,
                    alerts_triggered INTEGER DEFAULT 0,
                    notifications_sent INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                )
            """)

            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    change_percent TEXT NOT NULL,
                    change_amount TEXT NOT NULL,
                    previous_price TEXT NOT NULL,
                    current_price TEXT NOT NULL,
                    explanation TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    notified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_price(self, price_point: PricePoint) -> int:
        """Save a price point to the database.

        Args:
            price_point: The price point to save.

        Returns:
            The row ID of the inserted record.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO price_history (symbol, price, currency, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    price_point.symbol,
                    str(price_point.price),
                    price_point.currency,
                    price_point.timestamp,
                ),
            )
            return cursor.lastrowid or 0

    def get_latest_price(self, symbol: str) -> Optional[PricePoint]:
        """Get the most recent price for a symbol.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The latest PricePoint or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT symbol, price, currency, timestamp
                FROM price_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (symbol.upper(),),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return PricePoint(
                symbol=row["symbol"],
                price=Decimal(row["price"]),
                currency=row["currency"],
                timestamp=row["timestamp"],
            )

    def get_previous_price(self, symbol: str) -> Optional[PricePoint]:
        """Get the second most recent price for comparison.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The previous PricePoint or None if not enough history.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT symbol, price, currency, timestamp
                FROM price_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 1 OFFSET 1
                """,
                (symbol.upper(),),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return PricePoint(
                symbol=row["symbol"],
                price=Decimal(row["price"]),
                currency=row["currency"],
                timestamp=row["timestamp"],
            )

    def get_price_history(
        self,
        symbol: str,
        limit: int = 100,
    ) -> List[PricePoint]:
        """Get price history for a symbol.

        Args:
            symbol: The stock ticker symbol.
            limit: Maximum number of records to return.

        Returns:
            List of PricePoint objects, most recent first.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT symbol, price, currency, timestamp
                FROM price_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol.upper(), limit),
            )
            rows = cursor.fetchall()

            return [
                PricePoint(
                    symbol=row["symbol"],
                    price=Decimal(row["price"]),
                    currency=row["currency"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    def log_execution_start(self, symbols: List[str]) -> int:
        """Log the start of an execution run.

        Args:
            symbols: List of symbols being checked.

        Returns:
            The execution log ID.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO execution_log (started_at, symbols_checked)
                VALUES (?, ?)
                """,
                (datetime.utcnow(), ",".join(symbols)),
            )
            return cursor.lastrowid or 0

    def log_execution_complete(
        self,
        execution_id: int,
        alerts_triggered: int,
        notifications_sent: int,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log the completion of an execution run.

        Args:
            execution_id: The execution log ID from log_execution_start.
            alerts_triggered: Number of alerts that were triggered.
            notifications_sent: Number of notifications sent.
            success: Whether the execution completed successfully.
            error_message: Error message if execution failed.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE execution_log
                SET completed_at = ?,
                    alerts_triggered = ?,
                    notifications_sent = ?,
                    success = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    datetime.utcnow(),
                    alerts_triggered,
                    notifications_sent,
                    1 if success else 0,
                    error_message,
                    execution_id,
                ),
            )

    def save_alert(
        self,
        symbol: str,
        change_percent: Decimal,
        change_amount: Decimal,
        previous_price: Decimal,
        current_price: Decimal,
        explanation: Optional[str] = None,
        notified: bool = False,
    ) -> int:
        """Save an alert record.

        Args:
            symbol: The stock ticker symbol.
            change_percent: The percentage change.
            change_amount: The absolute price change.
            previous_price: The previous price.
            current_price: The current price.
            explanation: The LLM-generated explanation.
            notified: Whether notification was sent.

        Returns:
            The alert record ID.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts (
                    symbol, change_percent, change_amount,
                    previous_price, current_price, explanation,
                    timestamp, notified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    str(change_percent),
                    str(change_amount),
                    str(previous_price),
                    str(current_price),
                    explanation,
                    datetime.utcnow(),
                    1 if notified else 0,
                ),
            )
            return cursor.lastrowid or 0
