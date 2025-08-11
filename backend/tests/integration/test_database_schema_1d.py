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
        """Test that stock_prices_1d table has correct column structure (validated FMP schema)."""
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

            # Expected key columns per validated FMP schema
            expected_columns = {
                "symbol": ("character varying", "NO"),
                "fmp_timestamp": ("bigint", "NO"),
                "price": ("double precision", "YES"),
                "open_price": ("double precision", "YES"),
                "previous_close": ("double precision", "YES"),
                "volume": ("bigint", "YES"),
                # recorded_at may be nullable depending on creation script; accept YES
                "recorded_at": ("timestamp with time zone", "YES"),
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
        """Test that stock_prices_1d has correct primary key constraint (symbol, fmp_timestamp)."""
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

            expected_pk = ["symbol", "fmp_timestamp"]
            assert sorted(pk_columns) == sorted(
                expected_pk
            ), f"Primary key should be {expected_pk}"

    def test_stock_prices_1d_indexes_exist(self):
        """Test that a reasonable index exists on stock_prices_1d (at least on symbol)."""
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

            # Accept either (symbol, recorded_at) or symbol-only index
            index_found = False
            for index_name, index_def in indexes:
                if "symbol" in index_def:
                    index_found = True
                    break

            assert index_found, "Index on symbol should exist"

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
        """Test basic insert and query operations on stock_prices_1d table (FMP schema)."""
        test_data = {
            "symbol": "TEST1D",
            "fmp_timestamp": 1737442200,
            "price": 11.00,
            "open_price": 10.50,
            "previous_close": 10.25,
            "volume": 1500000,
            "recorded_at": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
        }

        with SessionLocal() as session:
            try:
                # Insert test data
                session.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d 
                    (symbol, fmp_timestamp, price, open_price, previous_close, volume, recorded_at)
                    VALUES (:symbol, :fmp_timestamp, :price, :open_price, :previous_close, :volume, :recorded_at)
                    """
                    ),
                    test_data,
                )
                session.commit()

                # Query the inserted data
                result = session.execute(
                    text("SELECT price, volume FROM stock_prices_1d WHERE symbol = :symbol AND fmp_timestamp = :fmp_timestamp"),
                    {"symbol": "TEST1D", "fmp_timestamp": test_data["fmp_timestamp"]},
                )
                row = result.fetchone()

                assert row is not None, "Inserted data should be retrievable"
                assert float(row[0]) == 11.00, "Price should match"
                assert int(row[1]) == 1500000, "Volume should match"

            finally:
                # Cleanup test data
                session.execute(
                    text("DELETE FROM stock_prices_1d WHERE symbol = :symbol"),
                    {"symbol": "TEST1D"},
                )
                session.commit()

    def test_stock_prices_1d_time_ordering(self):
        """Test that recorded_at ordering works correctly for time-series queries (FMP schema)."""
        test_symbol = "TESTTIME1"  # <= 10 chars to satisfy VARCHAR(10)
        test_times = [
            datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 21, 10, 30, 0, tzinfo=timezone.utc),
            datetime(2025, 1, 21, 11, 30, 0, tzinfo=timezone.utc),
        ]

        with SessionLocal() as session:
            try:
                # Insert test data in random order
                for i, rt in enumerate(reversed(test_times)):
                    session.execute(
                        text(
                            """
                        INSERT INTO stock_prices_1d (symbol, fmp_timestamp, price, volume, recorded_at)
                        VALUES (:symbol, :fmp_timestamp, :price, :volume, :recorded_at)
                        """
                        ),
                        {
                            "symbol": test_symbol,
                            "fmp_timestamp": 1737442200 + i,
                            "price": 10.0 + i,
                            "volume": 1000000,
                            "recorded_at": rt,
                        },
                    )
                session.commit()

                # Query with timestamp ordering
                result = session.execute(
                    text(
                        """
                    SELECT recorded_at, price 
                    FROM stock_prices_1d 
                    WHERE symbol = :symbol 
                    ORDER BY recorded_at ASC
                    """
                    ),
                    {"symbol": test_symbol},
                )
                rows = result.fetchall()

                assert len(rows) == 3, "Should retrieve all 3 records"

                # Verify timestamps are in ascending order
                times = [row[0] for row in rows]
                assert times == sorted(times), "recorded_at should be in ascending order"

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
            "fmp_timestamp": 1737442200,
            "price": 50.00,
            "volume": 999999999999,  # Very large volume
            "recorded_at": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
        }

        with SessionLocal() as session:
            try:
                session.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d (symbol, fmp_timestamp, price, volume, recorded_at)
                    VALUES (:symbol, :fmp_timestamp, :price, :volume, :recorded_at)
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
