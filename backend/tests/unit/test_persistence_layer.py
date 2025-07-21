"""
Unit Tests for Persistence Layer Components
Tests persistence logic with mocked dependencies
Focuses on testing persistence layer behavior in isolation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from services.persistence_interface import (
    PersistenceLayer,
    NullPersistence,
    DatabasePersistence,
    get_persistence_layer,
)


class TestNullPersistence:
    """Test NullPersistence implementation"""

    def setup_method(self):
        """Setup NullPersistence for testing"""
        self.null_persistence = NullPersistence()

    @pytest.mark.asyncio
    async def test_store_stock_data_always_succeeds(self):
        """Test that NullPersistence always returns True for stock data"""
        test_data = [{"symbol": "AAPL", "price": 150.0}]
        result = await self.null_persistence.store_stock_data(test_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_store_sector_sentiment_always_succeeds(self):
        """Test that NullPersistence always returns True for sector sentiment"""
        test_data = {"technology": {"sentiment": 0.75}}
        metadata = {"timestamp": "2024-01-01"}
        result = await self.null_persistence.store_sector_sentiment(test_data, metadata)
        assert result is True

    @pytest.mark.asyncio
    async def test_store_iwm_benchmark_always_succeeds(self):
        """Test that NullPersistence always returns True for IWM benchmark"""
        test_data = MagicMock()
        test_data.performance_1d = 2.5
        result = await self.null_persistence.store_iwm_benchmark(test_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_null_persistence_with_empty_data(self):
        """Test NullPersistence handles empty data gracefully"""
        assert await self.null_persistence.store_stock_data([]) is True
        assert await self.null_persistence.store_sector_sentiment({}) is True
        assert await self.null_persistence.store_iwm_benchmark(None) is True

    @pytest.mark.asyncio
    async def test_null_persistence_with_large_data(self):
        """Test NullPersistence handles large datasets"""
        large_stock_data = [{"symbol": f"STOCK{i}", "price": i} for i in range(1000)]
        result = await self.null_persistence.store_stock_data(large_stock_data)
        assert result is True


class TestDatabasePersistence:
    """Test DatabasePersistence implementation"""

    @pytest.mark.asyncio
    async def test_store_stock_data_success(self):
        """Test successful stock data storage"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.store_stock_price_data.return_value = True
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            test_data = [{"symbol": "AAPL", "price": 150.0}]
            result = await db_persistence.store_stock_data(test_data)

            # Verify success
            assert result is True
            mock_service.store_stock_price_data.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_store_stock_data_failure_handling(self):
        """Test stock data storage failure handling"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service that raises exception
            mock_service = AsyncMock()
            mock_service.store_stock_price_data.side_effect = Exception(
                "Database connection failed"
            )
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            test_data = [{"symbol": "AAPL", "price": 150.0}]
            result = await db_persistence.store_stock_data(test_data)

            # Should return False on error, not raise exception
            assert result is False

    @pytest.mark.asyncio
    async def test_store_sector_sentiment_success(self):
        """Test successful sector sentiment storage"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.store_sector_sentiment_data.return_value = True
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            test_data = {"technology": {"sentiment": 0.75}}
            metadata = {"timestamp": "2024-01-01"}
            result = await db_persistence.store_sector_sentiment(test_data, metadata)

            # Verify success
            assert result is True
            mock_service.store_sector_sentiment_data.assert_called_once_with(
                test_data, metadata
            )

    @pytest.mark.asyncio
    async def test_store_sector_sentiment_failure_handling(self):
        """Test sector sentiment storage failure handling"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service that raises exception
            mock_service = AsyncMock()
            mock_service.store_sector_sentiment_data.side_effect = Exception(
                "Database timeout"
            )
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            test_data = {"technology": {"sentiment": 0.75}}
            result = await db_persistence.store_sector_sentiment(test_data)

            # Should return False on error, not raise exception
            assert result is False

    @pytest.mark.asyncio
    async def test_store_iwm_benchmark_success(self):
        """Test successful IWM benchmark storage"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.store_iwm_benchmark_data.return_value = True
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            mock_iwm_data = MagicMock()
            mock_iwm_data.performance_1d = 2.5
            result = await db_persistence.store_iwm_benchmark(mock_iwm_data)

            # Verify success
            assert result is True
            mock_service.store_iwm_benchmark_data.assert_called_once_with(mock_iwm_data)

    @pytest.mark.asyncio
    async def test_store_iwm_benchmark_failure_handling(self):
        """Test IWM benchmark storage failure handling"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Setup mock service that raises exception
            mock_service = AsyncMock()
            mock_service.store_iwm_benchmark_data.side_effect = Exception(
                "Table lock timeout"
            )
            mock_get_service.return_value = mock_service

            # Test storage
            db_persistence = DatabasePersistence()
            mock_iwm_data = MagicMock()
            result = await db_persistence.store_iwm_benchmark(mock_iwm_data)

            # Should return False on error, not raise exception
            assert result is False

    @pytest.mark.asyncio
    async def test_database_persistence_initialization(self):
        """Test that DatabasePersistence initializes correctly"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            db_persistence = DatabasePersistence()

            # Should have called the service factory
            mock_get_service.assert_called_once()
            assert db_persistence._persistence_service == mock_service


