import pytest
from datetime import datetime, timezone
from core.database import SessionLocal, engine
from sqlalchemy import text


class TestDataPersistence1DIntegration:
    """Integration tests for stock_prices_1d table functionality."""

    def test_stock_prices_1d_table_exists_and_functional(self):
        """Validated schema: insert/select using FMP fields (symbol, fmp_timestamp, price, previous_close, volume)."""
        test_data = {
            "symbol": "TEST_1D",
            "fmp_timestamp": int(datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc).timestamp()),
            "price": 11.00,
            "previous_close": 10.50,
            "volume": 1500000,
        }

        with SessionLocal() as session:
            try:
                # Test that the table exists by checking schema
                result = session.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_prices_1d')"
                    )
                )
                table_exists = result.scalar()
                assert table_exists is True, "stock_prices_1d table should exist"

                # Test insert operation (validated minimal column set)
                session.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d 
                    (symbol, fmp_timestamp, price, previous_close, volume)
                    VALUES (:symbol, :fmp_timestamp, :price, :previous_close, :volume)
                    """
                    ),
                    test_data,
                )
                session.commit()

                # Test query operation
                result = session.execute(
                    text(
                        "SELECT symbol, price, volume FROM stock_prices_1d WHERE symbol = :symbol"
                    ),
                    {"symbol": "TEST_1D"},
                )
                row = result.fetchone()

                assert row is not None, "Data should be inserted and retrievable"
                assert row[0] == "TEST_1D", "Symbol should match"
                assert row[1] == 11.00, "Price should match"
                assert row[2] == 1500000, "Volume should match"

            finally:
                # Cleanup
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TEST_1D"},
                )
                session.commit()

    def test_stock_prices_1d_presence_and_core_columns(self):
        """Validated schema: ensure stock_prices_1d exists and core columns are present."""
        with SessionLocal() as session:
            # Check presence of stock_prices_1d
            result = session.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'stock_prices_1d'
                """
                )
            )
            tables = [row[0] for row in result.fetchall()]
            assert "stock_prices_1d" in tables, "stock_prices_1d table should exist"

            # Verify validated columns exist
            result = session.execute(
                text(
                    """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'stock_prices_1d' 
                AND column_name IN ('symbol', 'fmp_timestamp', 'price', 'previous_close', 'recorded_at')
                ORDER BY column_name
                """
                )
            )
            columns = [row[0] for row in result.fetchall()]
            assert set(["symbol","fmp_timestamp","price","previous_close","recorded_at"]).issubset(set(columns)), (
                "stock_prices_1d should have validated core columns"
            )
