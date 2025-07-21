"""
Unit Tests for 1D Volume Weighting Engine - Step 3 Implementation
Tests volume ratio calculations, weighting application, and edge case handling
"""

import pytest
from unittest.mock import patch

from services.volume_weighting_1d import (
    VolumeWeightingEngine1D,
    StockVolumeData,
    WeightedSectorResult,
    VOLUME_RATIO_MIN,
    VOLUME_RATIO_MAX,
    VOLUME_RATIO_CAP,
)


class TestStockVolumeData:
    """Test the StockVolumeData dataclass properties"""

    def test_volume_ratio_normal_scenario(self):
        """Test volume ratio calculation for normal scenarios"""
        # 2x average volume
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=200000,
            avg_volume_20d=100000,
            price_change_1d=2.5,
        )
        assert stock.volume_ratio == 2.0

        # 0.5x average volume
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=50000,
            avg_volume_20d=100000,
            price_change_1d=1.0,
        )
        assert stock.volume_ratio == 0.5

    def test_volume_ratio_edge_cases(self):
        """Test volume ratio calculation for edge cases"""
        # No average volume data
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=100000,
            avg_volume_20d=None,
            price_change_1d=1.0,
        )
        assert stock.volume_ratio == 1.0

        # Zero average volume
        stock = StockVolumeData(
            symbol="TEST", current_volume=100000, avg_volume_20d=0, price_change_1d=1.0
        )
        assert stock.volume_ratio == 1.0

        # Extreme high volume (should be capped)
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=1500000,
            avg_volume_20d=100000,
            price_change_1d=1.0,
        )
        assert stock.volume_ratio == VOLUME_RATIO_MAX

        # Extreme low volume (should be floored)
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=5000,
            avg_volume_20d=100000,
            price_change_1d=1.0,
        )
        assert stock.volume_ratio == VOLUME_RATIO_MIN

    def test_is_sufficient_volume(self):
        """Test volume threshold checking"""
        # Sufficient volume
        stock = StockVolumeData(
            symbol="TEST", current_volume=5000, avg_volume_20d=4000, price_change_1d=1.0
        )
        assert stock.is_sufficient_volume is True

        # Insufficient volume
        stock = StockVolumeData(
            symbol="TEST", current_volume=500, avg_volume_20d=400, price_change_1d=1.0
        )
        assert stock.is_sufficient_volume is False

    def test_is_volume_outlier(self):
        """Test volume outlier detection"""
        # Normal volume
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=200000,
            avg_volume_20d=100000,
            price_change_1d=1.0,
        )
        assert stock.is_volume_outlier is False

        # Outlier volume (6x average > 5x threshold)
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=600000,
            avg_volume_20d=100000,
            price_change_1d=1.0,
        )
        assert stock.is_volume_outlier is True

        # No average volume data
        stock = StockVolumeData(
            symbol="TEST",
            current_volume=600000,
            avg_volume_20d=None,
            price_change_1d=1.0,
        )
        assert stock.is_volume_outlier is False