class TestPersistenceLayerFactory:
    """Test persistence layer factory function"""

    def test_get_persistence_layer_null(self):
        """Test factory returns NullPersistence when database disabled"""
        persistence = get_persistence_layer(enable_database=False)
        assert isinstance(persistence, NullPersistence)

    def test_get_persistence_layer_database(self):
        """Test factory returns DatabasePersistence when database enabled"""
        with patch(
            "services.persistence_interface.DatabasePersistence"
        ) as mock_db_persistence:
            mock_instance = MagicMock()
            mock_db_persistence.return_value = mock_instance

            persistence = get_persistence_layer(enable_database=True)

            # Should create DatabasePersistence instance
            mock_db_persistence.assert_called_once()
            assert persistence == mock_instance

    def test_get_persistence_layer_default(self):
        """Test factory default behavior (should use database)"""
        with patch(
            "services.persistence_interface.DatabasePersistence"
        ) as mock_db_persistence:
            mock_instance = MagicMock()
            mock_db_persistence.return_value = mock_instance

            persistence = (
                get_persistence_layer()
            )  # No arguments, should default to database

            # Should create DatabasePersistence instance
            mock_db_persistence.assert_called_once()
            assert persistence == mock_instance


class TestPersistenceLayerProtocol:
    """Test that implementations conform to PersistenceLayer protocol"""

    @pytest.mark.asyncio
    async def test_null_persistence_conforms_to_protocol(self):
        """Test that NullPersistence implements PersistenceLayer protocol"""
        persistence = NullPersistence()

        # Should have all required methods
        assert hasattr(persistence, "store_stock_data")
        assert hasattr(persistence, "store_sector_sentiment")
        assert hasattr(persistence, "store_iwm_benchmark")

        # Methods should be callable
        assert callable(persistence.store_stock_data)
        assert callable(persistence.store_sector_sentiment)
        assert callable(persistence.store_iwm_benchmark)

    @pytest.mark.asyncio
    async def test_database_persistence_conforms_to_protocol(self):
        """Test that DatabasePersistence implements PersistenceLayer protocol"""
        with patch("services.data_persistence_service.get_persistence_service"):
            persistence = DatabasePersistence()

            # Should have all required methods
            assert hasattr(persistence, "store_stock_data")
            assert hasattr(persistence, "store_sector_sentiment")
            assert hasattr(persistence, "store_iwm_benchmark")

            # Methods should be callable
            assert callable(persistence.store_stock_data)
            assert callable(persistence.store_sector_sentiment)
            assert callable(persistence.store_iwm_benchmark)


class TestPersistenceErrorScenarios:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_null_persistence_with_invalid_data(self):
        """Test NullPersistence handles invalid data gracefully"""
        persistence = NullPersistence()

        # Should handle None gracefully
        assert await persistence.store_stock_data(None) is True
        assert await persistence.store_sector_sentiment(None) is True
        assert await persistence.store_iwm_benchmark(None) is True

    @pytest.mark.asyncio
    async def test_database_persistence_service_unavailable(self):
        """Test DatabasePersistence when service initialization fails"""
        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Service factory raises exception
            mock_get_service.side_effect = ImportError("Service not available")

            # Should raise the import error during initialization
            with pytest.raises(ImportError):
                DatabasePersistence()

    @pytest.mark.asyncio
    async def test_persistence_layer_type_checking(self):
        """Test type checking for persistence layer implementations"""
        # This test verifies that our implementations can be used where PersistenceLayer is expected

        def use_persistence_layer(persistence: PersistenceLayer) -> PersistenceLayer:
            return persistence

        # Both implementations should work
        null_persistence = NullPersistence()
        result = use_persistence_layer(null_persistence)
        assert result is null_persistence

        with patch("services.data_persistence_service.get_persistence_service"):
            db_persistence = DatabasePersistence()
            result = use_persistence_layer(db_persistence)
            assert result is db_persistence
