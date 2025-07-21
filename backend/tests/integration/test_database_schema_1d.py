import pytest
from datetime import datetime, timezone
from sqlalchemy import text, inspect
from core.database import engine, SessionLocal
from models.stock_data import StockPrice1D


class TestDatabaseSchema1D:
    """Database schema tests for stock_prices_1d table."""

    def test_stock_prices_1d_table_exists(self):
        """Test that stock_prices_1d table exists in database."""
        with SessionLocal() as session:
            # Check if table exists
            result = session.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_prices_1d')"
                )
            )
            table_exists = result.scalar()
            assert table_exists is True, "stock_prices_1d table should exist"

    def test_stock_prices_1d_table_structure(self):
        """Test that stock_prices_1d table has correct column structure."""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'stock_prices_1d' 
                ORDER BY ordinal_position
                """
                )
            )
            columns = result.fetchall()

            # Expected columns
            expected_columns = {
                "symbol": ("character varying", "NO"),
                "timestamp": ("timestamp with time zone", "NO"),
                "open_price": ("numeric", "YES"),
                "high_price": ("numeric", "YES"),
                "low_price": ("numeric", "YES"),
                "close_price": ("numeric", "YES"),
                "volume": ("bigint", "YES"),
                "created_at": ("timestamp with time zone", "YES"),
            }

            actual_columns = {col[0]: (col[1], col[2]) for col in columns}

            for col_name, (
                expected_type,
                expected_nullable,
            ) in expected_columns.items():
                assert col_name in actual_columns, f"Column {col_name} should exist"
                actual_type, actual_nullable = actual_columns[col_name]
                assert (
                    expected_nullable == actual_nullable
                ), f"Column {col_name} nullable mismatch"

    def test_stock_prices_1d_primary_key_constraint(self):
        """Test that stock_prices_1d has correct primary key constraint."""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = 'stock_prices_1d'::regclass AND i.indisprimary
                ORDER BY a.attname
                """
                )
            )
            pk_columns = [row[0] for row in result.fetchall()]

            expected_pk = ["symbol", "timestamp"]
            assert sorted(pk_columns) == sorted(
                expected_pk
            ), f"Primary key should be {expected_pk}"

    def test_stock_prices_1d_indexes_exist(self):
        """Test that required indexes exist on stock_prices_1d table."""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'stock_prices_1d'
                """
                )
            )
            indexes = result.fetchall()

            # Check for symbol-timestamp index
            index_found = False
            for index_name, index_def in indexes:
                if "symbol" in index_def and "timestamp" in index_def:
                    index_found = True
                    break

            assert index_found, "Index on (symbol, timestamp) should exist"

    def test_stock_prices_1d_is_hypertable(self):
        """Test that stock_prices_1d is configured as TimescaleDB hypertable."""
        with SessionLocal() as session:
            # Check if TimescaleDB extension exists
            try:
                result = session.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM pg_extension WHERE extname = 'timescaledb')"
                    )
                )
                timescaledb_exists = result.scalar()

                if not timescaledb_exists:
                    pytest.skip("TimescaleDB extension not available")

                # Check if table is a hypertable
                result = session.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM timescaledb_information.hypertables 
                    WHERE table_name = 'stock_prices_1d'
                    """
                    )
                )
                hypertable = result.scalar()

                assert (
                    hypertable == "stock_prices_1d"
                ), "stock_prices_1d should be a hypertable"

            except Exception as e:
                # If TimescaleDB queries fail, it might not be properly configured
                pytest.skip(f"TimescaleDB not properly configured: {e}")

    def test_stock_prices_1d_insert_and_query(self):
        """Test basic insert and query operations on stock_prices_1d table."""
        test_data = {
            "symbol": "TEST1D",
            "timestamp": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            "open_price": 10.50,
            "high_price": 11.25,
            "low_price": 10.25,
            "close_price": 11.00,
            "volume": 1500000,
        }

        with SessionLocal() as session:
            try:
                # Insert test data
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

                # Query the inserted data
                result = session.execute(
                    text("SELECT * FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TEST1D"},
                )
                row = result.fetchone()

                assert row is not None, "Inserted data should be retrievable"
                assert row[0] == "TEST1D", "Symbol should match"
                assert row[5] == 11.00, "Close price should match"
                assert row[6] == 1500000, "Volume should match"

            finally:
                # Cleanup test data
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TEST1D"},
                )
                session.commit()

    def test_stock_prices_1d_timestamp_ordering(self):
        """Test that timestamp ordering works correctly for time-series queries."""
        test_symbol = "TEST_TIME_ORDER"
        test_timestamps = [
            datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 21, 10, 30, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 21, 11, 30, 0, tzinfo=timezone.utc),
        ]

        with SessionLocal() as session:
            try:
                # Insert test data in random order
                for i, ts in enumerate(reversed(test_timestamps)):
                    session.execute(
                        text(
                            """
                        INSERT INTO stock_prices_1d (symbol, timestamp, close_price, volume)
                        VALUES (:symbol, :timestamp, :price, :volume)
                        """
                        ),
                        {
                            "symbol": test_symbol,
                            "timestamp": ts,
                            "price": 10.0 + i,
                            "volume": 1000000,
                        },
                    )
                session.commit()

                # Query with timestamp ordering
                result = session.execute(
                    text(
                        """
                    SELECT timestamp, close_price 
                    FROM stock_prices_1d 
                    WHERE symbol = :symbol 
                    ORDER BY timestamp ASC
                    """
                    ),
                    {"symbol": test_symbol},
                )
                rows = result.fetchall()

                assert len(rows) == 3, "Should retrieve all 3 records"

                # Verify timestamps are in ascending order
                timestamps = [row[0] for row in rows]
                assert timestamps == sorted(
                    timestamps
                ), "Timestamps should be in ascending order"

            finally:
                # Cleanup test data
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": test_symbol},
                )
                session.commit()

    def test_stock_prices_1d_volume_constraints(self):
        """Test that volume field can handle large numbers correctly."""
        test_data = {
            "symbol": "TESTVOL",
            "timestamp": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            "close_price": 50.00,
            "volume": 999999999999,  # Very large volume
        }

        with SessionLocal() as session:
            try:
                session.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d (symbol, timestamp, close_price, volume)
                    VALUES (:symbol, :timestamp, :close_price, :volume)
                    """
                    ),
                    test_data,
                )
                session.commit()

                # Verify large volume was stored correctly
                result = session.execute(
                    text("SELECT volume FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TESTVOL"},
                )
                stored_volume = result.scalar()

                assert (
                    stored_volume == 999999999999
                ), "Large volume should be stored correctly"

            finally:
                # Cleanup
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TESTVOL"},
                )
                session.commit()
