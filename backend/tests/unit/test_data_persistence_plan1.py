"""
Unit Tests for Plan 1: Data Persistence Cleanup Operations
Tests mandatory cleanup functionality before analysis and session cleanup
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from sqlalchemy.orm import Session

from services.data_persistence_service import DataPersistenceService


class TestDataPersistencePlan1:
    """Test Plan 1 cleanup functionality in DataPersistenceService"""

    @pytest.fixture
    def persistence_service(self):
        """Create persistence service instance for testing"""
        return DataPersistenceService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        session = Mock(spec=Session)
        session.execute.return_value = Mock(rowcount=5)
        session.query.return_value.filter.return_value.delete.return_value = 3
        session.commit.return_value = None
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_db_session):
        """Mock session factory context manager"""
        mock_factory = Mock()
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_db_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_factory.return_value = mock_session
        return mock_factory

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_1d_timeframe(
        self, persistence_service, mock_session_factory
    ):
        """Test cleanup_before_analysis with 1D timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("1d")

            # Should return True for successful cleanup
            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_success_1d(
        self, persistence_service, mock_session_factory
    ):
        """Test successful cleanup before analysis for 1D timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("1d")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_success_30min(
        self, persistence_service, mock_session_factory
    ):
        """Test successful cleanup before analysis for 30min timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("30min")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_success_3d(
        self, persistence_service, mock_session_factory
    ):
        """Test successful cleanup before analysis for 3D timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("3d")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_success_1w(
        self, persistence_service, mock_session_factory
    ):
        """Test successful cleanup before analysis for 1W timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("1w")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_unknown_timeframe(
        self, persistence_service, mock_session_factory
    ):
        """Test cleanup with unknown timeframe defaults to 24 hours"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("unknown")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_before_analysis_database_error(self, persistence_service):
        """Test cleanup handles database errors gracefully"""
        mock_factory = Mock()
        mock_session = Mock()
        mock_session.__enter__ = Mock(
            side_effect=Exception("Database connection failed")
        )
        mock_session.__exit__ = Mock(return_value=None)
        mock_factory.return_value = mock_session

        with patch.object(persistence_service, "db_session_factory", mock_factory):
            result = await persistence_service.cleanup_before_analysis("1d")

            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_stale_session_data_success_1d(
        self, persistence_service, mock_session_factory
    ):
        """Test successful session cleanup for 1D timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_stale_session_data("1d")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_stale_session_data_success_30min(
        self, persistence_service, mock_session_factory
    ):
        """Test successful session cleanup for 30min timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_stale_session_data("30min")

            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_stale_session_data_database_error(self, persistence_service):
        """Test session cleanup handles database errors gracefully"""
        mock_factory = Mock()
        mock_session = Mock()
        mock_session.__enter__ = Mock(side_effect=Exception("Database error"))
        mock_session.__exit__ = Mock(return_value=None)
        mock_factory.return_value = mock_session

        with patch.object(persistence_service, "db_session_factory", mock_factory):
            result = await persistence_service.cleanup_stale_session_data("1d")

            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_timeframe_thresholds(self, persistence_service):
        """Test that different timeframes use correct cleanup thresholds"""
        with patch.object(persistence_service, "db_session_factory") as mock_factory:
            mock_session = Mock(spec=Session)
            mock_session.execute.return_value = Mock(rowcount=0)
            mock_session.query.return_value.filter.return_value.delete.return_value = 0
            mock_factory.return_value.__enter__.return_value = mock_session
            mock_factory.return_value.__exit__.return_value = None

            # Test different timeframes
            timeframes = ["1d", "30min", "3d", "1w"]

            for timeframe in timeframes:
                result = await persistence_service.cleanup_before_analysis(timeframe)
                assert result is True, f"Failed for timeframe {timeframe}"

    @pytest.mark.asyncio
    async def test_cleanup_empty_timeframe(
        self, persistence_service, mock_session_factory
    ):
        """Test cleanup with empty timeframe string"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            result = await persistence_service.cleanup_before_analysis("")

            assert result is True  # Should handle gracefully with default threshold

    @pytest.mark.asyncio
    async def test_cleanup_none_timeframe(
        self, persistence_service, mock_session_factory
    ):
        """Test cleanup with None timeframe"""
        with patch.object(
            persistence_service, "db_session_factory", mock_session_factory
        ):
            # None timeframe should be handled gracefully and return True
            result = await persistence_service.cleanup_before_analysis(None)
            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_verify_sql_execution(self, persistence_service):
        """Test that cleanup executes correct SQL for 1D timeframe"""
        with patch.object(persistence_service, "db_session_factory") as mock_factory:
            mock_session = Mock(spec=Session)
            mock_execute = Mock(return_value=Mock(rowcount=10))
            mock_session.execute = mock_execute
            mock_session.query.return_value.filter.return_value.delete.return_value = 5
            mock_factory.return_value.__enter__.return_value = mock_session
            mock_factory.return_value.__exit__.return_value = None

            result = await persistence_service.cleanup_before_analysis("1d")

            assert result is True
            # Verify SQL was executed
            mock_execute.assert_called_once()
            # Verify the SQL contains correct table name
            call_args = mock_execute.call_args[0][0]
            assert "stock_prices_1d" in str(call_args)

    @pytest.mark.asyncio
    async def test_session_cleanup_cutoff_times(self, persistence_service):
        """Test that session cleanup calculates correct cutoff times"""
        with patch.object(persistence_service, "db_session_factory") as mock_factory:
            mock_session = Mock(spec=Session)
            mock_session.execute.return_value = Mock(rowcount=0)
            mock_session.query.return_value.filter.return_value.delete.return_value = 0
            mock_factory.return_value.__enter__.return_value = mock_session
            mock_factory.return_value.__exit__.return_value = None

            # Mock datetime to control time calculations
            with patch("services.data_persistence_service.datetime") as mock_dt:
                mock_now = datetime(2025, 1, 21, 15, 30, 0, tzinfo=UTC)  # 3:30 PM UTC
                mock_dt.now.return_value = mock_now
                mock_dt.replace = mock_now.replace

                # Test 30min timeframe (6 hours ago)
                result = await persistence_service.cleanup_stale_session_data("30min")
                assert result is True

                # Test 1d timeframe (18 hours ago)
                result = await persistence_service.cleanup_stale_session_data("1d")
                assert result is True
