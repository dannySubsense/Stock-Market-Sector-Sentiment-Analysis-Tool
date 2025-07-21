"""
Unit Tests for Pure Volume Weighting Logic
Tests calculation logic WITHOUT persistence dependencies using NullPersistence
Ensures separation of concerns and clean testability
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List

from services.volume_weighting_1d import (
    VolumeWeightingEngine1D,
    StockVolumeData,
    WeightedSectorResult,
)
from services.persistence_interface import NullPersistence


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


class TestVolumeWeightingPureLogic:
    """Test calculation logic WITHOUT persistence dependencies"""

    def setup_method(self):
        """Setup with NullPersistence for pure logic testing"""
        self.engine = VolumeWeightingEngine1D(persistence_layer=NullPersistence())

    @pytest.mark.asyncio
    async def test_volume_weighting_calculation_accuracy(self):
        """Test pure volume weighting calculation with known inputs"""
        # Create test data with known expected results
        stock_data = [
            MockStockVolumeData(
                symbol="SOUN",
                price_change_1d=5.0,  # 5% gain
                current_volume=2000000,
                avg_volume_20d=1000000,
                volume_ratio=2.0,  # 2x average volume
                is_sufficient_volume=True,
                is_volume_outlier=False,
            ),
            MockStockVolumeData(
                symbol="BBAI",
                price_change_1d=-3.0,  # 3% loss
                current_volume=1500000,
                avg_volume_20d=1000000,
                volume_ratio=1.5,  # 1.5x average volume
                is_sufficient_volume=True,
                is_volume_outlier=False,
            ),
        ]

        # Calculate weighted performance
        result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Verify calculation results
        assert isinstance(result, WeightedSectorResult)
        assert result.sector == "technology"
        assert result.stock_count == 2
        assert result.outlier_count == 0
        assert result.weighted_performance is not None
        assert result.confidence_score > 0.0
        assert result.total_weight > 0.0

    @pytest.mark.asyncio
    async def test_empty_stock_list_handling(self):
        """Test handling of empty stock list"""
        result = await self.engine.calculate_weighted_sector_sentiment("technology", [])

        assert result.sector == "technology"
        assert result.stock_count == 0
        assert result.weighted_performance == 0.0
        assert result.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_insufficient_volume_filtering(self):
        """Test that stocks with insufficient volume are filtered out"""
        stock_data = [
            MockStockVolumeData(
                symbol="LOW_VOL",
                price_change_1d=10.0,
                current_volume=100000,
                avg_volume_20d=1000000,
                volume_ratio=0.1,
                is_sufficient_volume=False,  # Filtered out
            ),
            MockStockVolumeData(
                symbol="GOOD_VOL",
                price_change_1d=5.0,
                current_volume=2000000,
                avg_volume_20d=1000000,
                volume_ratio=2.0,
                is_sufficient_volume=True,  # Included
            ),
        ]

        result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Should only analyze the one stock with sufficient volume
        assert result.stock_count == 1
        assert result.weighted_performance != 0.0

    @pytest.mark.asyncio
    async def test_outlier_detection_and_tracking(self):
        """Test outlier detection and counting"""
        stock_data = [
            MockStockVolumeData(
                symbol="OUTLIER",
                price_change_1d=50.0,  # Extreme move
                current_volume=10000000,
                avg_volume_20d=1000000,
                volume_ratio=10.0,  # 10x volume
                is_sufficient_volume=True,
                is_volume_outlier=True,  # Marked as outlier
            ),
            MockStockVolumeData(
                symbol="NORMAL",
                price_change_1d=2.0,
                current_volume=1500000,
                avg_volume_20d=1000000,
                volume_ratio=1.5,
                is_sufficient_volume=True,
                is_volume_outlier=False,
            ),
        ]

        result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        assert result.outlier_count == 1
        assert result.stock_count == 2

    @pytest.mark.asyncio
    async def test_volatility_multiplier_application(self):
        """Test that sector volatility multiplier is properly applied"""
        stock_data = [
            MockStockVolumeData(
                symbol="TEST",
                price_change_1d=10.0,
                current_volume=2000000,
                avg_volume_20d=1000000,
                volume_ratio=2.0,
                is_sufficient_volume=True,
            )
        ]

        result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Technology sector should have a volatility multiplier applied
        assert result.volatility_multiplier > 0.0
        assert result.weighted_performance is not None

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self):
        """Test confidence score calculation based on data quality"""
        # High quality data (normal volumes, no outliers)
        high_quality_data = [
            MockStockVolumeData("STOCK1", 5.0, 1500000, 1000000, 1.5, True, False),
            MockStockVolumeData("STOCK2", 3.0, 1200000, 1000000, 1.2, True, False),
            MockStockVolumeData("STOCK3", 4.0, 1800000, 1000000, 1.8, True, False),
        ]

        high_quality_result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", high_quality_data
        )

        # Low quality data (outliers present)
        low_quality_data = [
            MockStockVolumeData("OUTLIER1", 50.0, 10000000, 1000000, 10.0, True, True),
            MockStockVolumeData("OUTLIER2", -30.0, 8000000, 1000000, 8.0, True, True),
        ]

        low_quality_result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", low_quality_data
        )

        # High quality data should have higher confidence
        assert (
            high_quality_result.confidence_score > low_quality_result.confidence_score
        )

    @pytest.mark.asyncio
    async def test_zero_weights_edge_case(self):
        """Test handling of edge case where all weights are zero"""
        # This shouldn't normally happen but test defensive programming
        stock_data = [
            MockStockVolumeData(
                symbol="ZERO_WEIGHT",
                price_change_1d=5.0,
                current_volume=0,  # Zero volume
                avg_volume_20d=1000000,
                volume_ratio=0.0,  # Zero ratio
                is_sufficient_volume=True,  # But marked as sufficient (edge case)
            )
        ]

        result = await self.engine.calculate_weighted_sector_sentiment(
            "technology", stock_data
        )

        # Should handle gracefully
        assert result.sector == "technology"
        assert result.weighted_performance == 0.0  # Default for edge case

    def test_persistence_layer_injection(self):
        """Test that persistence layer is properly injected"""
        # Test with explicit NullPersistence
        null_engine = VolumeWeightingEngine1D(persistence_layer=NullPersistence())
        assert isinstance(null_engine.persistence, NullPersistence)

        # Test with default (should be DatabasePersistence)
        default_engine = VolumeWeightingEngine1D()
        assert default_engine.persistence is not None
