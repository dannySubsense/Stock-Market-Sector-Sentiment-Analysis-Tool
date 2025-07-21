"""
Unit Tests for 1D Sector Performance Calculator
Tests mathematical formulas and edge cases defined in specification
"""

import pytest
from datetime import datetime
from services.sector_performance_1d import (
    SectorPerformanceCalculator1D,
    StockData1D,
    SectorPerformance1D,
)


class TestSectorPerformanceCalculator1D:
    """Test class for 1D sector performance calculations"""

    @pytest.fixture
    def calculator(self):
        """Create calculator with test volatility multipliers"""
        volatility_multipliers = {
            "technology": 1.3,
            "healthcare": 1.5,
            "energy": 1.2,
            "financial": 1.1,
            "consumer_discretionary": 1.1,
            "industrials": 1.0,
            "materials": 1.2,
            "utilities": 0.7,
            "real_estate": 0.9,
            "consumer_defensive": 0.8,
            "communication_services": 1.0,
        }
        return SectorPerformanceCalculator1D(volatility_multipliers)

    @pytest.fixture
    def sample_stock_data(self):
        """Sample stock data for testing"""
        return [
            StockData1D(
                symbol="SOUN",
                current_price=5.00,
                previous_close=4.50,
                current_volume=2000000,
                avg_20_day_volume=1000000,
                sector="technology",
            ),
            StockData1D(
                symbol="BBAI",
                current_price=3.60,
                previous_close=4.00,
                current_volume=1500000,
                avg_20_day_volume=1500000,
                sector="technology",
            ),
        ]

    def test_calculate_stock_performance_basic(self, calculator):
        """Test basic stock performance calculation"""
        stock_data = StockData1D(
            symbol="TEST",
            current_price=110.0,
            previous_close=100.0,
            current_volume=1000000,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        performance = calculator.calculate_stock_performance(stock_data)
        expected = 10.0  # (110 - 100) / 100 * 100 = 10%

        assert performance == expected
        assert isinstance(performance, float)

    def test_calculate_stock_performance_negative(self, calculator):
        """Test negative stock performance calculation"""
        stock_data = StockData1D(
            symbol="TEST",
            current_price=90.0,
            previous_close=100.0,
            current_volume=1000000,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        performance = calculator.calculate_stock_performance(stock_data)
        expected = -10.0  # (90 - 100) / 100 * 100 = -10%

        assert performance == expected

    def test_calculate_stock_performance_extreme_capping(self, calculator):
        """Test extreme performance capping at ±50%"""
        # Test extreme positive case
        extreme_positive = StockData1D(
            symbol="EXTREME_UP",
            current_price=15.0,
            previous_close=2.0,
            current_volume=1000000,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        performance = calculator.calculate_stock_performance(extreme_positive)
        # Raw: (15 - 2) / 2 * 100 = 650% -> Capped at 50%
        assert performance == 50.0

        # Test extreme negative case
        extreme_negative = StockData1D(
            symbol="EXTREME_DOWN",
            current_price=1.0,
            previous_close=10.0,
            current_volume=1000000,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        performance = calculator.calculate_stock_performance(extreme_negative)
        # Raw: (1 - 10) / 10 * 100 = -90% -> Capped at -50%
        assert performance == -50.0

    def test_calculate_stock_performance_precision(self, calculator):
        """Test mathematical accuracy to 3 decimal places"""
        stock_data = StockData1D(
            symbol="PRECISION",
            current_price=33.333,
            previous_close=30.0,
            current_volume=1000000,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        performance = calculator.calculate_stock_performance(stock_data)
        expected = 11.110  # (33.333 - 30) / 30 * 100 = 11.11%

        assert performance == expected

    def test_calculate_stock_performance_invalid_inputs(self, calculator):
        """Test validation of invalid inputs"""
        # Test zero current price
        with pytest.raises(ValueError, match="Invalid current price"):
            calculator.calculate_stock_performance(
                StockData1D(
                    symbol="INVALID",
                    current_price=0.0,
                    previous_close=10.0,
                    current_volume=1000000,
                    avg_20_day_volume=1000000,
                    sector="technology",
                )
            )

        # Test zero previous close
        with pytest.raises(ValueError, match="Invalid previous close"):
            calculator.calculate_stock_performance(
                StockData1D(
                    symbol="INVALID",
                    current_price=10.0,
                    previous_close=0.0,
                    current_volume=1000000,
                    avg_20_day_volume=1000000,
                    sector="technology",
                )
            )

    def test_calculate_volume_weight_normal(self, calculator):
        """Test normal volume weight calculation"""
        stock_data = StockData1D(
            symbol="NORMAL",
            current_price=10.0,
            previous_close=9.0,
            current_volume=2000000,  # 2x average
            avg_20_day_volume=1000000,
            sector="technology",
        )

        weight = calculator.calculate_volume_weight(stock_data)
        expected = 2.0  # 2000000 / 1000000 = 2.0

        assert weight == expected

    def test_calculate_volume_weight_extreme_values(self, calculator):
        """Test volume weight capping at 0.1x and 10.0x"""
        # Test extreme high volume (should cap at 10.0)
        high_volume = StockData1D(
            symbol="HIGH_VOL",
            current_price=10.0,
            previous_close=9.0,
            current_volume=50000000,  # 50x average
            avg_20_day_volume=1000000,
            sector="technology",
        )

        weight = calculator.calculate_volume_weight(high_volume)
        assert weight == 10.0  # Capped at max

        # Test extreme low volume (should cap at 0.1)
        low_volume = StockData1D(
            symbol="LOW_VOL",
            current_price=10.0,
            previous_close=9.0,
            current_volume=10000,  # 0.01x average
            avg_20_day_volume=1000000,
            sector="technology",
        )

        weight = calculator.calculate_volume_weight(low_volume)
        assert weight == 0.1  # Capped at min

    def test_calculate_volume_weight_edge_cases(self, calculator):
        """Test volume weight edge cases"""
        # Test zero current volume
        zero_volume = StockData1D(
            symbol="ZERO_VOL",
            current_price=10.0,
            previous_close=9.0,
            current_volume=0,
            avg_20_day_volume=1000000,
            sector="technology",
        )

        weight = calculator.calculate_volume_weight(zero_volume)
        assert weight == 1.0  # Neutral weight for zero volume

        # Test zero average volume
        zero_avg = StockData1D(
            symbol="ZERO_AVG",
            current_price=10.0,
            previous_close=9.0,
            current_volume=1000000,
            avg_20_day_volume=0,
            sector="technology",
        )

        weight = calculator.calculate_volume_weight(zero_avg)
        assert weight == 1.0  # Neutral weight for zero average

    def test_calculate_sector_aggregation_from_specification(self, calculator):
        """Test sector aggregation with exact example from specification"""
        # Test Case 1 from specification document
        stocks_data = [
            StockData1D(
                symbol="SOUN",
                current_price=5.00,
                previous_close=4.50,
                current_volume=2000000,
                avg_20_day_volume=1000000,
                sector="technology",
            ),
            StockData1D(
                symbol="BBAI",
                current_price=3.60,
                previous_close=4.00,
                current_volume=1500000,
                avg_20_day_volume=1500000,
                sector="technology",
            ),
        ]

        sector_performance, metadata = calculator.calculate_sector_aggregation(
            stocks_data, "technology"
        )

        # Expected calculation from specification:
        # SOUN: +11.11% * 2.0 weight = +22.22% weighted
        # BBAI: -10.00% * 1.0 weight = -10.00% weighted
        # Sector: (22.22 + -10.00) / (2.0 + 1.0) = +4.07% raw
        # Final: +4.07% * 1.3 = +5.29%
        expected = 5.291  # With rounding

        assert (
            abs(sector_performance - expected) < 0.01
        )  # Allow small rounding differences
        assert metadata["valid_stocks"] == 2
        assert metadata["volatility_multiplier"] == 1.3

    def test_calculate_iwm_benchmark(self, calculator):
        """Test IWM benchmark calculation"""
        iwm_current = 200.0
        iwm_previous = 198.0

        iwm_performance = calculator.calculate_iwm_benchmark(iwm_current, iwm_previous)
        expected = 1.010  # (200 - 198) / 198 * 100 = 1.010%

        assert abs(iwm_performance - expected) < 0.001

    def test_calculate_iwm_benchmark_invalid_inputs(self, calculator):
        """Test IWM benchmark with invalid inputs"""
        with pytest.raises(ValueError, match="Invalid IWM previous close"):
            calculator.calculate_iwm_benchmark(200.0, 0.0)

        with pytest.raises(ValueError, match="Invalid IWM current price"):
            calculator.calculate_iwm_benchmark(0.0, 198.0)

    def test_classify_relative_strength(self, calculator):
        """Test relative strength classification"""
        # Test all classification ranges
        assert calculator.classify_relative_strength(3.0) == "STRONG_OUTPERFORM"
        assert calculator.classify_relative_strength(1.0) == "OUTPERFORM"
        assert calculator.classify_relative_strength(0.0) == "NEUTRAL"
        assert calculator.classify_relative_strength(-1.0) == "UNDERPERFORM"
        assert calculator.classify_relative_strength(-3.0) == "STRONG_UNDERPERFORM"

        # Test boundary conditions
        assert (
            calculator.classify_relative_strength(2.0) == "OUTPERFORM"
        )  # Exactly at threshold
        assert (
            calculator.classify_relative_strength(0.5) == "NEUTRAL"
        )  # Exactly at threshold
        assert (
            calculator.classify_relative_strength(-0.5) == "UNDERPERFORM"
        )  # Exactly at threshold
        assert (
            calculator.classify_relative_strength(-2.0) == "STRONG_UNDERPERFORM"
        )  # Exactly at threshold

    def test_calculate_confidence(self, calculator):
        """Test confidence calculation"""
        # High quality data
        high_quality = {"data_coverage": 1.0, "valid_stocks": 10}
        confidence = calculator.calculate_confidence(high_quality)
        assert confidence == 1.0

        # Low quality data
        low_quality = {"data_coverage": 0.5, "valid_stocks": 1}
        confidence = calculator.calculate_confidence(low_quality)
        expected = (0.5 * 0.7) + (1 / 3 * 0.3)  # 0.35 + 0.1 = 0.45
        assert abs(confidence - 0.45) < 0.01

    def test_calculate_sector_performance_1d_complete(
        self, calculator, sample_stock_data
    ):
        """Test complete 1D sector performance calculation"""
        iwm_current = 200.0
        iwm_previous = 198.0

        result = calculator.calculate_sector_performance_1d(
            sample_stock_data, "technology", iwm_current, iwm_previous
        )

        # Verify result structure
        assert isinstance(result, SectorPerformance1D)
        assert result.sector_name == "technology"
        assert isinstance(result.performance_1d, float)
        assert isinstance(result.iwm_benchmark, float)
        assert isinstance(result.alpha, float)
        assert result.relative_strength in [
            "STRONG_OUTPERFORM",
            "OUTPERFORM",
            "NEUTRAL",
            "UNDERPERFORM",
            "STRONG_UNDERPERFORM",
        ]
        assert 0.0 <= result.confidence <= 1.0
        assert result.stock_count == 2
        assert result.calculation_time >= 0  # Allow 0 for very fast calculations

    def test_volatility_multiplier_validation(self):
        """Test volatility multiplier validation"""
        # Test valid multipliers
        valid_multipliers = {"sector1": 1.0, "sector2": 0.5, "sector3": 2.0}
        calculator = SectorPerformanceCalculator1D(valid_multipliers)
        assert calculator.volatility_multipliers == valid_multipliers

        # Test invalid multipliers
        with pytest.raises(ValueError, match="outside range 0.5-2.0"):
            SectorPerformanceCalculator1D({"invalid": 0.3})  # Too low

        with pytest.raises(ValueError, match="outside range 0.5-2.0"):
            SectorPerformanceCalculator1D({"invalid": 2.5})  # Too high

    def test_edge_case_empty_stocks_list(self, calculator):
        """Test handling of empty stocks list"""
        result, metadata = calculator.calculate_sector_aggregation([], "technology")

        assert result == 0.0
        assert "error" in metadata

    def test_edge_case_all_invalid_stocks(self, calculator):
        """Test handling when all stocks have invalid data"""
        invalid_stocks = [
            StockData1D(
                symbol="INVALID1",
                current_price=0.0,  # Invalid price
                previous_close=10.0,
                current_volume=1000000,
                avg_20_day_volume=1000000,
                sector="technology",
            )
        ]

        result, metadata = calculator.calculate_sector_aggregation(
            invalid_stocks, "technology"
        )

        assert result == 0.0
        assert "error" in metadata
