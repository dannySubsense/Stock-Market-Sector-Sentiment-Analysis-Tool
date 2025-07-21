import pytest
from datetime import datetime, timezone
from core.database import SessionLocal, engine
from sqlalchemy import text


class TestDataPersistence1DIntegration:
    """Integration tests for stock_prices_1d table functionality."""

    def test_stock_prices_1d_table_exists_and_functional(self):
        """Test that stock_prices_1d table exists and basic operations work."""
        test_data = {
            "symbol": "TEST_1D",
            "timestamp": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            "open_price": 10.50,
            "high_price": 11.25,
            "low_price": 10.25,
            "close_price": 11.00,
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

                # Test insert operation
                session.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d 
                    (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                    VALUES (:symbol, :timestamp, :open_price, :high_price, :low_price, :close_price, :volume)
                    """
                    ),
                    test_data,
                )
                session.commit()

                # Test query operation
                result = session.execute(
                    text(
                        "SELECT symbol, close_price, volume FROM stock_prices_1d WHERE symbol = :symbol"
                    ),
                    {"symbol": "TEST_1D"},
                )
                row = result.fetchone()

                assert row is not None, "Data should be inserted and retrievable"
                assert row[0] == "TEST_1D", "Symbol should match"
                assert row[1] == 11.00, "Close price should match"
                assert row[2] == 1500000, "Volume should match"

            finally:
                # Cleanup
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TEST_1D"},
                )
                session.commit()

    def test_stock_prices_1d_vs_stock_prices_separation(self):
        """Test that stock_prices_1d is separate from stock_prices table."""
        with SessionLocal() as session:
            # Check both tables exist
            result = session.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('stock_prices', 'stock_prices_1d')
                ORDER BY table_name
                """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            # Should have both tables
            assert (
                "stock_prices" in tables
            ), "Original stock_prices table should still exist"
            assert "stock_prices_1d" in tables, "New stock_prices_1d table should exist"

            # Verify they have same basic structure but are separate
            for table in ["stock_prices", "stock_prices_1d"]:
                result = session.execute(
                    text(
                        f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name IN ('symbol', 'timestamp', 'close_price', 'volume')
                    ORDER BY column_name
                    """
                    )
                )
                columns = [row[0] for row in result.fetchall()]
                assert len(columns) == 4, f"Table {table} should have required columns"
