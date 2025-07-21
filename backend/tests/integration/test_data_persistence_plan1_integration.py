"""
Integration Tests for Plan 1: Data Persistence Cleanup Operations
Tests mandatory cleanup functionality with real database operations
"""

import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import text

from core.database import SessionLocal
from models.sector_sentiment import SectorSentiment
from services.data_persistence_service import DataPersistenceService


class TestDataPersistencePlan1Integration:
    """Integration tests for Plan 1 cleanup functionality with real database"""

    @pytest.fixture
    def persistence_service(self):
        """Create persistence service for integration testing"""
        return DataPersistenceService()

    @pytest.fixture
    def cleanup_test_data(self):
        """Cleanup any test data after each test"""
        yield
        # Cleanup after test
        with SessionLocal() as db:
            # Clean up test stock price data
            db.execute(text("DELETE FROM stock_prices_1d WHERE symbol LIKE 'TEST%'"))
            # Clean up test sector sentiment data
            db.query(SectorSentiment).filter(
                SectorSentiment.sector.like("test_%")
            ).delete()
            db.commit()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_with_real_database(
        self, persistence_service, cleanup_test_data
    ):
        """Test cleanup_before_analysis with real database operations"""
        # Setup: Insert test data that should be cleaned up
        with SessionLocal() as db:
            # Insert old price data (25 hours ago - should be cleaned for 1d)
            old_timestamp = datetime.now(UTC) - timedelta(hours=25)
            db.execute(
                text(
                    """
                INSERT INTO stock_prices_1d 
                (symbol, timestamp, close_price, volume) 
                VALUES (:symbol, :timestamp, :price, :volume)
                """
                ),
                {
                    "symbol": "TESTO",  # Shortened from TEST_OLD
                    "timestamp": old_timestamp,
                    "price": 10.50,
                    "volume": 1000000,
                },
            )

            # Insert recent price data (1 hour ago - should NOT be cleaned)
            recent_timestamp = datetime.now(UTC) - timedelta(hours=1)
            db.execute(
                text(
                    """
                INSERT INTO stock_prices_1d 
                (symbol, timestamp, close_price, volume) 
                VALUES (:symbol, :timestamp, :price, :volume)
                """
                ),
                {
                    "symbol": "TESTR",  # Shortened from TEST_RECENT
                    "timestamp": recent_timestamp,
                    "price": 11.50,
                    "volume": 1500000,
                },
            )

            # Insert old sector sentiment data
            old_sentiment = SectorSentiment(
                sector="test_tech",
                timeframe="1d",
                timestamp=old_timestamp,
                sentiment_score=0.75,
                bullish_count=5,
                bearish_count=2,
                total_volume=10000000,
            )
            db.add(old_sentiment)

            # Insert recent sector sentiment data
            recent_sentiment = SectorSentiment(
                sector="test_health",
                timeframe="1d",
                timestamp=recent_timestamp,
                sentiment_score=0.45,
                bullish_count=3,
                bearish_count=4,
                total_volume=8000000,
            )
            db.add(recent_sentiment)

            db.commit()

            # Verify data was inserted
            price_count_before = db.execute(
                text("SELECT COUNT(*) FROM stock_prices_1d WHERE symbol LIKE 'TEST%'")
            ).scalar()
            sentiment_count_before = (
                db.query(SectorSentiment)
                .filter(SectorSentiment.sector.like("test_%"))
                .count()
            )

            assert price_count_before == 2
            assert sentiment_count_before == 2

        # Execute cleanup
        result = await persistence_service.cleanup_before_analysis("1d")
        assert result is True

        # Verify cleanup results
        with SessionLocal() as db:
            # Check remaining price data
            remaining_prices = db.execute(
                text("SELECT symbol FROM stock_prices_1d WHERE symbol LIKE 'TEST%'")
            ).fetchall()

            # Should only have recent data
            remaining_symbols = [row[0] for row in remaining_prices]
            assert "TESTR" in remaining_symbols
            assert "TESTO" not in remaining_symbols

            # Check remaining sentiment data
            remaining_sentiment = (
                db.query(SectorSentiment)
                .filter(SectorSentiment.sector.like("test_%"))
                .all()
            )

            # Should only have recent sentiment data
            assert len(remaining_sentiment) == 1
            assert remaining_sentiment[0].sector == "test_health"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_stale_session_data_with_real_database(
        self, persistence_service, cleanup_test_data
    ):
        """Test cleanup_stale_session_data with real database operations"""
        # Setup: Insert session data that should be cleaned up
        with SessionLocal() as db:
            # Insert data from previous session (20 hours ago for 1d)
            previous_session = datetime.now(UTC) - timedelta(hours=20)
            db.execute(
                text(
                    """
                INSERT INTO stock_prices_1d 
                (symbol, timestamp, close_price, volume) 
                VALUES (:symbol, :timestamp, :price, :volume)
                """
                ),
                {
                    "symbol": "TEST_PREV_SESSION",
                    "timestamp": previous_session,
                    "price": 12.50,
                    "volume": 2000000,
                },
            )

            # Insert current session data (2 hours ago - should remain)
            current_session = datetime.now(UTC) - timedelta(hours=2)
            db.execute(
                text(
                    """
                INSERT INTO stock_prices_1d 
                (symbol, timestamp, close_price, volume) 
                VALUES (:symbol, :timestamp, :price, :volume)
                """
                ),
                {
                    "symbol": "TEST_CURR_SESSION",
                    "timestamp": current_session,
                    "price": 13.50,
                    "volume": 2500000,
                },
            )

            db.commit()

        # Execute session cleanup
        result = await persistence_service.cleanup_stale_session_data("1d")
        assert result is True

        # Verify session cleanup results
        with SessionLocal() as db:
            remaining_session_data = db.execute(
                text(
                    "SELECT symbol FROM stock_prices_1d WHERE symbol LIKE 'TEST_%_SESSION'"
                )
            ).fetchall()

            remaining_symbols = [row[0] for row in remaining_session_data]
            assert "TEST_CURR_SESSION" in remaining_symbols
            assert "TEST_PREV_SESSION" not in remaining_symbols

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_different_timeframes_integration(
        self, persistence_service, cleanup_test_data
    ):
        """Test cleanup with different timeframes using real database"""
        # Setup test data for different timeframe scenarios
        with SessionLocal() as db:
            current_time = datetime.now(UTC)

            # Data scenarios for different timeframes
            test_scenarios = [
                # (timeframe, data_age_hours, should_be_cleaned)
                ("30min", 5, True),  # 5 hours old for 30min (> 4 hour threshold)
                ("30min", 2, False),  # 2 hours old for 30min (< 4 hour threshold)
                ("1d", 25, True),  # 25 hours old for 1d (> 24 hour threshold)
                ("1d", 12, False),  # 12 hours old for 1d (< 24 hour threshold)
            ]

            for timeframe, age_hours, should_clean in test_scenarios:
                timestamp = current_time - timedelta(hours=age_hours)
                symbol = f"TEST_{timeframe}_{age_hours}H"

                db.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d 
                    (symbol, timestamp, close_price, volume) 
                    VALUES (:symbol, :timestamp, :price, :volume)
                    """
                    ),
                    {
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "price": 15.00,
                        "volume": 1000000,
                    },
                )

                # Add corresponding sentiment data
                sentiment = SectorSentiment(
                    sector=f"test_{timeframe}_{age_hours}",
                    timeframe=timeframe,
                    timestamp=timestamp,
                    sentiment_score=0.5,
                    bullish_count=2,
                    bearish_count=2,
                    total_volume=5000000,
                )
                db.add(sentiment)

            db.commit()

        # Test cleanup for 30min timeframe
        result = await persistence_service.cleanup_before_analysis("30min")
        assert result is True

        # Test cleanup for 1d timeframe
        result = await persistence_service.cleanup_before_analysis("1d")
        assert result is True

        # Verify results
        with SessionLocal() as db:
            remaining_data = db.execute(
                text("SELECT symbol FROM stock_prices_1d WHERE symbol LIKE 'TEST_%H'")
            ).fetchall()

            remaining_symbols = [row[0] for row in remaining_data]

            # Based on cleanup logic, only data within thresholds should remain
            expected_remaining = ["TEST_30min_2H", "TEST_1d_12H"]

            for expected in expected_remaining:
                assert (
                    expected in remaining_symbols
                ), f"Expected {expected} to remain after cleanup"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_empty_database_integration(
        self, persistence_service, cleanup_test_data
    ):
        """Test cleanup operations on empty database tables"""
        # Ensure tables are empty for this test
        with SessionLocal() as db:
            db.execute(text("DELETE FROM stock_prices_1d WHERE symbol LIKE 'TEST%'"))
            db.query(SectorSentiment).filter(
                SectorSentiment.sector.like("test_%")
            ).delete()
            db.commit()

        # Test cleanup on empty tables
        result = await persistence_service.cleanup_before_analysis("1d")
        assert result is True

        result = await persistence_service.cleanup_stale_session_data("1d")
        assert result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_large_dataset_performance(
        self, persistence_service, cleanup_test_data
    ):
        """Test cleanup performance with larger dataset"""
        # Setup: Insert larger test dataset
        with SessionLocal() as db:
            current_time = datetime.now(UTC)
            old_time = current_time - timedelta(hours=25)  # Older than 1d threshold

            # Insert multiple records for performance testing
            test_symbols = [f"PERF_TEST_{i:03d}" for i in range(50)]

            for symbol in test_symbols:
                db.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d 
                    (symbol, timestamp, close_price, volume) 
                    VALUES (:symbol, :timestamp, :price, :volume)
                    """
                    ),
                    {
                        "symbol": symbol,
                        "timestamp": old_time,
                        "price": 20.00,
                        "volume": 1000000,
                    },
                )

            db.commit()

            # Verify data insertion
            count_before = db.execute(
                text(
                    "SELECT COUNT(*) FROM stock_prices_1d WHERE symbol LIKE 'PERF_TEST_%'"
                )
            ).scalar()
            assert count_before == 50

        # Execute cleanup and measure basic performance
        import time

        start_time = time.time()
        result = await persistence_service.cleanup_before_analysis("1d")
        end_time = time.time()

        cleanup_duration = end_time - start_time

        assert result is True
        assert cleanup_duration < 10.0  # Should complete within 10 seconds

        # Verify cleanup completed
        with SessionLocal() as db:
            count_after = db.execute(
                text(
                    "SELECT COUNT(*) FROM stock_prices_1d WHERE symbol LIKE 'PERF_TEST_%'"
                )
            ).scalar()
            assert count_after == 0  # All old data should be cleaned up