class TestVolumeWeightingEngine1D:
    """Test the VolumeWeightingEngine1D class"""

    @pytest.fixture
    def engine(self):
        """Create volume weighting engine instance"""
        return VolumeWeightingEngine1D()

    @pytest.fixture
    def sample_stocks_normal(self):
        """Sample stocks with normal volume scenarios"""
        return [
            StockVolumeData("STOCK1", 100000, 80000, 2.5),  # 1.25x volume, +2.5%
            StockVolumeData("STOCK2", 150000, 100000, -1.8),  # 1.5x volume, -1.8%
            StockVolumeData("STOCK3", 200000, 120000, 3.2),  # 1.67x volume, +3.2%
            StockVolumeData("STOCK4", 80000, 100000, 0.5),  # 0.8x volume, +0.5%
        ]

    @pytest.fixture
    def sample_stocks_extreme(self):
        """Sample stocks with extreme volume scenarios"""
        return [
            StockVolumeData("HIGH_VOL", 1000000, 100000, 5.0),  # 10x volume (capped)
            StockVolumeData("LOW_VOL", 5000, 100000, 2.0),  # 0.05x volume (floored)
            StockVolumeData("ZERO_VOL", 0, 100000, 1.0),  # Zero volume
            StockVolumeData("NO_AVG", 100000, None, 3.0),  # No average data
        ]

    @pytest.fixture
    def sample_stocks_insufficient_volume(self):
        """Sample stocks with insufficient volume"""
        return [
            StockVolumeData("LOW1", 500, 400, 2.0),  # Below threshold
            StockVolumeData("LOW2", 800, 600, -1.5),  # Below threshold
        ]

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_normal(
        self, mock_volatility, engine, sample_stocks_normal
    ):
        """Test weighted sector performance calculation with normal data"""
        mock_volatility.return_value = 1.2  # Technology sector multiplier

        result = await engine.calculate_weighted_sector_sentiment(
            "technology", sample_stocks_normal
        )

        # Verify result structure
        assert isinstance(result, WeightedSectorResult)
        assert result.sector == "technology"
        assert result.stock_count == 4
        assert result.volatility_multiplier == 1.2
        assert result.total_weight > 0
        assert 0.0 <= result.confidence_score <= 1.0

        # Verify calculation logic
        # Expected weights: 1.25, 1.5, 1.67, 0.8 (all under cap)
        expected_total_weight = 1.25 + 1.5 + 1.67 + 0.8
        expected_weighted_performance = (
            (2.5 * 1.25) + (-1.8 * 1.5) + (3.2 * 1.67) + (0.5 * 0.8)
        ) / expected_total_weight
        expected_final = expected_weighted_performance * 1.2

        assert abs(result.weighted_performance - expected_final) < 0.01
        assert abs(result.total_weight - expected_total_weight) < 0.01

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_extreme(
        self, mock_volatility, engine, sample_stocks_extreme
    ):
        """Test weighted sector performance with extreme volume scenarios"""
        mock_volatility.return_value = 1.0

        result = await engine.calculate_weighted_sector_sentiment(
            "industrials", sample_stocks_extreme
        )

        # Should handle extreme cases gracefully
        assert result.stock_count == 3  # Zero volume stock excluded
        assert result.outlier_count == 1  # HIGH_VOL is outlier (>5x)
        assert result.total_weight > 0

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_insufficient_volume(
        self, mock_volatility, engine, sample_stocks_insufficient_volume
    ):
        """Test sector calculation with insufficient volume stocks"""
        mock_volatility.return_value = 1.0

        result = await engine.calculate_weighted_sector_sentiment(
            "utilities", sample_stocks_insufficient_volume
        )

        # Should return empty result when no stocks meet volume threshold
        assert result.stock_count == 0
        assert result.weighted_performance == 0.0
        assert result.total_weight == 0.0
        assert result.confidence_score == 0.0

    def test_calculate_volume_weight_normal_scenarios(self, engine):
        """Test volume weight calculation for normal scenarios"""
        # 1x volume
        stock = StockVolumeData("TEST", 100000, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 1.0

        # 2x volume
        stock = StockVolumeData("TEST", 200000, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 2.0

        # 3x volume (at cap)
        stock = StockVolumeData("TEST", 300000, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == VOLUME_RATIO_CAP

    def test_calculate_volume_weight_extreme_scenarios(self, engine):
        """Test volume weight calculation for extreme scenarios"""
        # Zero current volume
        stock = StockVolumeData("TEST", 0, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 0.0

        # Very high volume (should be capped)
        stock = StockVolumeData("TEST", 1500000, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == VOLUME_RATIO_CAP

        # Very low volume (should be floored)
        stock = StockVolumeData("TEST", 5000, 100000, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 0.1  # Minimum weight

    def test_calculate_volume_weight_missing_data(self, engine):
        """Test volume weight calculation with missing data"""
        # No average volume
        stock = StockVolumeData("TEST", 100000, None, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 1.0  # Default to 1.0 when no average

        # Zero average volume
        stock = StockVolumeData("TEST", 100000, 0, 1.0)
        weight = engine._calculate_volume_weight(stock)
        assert weight == 1.0

    def test_calculate_confidence_score_high_quality(self, engine):
        """Test confidence calculation with high quality data"""
        # Many stocks, no outliers, good data
        valid_stocks = [
            StockVolumeData(f"STOCK{i}", 100000, 90000, 1.0)
            for i in range(25)  # 25 stocks for high count factor
        ]

        confidence = engine._calculate_confidence_score(valid_stocks, 0, 25.0)
        assert confidence > 0.8  # Should be high confidence

    def test_calculate_confidence_score_low_quality(self, engine):
        """Test confidence calculation with low quality data"""
        # Few stocks, many outliers, poor data
        valid_stocks = [
            StockVolumeData("STOCK1", 100000, None, 1.0),  # No avg volume
            StockVolumeData("STOCK2", 500000, 100000, 2.0),  # Outlier
        ]

        confidence = engine._calculate_confidence_score(valid_stocks, 1, 2.0)
        assert confidence < 0.5  # Should be low confidence

    def test_validate_volume_data_valid_stocks(self, engine):
        """Test volume data validation with valid stocks"""
        stocks = [
            StockVolumeData("AAPL", 100000, 90000, 2.5),
            StockVolumeData("MSFT", 150000, 120000, -1.8),
        ]

        valid_stocks, errors = engine.validate_volume_data(stocks)

        assert len(valid_stocks) == 2
        assert len(errors) == 0

    def test_validate_volume_data_invalid_stocks(self, engine):
        """Test volume data validation with invalid stocks"""
        stocks = [
            StockVolumeData("", 100000, 90000, 2.5),  # Empty symbol
            StockVolumeData("NEG", -50000, 90000, 1.0),  # Negative volume
            StockVolumeData("EXTREME", 100000, 90000, 75.0),  # Extreme price change
        ]

        valid_stocks, errors = engine.validate_volume_data(stocks)

        assert len(valid_stocks) == 1  # Only EXTREME (included despite warning)
        assert len(errors) == 3  # All have errors
        assert "missing symbol" in errors[0]
        assert "Negative volume" in errors[1]
        assert "Extreme price change" in errors[2]

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    def test_create_empty_result(self, mock_volatility, engine):
        """Test creation of empty result"""
        mock_volatility.return_value = 1.1

        result = engine._create_empty_result("financial")

        assert result.sector == "financial"
        assert result.weighted_performance == 0.0
        assert result.total_weight == 0.0
        assert result.stock_count == 0
        assert result.outlier_count == 0
        assert result.volatility_multiplier == 1.1
        assert result.confidence_score == 0.0


class TestVolumeWeightingMathematicalProperties:
    """Test mathematical properties and invariants of volume weighting"""

    @pytest.fixture
    def engine(self):
        return VolumeWeightingEngine1D()

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    def test_volume_weight_bounds_property(self, mock_volatility, engine):
        """Test that volume weights are always within expected bounds"""
        mock_volatility.return_value = 1.0

        # Test various volume ratios
        test_cases = [
            (50000, 100000),  # 0.5x
            (100000, 100000),  # 1.0x
            (300000, 100000),  # 3.0x (at cap)
            (500000, 100000),  # 5.0x (exceeds cap)
            (0, 100000),  # 0x (special case)
        ]

        for current_vol, avg_vol in test_cases:
            stock = StockVolumeData("TEST", current_vol, avg_vol, 1.0)
            weight = engine._calculate_volume_weight(stock)

            # Volume weight should be between 0 and cap (except for zero volume)
            if current_vol == 0:
                assert weight == 0.0
            else:
                assert 0.1 <= weight <= VOLUME_RATIO_CAP

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    @pytest.mark.asyncio
    async def test_confidence_score_bounds_property(self, mock_volatility, engine):
        """Test that confidence scores are always between 0 and 1"""
        mock_volatility.return_value = 1.0

        # Test extreme scenarios
        test_cases = [
            [],  # Empty list
            [StockVolumeData("TEST", 100000, 90000, 1.0)],  # Single stock
            [
                StockVolumeData(f"STOCK{i}", 100000, 90000, 1.0) for i in range(50)
            ],  # Many stocks
        ]

        for stocks in test_cases:
            result = await engine.calculate_weighted_sector_sentiment("test", stocks)
            assert 0.0 <= result.confidence_score <= 1.0

    @patch("services.volume_weighting_1d.get_weight_for_sector")
    @pytest.mark.asyncio
    async def test_weighted_performance_linearity(self, mock_volatility, engine):
        """Test that doubling all price changes doubles the weighted performance"""
        mock_volatility.return_value = 1.0

        stocks_base = [
            StockVolumeData("STOCK1", 100000, 100000, 2.0),
            StockVolumeData("STOCK2", 150000, 100000, -1.0),
        ]

        stocks_doubled = [
            StockVolumeData("STOCK1", 100000, 100000, 4.0),
            StockVolumeData("STOCK2", 150000, 100000, -2.0),
        ]

        result_base = await engine.calculate_weighted_sector_sentiment(
            "test", stocks_base
        )
        result_doubled = await engine.calculate_weighted_sector_sentiment(
            "test", stocks_doubled
        )

        # Should be approximately 2x (within floating point precision)
        assert (
            abs(
                result_doubled.weighted_performance
                - (2 * result_base.weighted_performance)
            )
            < 0.01
        )
