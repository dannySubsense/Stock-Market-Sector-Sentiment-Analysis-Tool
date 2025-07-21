"""
Integration Tests for Persistence Layer
Tests persistence integration and hybrid cache+database consistency
Verifies that persistence failures don't break main calculations
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

from services.persistence_interface import (
    PersistenceLayer,
    NullPersistence,
    DatabasePersistence,
)
from services.volume_weighting_1d import VolumeWeightingEngine1D
from services.iwm_benchmark_service_1d import IWMBenchmarkService1D


class MockFailingPersistence:
    """Mock persistence that always fails - for testing error handling"""

    async def store_stock_data(self, stock_data_list: List) -> bool:
        raise Exception("Simulated persistence failure")

    async def store_sector_sentiment(
        self, sector_results: Dict[str, Any], metadata=None
    ) -> bool:
        raise Exception("Simulated persistence failure")

    async def store_iwm_benchmark(self, iwm_data) -> bool:
        raise Exception("Simulated persistence failure")


class MockSuccessfulPersistence:
    """Mock persistence that always succeeds - for testing success paths"""

    def __init__(self):
        self.stored_stock_data = []
        self.stored_sector_data = []
        self.stored_iwm_data = []

    async def store_stock_data(self, stock_data_list: List) -> bool:
        self.stored_stock_data.append(stock_data_list)
        return True

    async def store_sector_sentiment(
        self, sector_results: Dict[str, Any], metadata=None
    ) -> bool:
        self.stored_sector_data.append((sector_results, metadata))
        return True

    async def store_iwm_benchmark(self, iwm_data) -> bool:
        self.stored_iwm_data.append(iwm_data)
        return True


@dataclass
class MockStockVolumeData:
    """Mock stock volume data for testing"""

    symbol: str
    price_change_1d: float
    current_volume: int
    avg_volume_20d: int
    volume_ratio: float
    is_sufficient_volume: bool
    is_volume_outlier: bool = False


class TestPersistenceIntegration:
    """Test persistence layer integration with business logic"""

    @pytest.mark.asyncio
    async def test_hybrid_cache_database_consistency_simulation(self):
        """Simulate testing cache and database contain consistent data"""
        # This would need actual cache/database setup for full integration
        # For now, test that persistence is called correctly

        mock_persistence = MockSuccessfulPersistence()
        engine = VolumeWeightingEngine1D(persistence_layer=mock_persistence)

        stock_data = [
            MockStockVolumeData("TEST", 5.0, 2000000, 1000000, 2.0, True, False)
        ]

        # Perform calculation (should trigger persistence)
        result = await engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Verify calculation succeeded
        assert result.sector == "technology"
        assert result.stock_count == 1

        # Verify persistence was called
        assert len(mock_persistence.stored_stock_data) == 1
        assert len(mock_persistence.stored_stock_data[0]) > 0

    @pytest.mark.asyncio
    async def test_persistence_failure_non_blocking(self):
        """Verify calculation succeeds even if persistence fails"""
        failing_persistence = MockFailingPersistence()
        engine = VolumeWeightingEngine1D(persistence_layer=failing_persistence)

        stock_data = [
            MockStockVolumeData("TEST", 5.0, 2000000, 1000000, 2.0, True, False)
        ]

        # Calculation should succeed despite persistence failure
        result = await engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Main calculation should still work
        assert result.sector == "technology"
        assert result.stock_count == 1
        assert result.weighted_performance is not None
        assert result.confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_cache_first_performance_maintained(self):
        """Verify persistence doesn't significantly impact calculation performance"""
        import time

        # Test with NullPersistence (no database overhead)
        null_engine = VolumeWeightingEngine1D(persistence_layer=NullPersistence())

        stock_data = [
            MockStockVolumeData(f"STOCK{i}", 5.0, 2000000, 1000000, 2.0, True, False)
            for i in range(10)  # 10 stocks for meaningful test
        ]

        start_time = time.time()
        result_null = await null_engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )
        null_duration = time.time() - start_time

        # Test with mock successful persistence (simulates database overhead)
        mock_engine = VolumeWeightingEngine1D(
            persistence_layer=MockSuccessfulPersistence()
        )

        start_time = time.time()
        result_mock = await mock_engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )
        mock_duration = time.time() - start_time

        # Results should be identical
        assert result_null.sector == result_mock.sector
        assert result_null.stock_count == result_mock.stock_count

        # Performance test - if both are very fast (< 0.001s), just ensure both complete successfully
        # Otherwise, verify persistence doesn't add significant overhead
        if null_duration < 0.001 and mock_duration < 0.001:
            # Both are very fast - this is good, just verify they completed
            assert result_null.weighted_performance is not None
            assert result_mock.weighted_performance is not None
        else:
            # Measurable time - verify persistence doesn't add too much overhead (less than 5x slower)
            assert mock_duration < null_duration * 5.0

    @pytest.mark.asyncio
    async def test_iwm_persistence_integration(self):
        """Test IWM benchmark service persistence integration"""
        mock_persistence = MockSuccessfulPersistence()

        # Mock the dependencies for IWM service
        with patch(
            "services.iwm_benchmark_service_1d.StockDataRetrieval1D"
        ) as mock_retrieval, patch(
            "services.iwm_benchmark_service_1d.get_cache_service"
        ) as mock_cache:

            # Setup mocks
            mock_retrieval_instance = AsyncMock()
            mock_retrieval.return_value = mock_retrieval_instance

            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get_cached_iwm_benchmark_1d.return_value = (
                None  # Cache miss
            )

            # Mock the refresh_iwm_data method
            iwm_service = IWMBenchmarkService1D(persistence_layer=mock_persistence)

            # Create mock IWM data
            mock_iwm_data = MagicMock()
            mock_iwm_data.performance_1d = 2.5

            # Mock the refresh method to return our mock data
            iwm_service.refresh_iwm_data = AsyncMock(return_value=mock_iwm_data)
            iwm_service._cache_iwm_data = AsyncMock()

            # Test the method
            result = await iwm_service.get_cached_iwm_benchmark_1d()

            # Verify persistence was called
            assert len(mock_persistence.stored_iwm_data) == 1

    @pytest.mark.asyncio
    async def test_database_persistence_error_handling(self):
        """Test error handling in DatabasePersistence wrapper"""
        # Test that DatabasePersistence properly handles errors

        with patch(
            "services.data_persistence_service.get_persistence_service"
        ) as mock_get_service:
            # Mock a failing persistence service
            mock_service = AsyncMock()
            mock_service.store_stock_price_data.side_effect = Exception(
                "Database error"
            )
            mock_get_service.return_value = mock_service

            db_persistence = DatabasePersistence()

            # Should return False on error, not raise exception
            result = await db_persistence.store_stock_data([])
            assert result is False

    @pytest.mark.asyncio
    async def test_persistence_layer_factory(self):
        """Test persistence layer factory function"""
        from services.persistence_interface import get_persistence_layer

        # Test null persistence
        null_persistence = get_persistence_layer(enable_database=False)
        assert isinstance(null_persistence, NullPersistence)

        # Test database persistence
        db_persistence = get_persistence_layer(enable_database=True)
        assert isinstance(db_persistence, DatabasePersistence)

    @pytest.mark.asyncio
    async def test_concurrent_persistence_operations(self):
        """Test that multiple persistence operations can run concurrently"""
        mock_persistence = MockSuccessfulPersistence()

        # Create multiple engines with same persistence layer
        engines = [
            VolumeWeightingEngine1D(persistence_layer=mock_persistence)
            for _ in range(3)
        ]

        stock_data = [
            MockStockVolumeData("TEST", 5.0, 2000000, 1000000, 2.0, True, False)
        ]

        # Run calculations concurrently
        tasks = [
            engine.calculate_weighted_sector_sentiment(f"sector_{i}", stock_data)
            for i, engine in enumerate(engines)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert result.stock_count == 1

        # All should have persisted data
        assert len(mock_persistence.stored_stock_data) == 3

    @pytest.mark.asyncio
    async def test_persistence_data_integrity(self):
        """Test that persisted data maintains integrity"""
        mock_persistence = MockSuccessfulPersistence()
        engine = VolumeWeightingEngine1D(persistence_layer=mock_persistence)

        # Test data with specific values
        stock_data = [
            MockStockVolumeData("AAPL", 3.5, 1500000, 1000000, 1.5, True, False),
            MockStockVolumeData("MSFT", -2.1, 2000000, 1000000, 2.0, True, False),
        ]

        result = await engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Verify data was persisted
        assert len(mock_persistence.stored_stock_data) == 1
        persisted_data = mock_persistence.stored_stock_data[0]

        # Verify data integrity
        assert len(persisted_data) == 2  # Both stocks should be persisted

        # Extract symbols from persisted data
        persisted_symbols = [stock.symbol for stock in persisted_data]
        assert "AAPL" in persisted_symbols
        assert "MSFT" in persisted_symbols
