"""
Unit Tests for 1D Sector Aggregation Service
Tests Step 5 functionality: sector mapping, aggregation, classification, and quality assessment
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any

from services.sector_aggregation_1d import (
    SectorAggregation1D,
    SectorStockMapping,
    SectorSentimentResult,
    DataQualityAssessment,
    ColorClassification,
    TRADING_SIGNALS,
)
from services.sector_performance_1d import StockData1D
from models.stock_universe import StockUniverse


class TestSectorAggregation1D:
    """Test class for 1D sector aggregation service"""

    @pytest.fixture
    def mock_persistence(self):
        """Mock persistence layer for testing"""
        mock_persistence = Mock()
        mock_persistence.store_sector_sentiment_1d = AsyncMock(return_value=True)
        return mock_persistence

    @pytest.fixture
    def aggregation_service(self, mock_persistence):
        """Create aggregation service with mocked dependencies"""
        with patch("services.sector_aggregation_1d.SessionLocal"), patch(
            "services.sector_aggregation_1d.get_iwm_service"
        ), patch("services.sector_aggregation_1d.get_static_weights") as mock_weights:

            mock_weights.return_value = {
                "technology": 1.3,
                "healthcare": 1.5,
                "energy": 1.2,
            }

            service = SectorAggregation1D(persistence_layer=mock_persistence)
            return service

    @pytest.fixture
    def sample_stock_universe(self):
        """Sample stock universe data for testing"""
        return [
            Mock(
                symbol="SOUN",
                sector="technology",
                is_active=True,
                market_cap=180_000_000,
                avg_daily_volume=2_000_000,
            ),
            Mock(
                symbol="BBAI",
                sector="technology",
                is_active=True,
                market_cap=120_000_000,
                avg_daily_volume=1_500_000,
            ),
            Mock(
                symbol="OCUL",
                sector="healthcare",
                is_active=True,
                market_cap=200_000_000,
                avg_daily_volume=1_800_000,
            ),
        ]

    @pytest.fixture
    def sample_stock_data_1d(self):
        """Sample 1D stock data for testing"""
        return [
            StockData1D(
                symbol="SOUN",
                current_price=5.00,
                previous_close=4.50,
                current_volume=2_000_000,
                avg_20_day_volume=1_000_000,
                sector="technology",
            ),
            StockData1D(
                symbol="BBAI",
                current_price=3.60,
                previous_close=4.00,
                current_volume=1_500_000,
                avg_20_day_volume=1_500_000,
                sector="technology",
            ),
        ]

    def test_get_sector_stocks_success(
        self, aggregation_service, sample_stock_universe
    ):
        """Test successful stock-to-sector mapping"""
        # Mock database query
        with patch("services.sector_aggregation_1d.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Setup query mocks
            tech_stocks = [
                stock for stock in sample_stock_universe if stock.sector == "technology"
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = (
                tech_stocks
            )
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
                tech_stocks
            )

            # Test the method
            result = asyncio.run(aggregation_service.get_sector_stocks("technology"))

            # Verify result
            assert isinstance(result, SectorStockMapping)
            assert result.sector == "technology"
            assert len(result.symbols) == 2
            assert "SOUN" in result.symbols
            assert "BBAI" in result.symbols
            assert result.active_stocks == 2
            assert result.coverage_percentage == 100.0

    def test_get_sector_stocks_empty_sector(self, aggregation_service):
        """Test sector mapping with no stocks"""
        with patch("services.sector_aggregation_1d.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock empty results
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = (
                []
            )

            result = asyncio.run(aggregation_service.get_sector_stocks("empty_sector"))

            assert result.sector == "empty_sector"
            assert len(result.symbols) == 0
            assert result.active_stocks == 0
            assert result.coverage_percentage == 0.0

    @pytest.mark.asyncio
    async def test_retrieve_stock_data_1d_success(
        self, aggregation_service, sample_stock_data_1d
    ):
        """Test successful stock data retrieval using Step 2 service"""
        # Mock Step 2 service
        aggregation_service.data_retrieval.get_1d_stock_data = AsyncMock()
        aggregation_service.data_retrieval.get_1d_stock_data.side_effect = (
            sample_stock_data_1d
        )

        symbols = ["SOUN", "BBAI"]
        result = await aggregation_service.retrieve_stock_data_1d(symbols)

        assert len(result) == 2
        assert all(isinstance(stock, StockData1D) for stock in result)
        assert result[0].symbol == "SOUN"
        assert result[1].symbol == "BBAI"

    @pytest.mark.asyncio
    async def test_retrieve_stock_data_1d_partial_failure(
        self, aggregation_service, sample_stock_data_1d
    ):
        """Test stock data retrieval with some API failures"""
        # Mock partial failure
        aggregation_service.data_retrieval.get_1d_stock_data = AsyncMock()
        aggregation_service.data_retrieval.get_1d_stock_data.side_effect = [
            sample_stock_data_1d[0],  # Success
            None,  # Failure
            sample_stock_data_1d[1],  # Success
        ]

        symbols = ["SOUN", "FAILED", "BBAI"]
        result = await aggregation_service.retrieve_stock_data_1d(symbols)

        assert len(result) == 2  # Only successful retrievals
        assert result[0].symbol == "SOUN"
        assert result[1].symbol == "BBAI"

    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_success(
        self, aggregation_service, sample_stock_data_1d
    ):
        """Test weighted sector performance calculation"""
        # Mock IWM service
        mock_iwm_data = Mock()
        mock_iwm_data.performance_1d = 1.5
        mock_iwm_data.confidence = 0.9
        aggregation_service.iwm_service.get_cached_iwm_benchmark_1d = AsyncMock(
            return_value=mock_iwm_data
        )
        aggregation_service.iwm_service.calculate_sector_alpha = Mock(return_value=3.8)
        aggregation_service.iwm_service.classify_relative_strength = Mock(
            return_value="OUTPERFORM"
        )

        # Mock Step 1 performance calculator
        aggregation_service.performance_calculator.calculate_sector_aggregation = Mock(
            return_value=(
                5.3,
                {
                    "volatility_multiplier": 1.3,
                    "avg_volume_weight": 1.8,
                    "data_coverage": 0.9,
                },
            )
        )

        result = await aggregation_service.calculate_weighted_sector_performance(
            "technology", sample_stock_data_1d
        )

        assert result["sector_performance_1d"] == 5.3
        assert result["iwm_benchmark_1d"] == 1.5
        assert result["alpha"] == 3.8
        assert result["relative_strength"] == "OUTPERFORM"
        assert result["metadata"]["volatility_multiplier"] == 1.3

    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_empty_data(
        self, aggregation_service
    ):
        """Test weighted performance calculation with no stock data"""
        result = await aggregation_service.calculate_weighted_sector_performance(
            "technology", []
        )

        assert result["sector_performance_1d"] == 0.0
        assert result["iwm_benchmark_1d"] == 0.0
        assert result["alpha"] == 0.0
        assert result["relative_strength"] == "NEUTRAL"

    def test_classify_sector_sentiment_bullish(self, aggregation_service):
        """Test sentiment classification for bullish scenario"""
        # Test strong bullish (alpha > 6%)
        result = aggregation_service.classify_sector_sentiment(8.5, 6.2)

        assert result["sentiment_score"] > 0.6  # Should be in dark green range
        assert result["color_classification"] == ColorClassification.DARK_GREEN
        assert result["trading_signal"] == "DO_NOT_SHORT"

    def test_classify_sector_sentiment_bearish(self, aggregation_service):
        """Test sentiment classification for bearish scenario"""
        # Test strong bearish (alpha < -6%)
        result = aggregation_service.classify_sector_sentiment(-8.2, -7.5)

        assert result["sentiment_score"] < -0.6  # Should be in dark red range
        assert result["color_classification"] == ColorClassification.DARK_RED
        assert result["trading_signal"] == "PRIME_SHORTING_ENVIRONMENT"

    def test_classify_sector_sentiment_neutral(self, aggregation_service):
        """Test sentiment classification for neutral scenario"""
        # Test neutral (small alpha)
        result = aggregation_service.classify_sector_sentiment(1.2, 0.8)

        assert -0.2 <= result["sentiment_score"] <= 0.2
        assert result["color_classification"] == ColorClassification.BLUE_NEUTRAL
        assert result["trading_signal"] == "NEUTRAL_CAUTIOUS"

    def test_assess_data_quality_high_quality(
        self, aggregation_service, sample_stock_data_1d
    ):
        """Test data quality assessment with high quality data"""
        sector_mapping = SectorStockMapping(
            sector="technology",
            symbols=[
                "SOUN",
                "BBAI",
                "PATH",
                "OCUL",
                "SMCI",
                "NVDA",
            ],  # 6 stocks for high confidence
            total_stocks=6,
            active_stocks=6,
            coverage_percentage=100.0,
        )

        # Extend sample data for 6 stocks
        extended_stock_data = sample_stock_data_1d + [
            StockData1D(
                symbol="PATH",
                current_price=10.0,
                previous_close=9.5,
                current_volume=1000000,
                avg_20_day_volume=800000,
                sector="technology",
            ),
            StockData1D(
                symbol="OCUL",
                current_price=15.0,
                previous_close=14.8,
                current_volume=900000,
                avg_20_day_volume=750000,
                sector="technology",
            ),
            StockData1D(
                symbol="SMCI",
                current_price=50.0,
                previous_close=52.0,
                current_volume=2000000,
                avg_20_day_volume=1500000,
                sector="technology",
            ),
            StockData1D(
                symbol="NVDA",
                current_price=120.0,
                previous_close=118.0,
                current_volume=3000000,
                avg_20_day_volume=2500000,
                sector="technology",
            ),
        ]

        performance_metadata = {
            "data_coverage": 0.95,
            "volatility_multiplier": 1.3,
            "valid_stocks": 6,
        }

        result = aggregation_service.assess_data_quality(
            sector_mapping, extended_stock_data, performance_metadata
        )

        assert isinstance(result, DataQualityAssessment)
        assert result.sector == "technology"
        assert result.api_success_count == 6
        assert result.data_coverage == 1.0  # 6/6 = 100%
        assert result.confidence_score > 0.8  # High confidence with 6+ stocks
        assert len(result.quality_flags) == 0  # No issues with 6+ stocks

    def test_assess_data_quality_low_quality(self, aggregation_service):
        """Test data quality assessment with low quality data"""
        sector_mapping = SectorStockMapping(
            sector="technology",
            symbols=["SOUN"],
            total_stocks=10,
            active_stocks=10,
            coverage_percentage=100.0,
        )

        stock_data_list = []  # No data retrieved
        performance_metadata = {"data_coverage": 0.1}

        result = aggregation_service.assess_data_quality(
            sector_mapping, stock_data_list, performance_metadata
        )

        assert result.data_coverage == 0.0  # 0/10 = 0%
        assert result.confidence_score < 0.3  # Low confidence
        assert "INSUFFICIENT_STOCKS" in result.quality_flags
        assert "LOW_DATA_COVERAGE" in result.quality_flags

    def test_normalize_to_sentiment_score(self, aggregation_service):
        """Test alpha to sentiment score normalization"""
        # Test linear range (within ±10%)
        assert aggregation_service._normalize_to_sentiment_score(5.0) == 0.5
        assert aggregation_service._normalize_to_sentiment_score(-5.0) == -0.5
        assert aggregation_service._normalize_to_sentiment_score(10.0) == 1.0
        assert aggregation_service._normalize_to_sentiment_score(-10.0) == -1.0

        # Test zero
        assert aggregation_service._normalize_to_sentiment_score(0.0) == 0.0

        # Test extreme values (should be compressed but still capped at ±1.0)
        extreme_positive = aggregation_service._normalize_to_sentiment_score(50.0)
        extreme_negative = aggregation_service._normalize_to_sentiment_score(-50.0)
        assert 0.8 <= extreme_positive <= 1.0
        assert -1.0 <= extreme_negative <= -0.8

    def test_classify_sentiment_color_boundary_cases(self, aggregation_service):
        """Test color classification boundary cases"""
        # Test exact boundaries (ranges are [min, max) except for 1.0)
        assert (
            aggregation_service._classify_sentiment_color(-0.6)
            == ColorClassification.LIGHT_RED
        )  # -0.6 is start of LIGHT_RED range
        assert (
            aggregation_service._classify_sentiment_color(-0.7)
            == ColorClassification.DARK_RED
        )  # -0.7 is in DARK_RED range
        assert (
            aggregation_service._classify_sentiment_color(-0.2)
            == ColorClassification.BLUE_NEUTRAL
        )  # -0.2 is start of NEUTRAL range
        assert (
            aggregation_service._classify_sentiment_color(0.0)
            == ColorClassification.BLUE_NEUTRAL
        )
        assert (
            aggregation_service._classify_sentiment_color(0.2)
            == ColorClassification.LIGHT_GREEN
        )  # 0.2 is start of LIGHT_GREEN range
        assert (
            aggregation_service._classify_sentiment_color(0.6)
            == ColorClassification.DARK_GREEN
        )  # 0.6 is start of DARK_GREEN range

        # Test edge case for exactly 1.0 (special handling)
        assert (
            aggregation_service._classify_sentiment_color(1.0)
            == ColorClassification.DARK_GREEN
        )

        # Test extreme negative (start of DARK_RED range)
        assert (
            aggregation_service._classify_sentiment_color(-1.0)
            == ColorClassification.DARK_RED
        )

    @pytest.mark.asyncio
    async def test_aggregate_sector_sentiment_1d_complete_success(
        self, aggregation_service, sample_stock_data_1d
    ):
        """Test complete 1D sector aggregation workflow"""
        # Mock all dependencies for successful flow

        # Mock sector mapping
        sector_mapping = SectorStockMapping(
            sector="technology",
            symbols=["SOUN", "BBAI"],
            total_stocks=2,
            active_stocks=2,
            coverage_percentage=100.0,
        )
        aggregation_service.get_sector_stocks = AsyncMock(return_value=sector_mapping)

        # Mock data retrieval
        aggregation_service.retrieve_stock_data_1d = AsyncMock(
            return_value=sample_stock_data_1d
        )

        # Mock performance calculation
        performance_result = {
            "sector_performance_1d": 5.3,
            "iwm_benchmark_1d": 1.5,
            "alpha": 3.8,
            "relative_strength": "OUTPERFORM",
            "metadata": {
                "volatility_multiplier": 1.3,
                "avg_volume_weight": 1.8,
                "data_coverage": 0.9,
            },
        }
        aggregation_service.calculate_weighted_sector_performance = AsyncMock(
            return_value=performance_result
        )

        # Mock sentiment classification
        sentiment_result = {
            "sentiment_score": 0.38,
            "color_classification": ColorClassification.LIGHT_GREEN,
            "trading_signal": "AVOID_SHORTS",
        }
        aggregation_service.classify_sector_sentiment = Mock(
            return_value=sentiment_result
        )

        # Mock quality assessment
        quality_assessment = DataQualityAssessment(
            sector="technology",
            total_universe_stocks=2,
            api_success_count=2,
            valid_data_count=2,
            data_coverage=1.0,
            confidence_score=0.9,
            quality_flags=[],
            recommendations=[],
        )
        aggregation_service.assess_data_quality = Mock(return_value=quality_assessment)

        # Execute complete workflow
        result = await aggregation_service.aggregate_sector_sentiment_1d("technology")

        # Verify result structure and content
        assert isinstance(result, SectorSentimentResult)
        assert result.sector == "technology"
        assert result.timeframe == "1D"
        assert result.sentiment_score == 0.38
        assert result.sector_performance_1d == 5.3
        assert result.iwm_benchmark_1d == 1.5
        assert result.alpha == 3.8
        assert result.color_classification == ColorClassification.LIGHT_GREEN
        assert result.trading_signal == "AVOID_SHORTS"
        assert result.relative_strength == "OUTPERFORM"
        assert result.stock_count == 2
        assert result.data_coverage == 1.0
        assert result.confidence_level == 0.9
        assert result.calculation_time >= 0.0

    @pytest.mark.asyncio
    async def test_aggregate_sector_sentiment_1d_no_stocks(self, aggregation_service):
        """Test complete workflow with no stocks in sector"""
        # Mock empty sector mapping
        empty_mapping = SectorStockMapping(
            sector="empty_sector",
            symbols=[],
            total_stocks=0,
            active_stocks=0,
            coverage_percentage=0.0,
        )
        aggregation_service.get_sector_stocks = AsyncMock(return_value=empty_mapping)

        result = await aggregation_service.aggregate_sector_sentiment_1d("empty_sector")

        # Should return empty result
        assert result.sector == "empty_sector"
        assert result.sentiment_score == 0.0
        assert result.stock_count == 0
        assert result.confidence_level == 0.0
        assert result.color_classification == ColorClassification.BLUE_NEUTRAL

    @pytest.mark.asyncio
    async def test_aggregate_sector_sentiment_1d_api_failures(
        self, aggregation_service
    ):
        """Test complete workflow with API data retrieval failures"""
        # Mock sector mapping with stocks
        sector_mapping = SectorStockMapping(
            sector="technology",
            symbols=["SOUN", "BBAI"],
            total_stocks=2,
            active_stocks=2,
            coverage_percentage=100.0,
        )
        aggregation_service.get_sector_stocks = AsyncMock(return_value=sector_mapping)

        # Mock failed data retrieval
        aggregation_service.retrieve_stock_data_1d = AsyncMock(return_value=[])

        result = await aggregation_service.aggregate_sector_sentiment_1d("technology")

        # Should return empty result due to no valid data
        assert result.sector == "technology"
        assert result.sentiment_score == 0.0
        assert result.stock_count == 0
        assert result.confidence_level == 0.0

    def test_validate_stock_data_valid(self, aggregation_service):
        """Test stock data validation with valid data"""
        valid_stock = StockData1D(
            symbol="SOUN",
            current_price=5.00,
            previous_close=4.50,
            current_volume=1_000_000,
            avg_20_day_volume=800_000,
            sector="technology",
        )

        assert aggregation_service._validate_stock_data(valid_stock) is True

    def test_validate_stock_data_invalid(self, aggregation_service):
        """Test stock data validation with invalid data"""
        # Test zero current price
        invalid_stock1 = StockData1D(
            symbol="INVALID",
            current_price=0.0,
            previous_close=4.50,
            current_volume=1_000_000,
            avg_20_day_volume=800_000,
            sector="technology",
        )
        assert aggregation_service._validate_stock_data(invalid_stock1) is False

        # Test zero previous close
        invalid_stock2 = StockData1D(
            symbol="INVALID",
            current_price=5.00,
            previous_close=0.0,
            current_volume=1_000_000,
            avg_20_day_volume=800_000,
            sector="technology",
        )
        assert aggregation_service._validate_stock_data(invalid_stock2) is False

        # Test negative volume
        invalid_stock3 = StockData1D(
            symbol="INVALID",
            current_price=5.00,
            previous_close=4.50,
            current_volume=-1000,
            avg_20_day_volume=800_000,
            sector="technology",
        )
        assert aggregation_service._validate_stock_data(invalid_stock3) is False

    def test_calculate_confidence_score_high_quality(self, aggregation_service):
        """Test confidence score calculation with high quality data"""
        performance_metadata = {"data_coverage": 0.95}

        confidence = aggregation_service._calculate_confidence_score(
            api_success_count=10,  # More than minimum
            total_universe_stocks=12,
            data_coverage=0.85,  # Good coverage
            performance_metadata=performance_metadata,
        )

        assert 0.8 <= confidence <= 1.0  # High confidence

    def test_calculate_confidence_score_low_quality(self, aggregation_service):
        """Test confidence score calculation with low quality data"""
        performance_metadata = {"data_coverage": 0.1}

        confidence = aggregation_service._calculate_confidence_score(
            api_success_count=2,  # Below minimum for high confidence
            total_universe_stocks=20,
            data_coverage=0.1,  # Poor coverage
            performance_metadata=performance_metadata,
        )

        assert 0.0 <= confidence <= 0.4  # Low confidence

    @pytest.mark.asyncio
    async def test_persistence_integration(self, aggregation_service, mock_persistence):
        """Test optional persistence integration"""
        result = SectorSentimentResult(
            sector="technology",
            sentiment_score=0.5,
            stock_count=5,
            confidence_level=0.8,
        )

        quality_assessment = DataQualityAssessment(
            sector="technology",
            total_universe_stocks=5,
            api_success_count=5,
            valid_data_count=5,
            data_coverage=1.0,
            confidence_score=0.8,
            quality_flags=[],
            recommendations=[],
        )

        # Test successful persistence
        await aggregation_service._persist_sector_result_if_enabled(
            result, quality_assessment
        )

        # Verify persistence was called
        mock_persistence.store_sector_sentiment.assert_called_once()
        call_args = mock_persistence.store_sector_sentiment.call_args[0][0]
        assert call_args["sector"] == "technology"
        assert call_args["sentiment_score"] == 0.5

    @pytest.mark.asyncio
    async def test_persistence_failure_non_blocking(
        self, aggregation_service, mock_persistence
    ):
        """Test that persistence failures don't break main calculation"""
        result = SectorSentimentResult(sector="technology")
        quality_assessment = DataQualityAssessment(
            sector="technology",
            total_universe_stocks=0,
            api_success_count=0,
            valid_data_count=0,
            data_coverage=0.0,
            confidence_score=0.0,
            quality_flags=[],
            recommendations=[],
        )

        # Mock persistence failure
        mock_persistence.store_sector_sentiment.side_effect = Exception(
            "Database error"
        )

        # Should not raise exception
        await aggregation_service._persist_sector_result_if_enabled(
            result, quality_assessment
        )

        # Verify it was attempted
        mock_persistence.store_sector_sentiment.assert_called_once()

    def test_trading_signals_consistency(self):
        """Test that all color classifications have corresponding trading signals"""
        for color in ColorClassification:
            assert color in TRADING_SIGNALS
            assert isinstance(TRADING_SIGNALS[color], str)
            assert len(TRADING_SIGNALS[color]) > 0

    def test_get_sector_aggregation_1d_singleton(self):
        """Test global service instance singleton pattern"""
        from services.sector_aggregation_1d import get_sector_aggregation_1d

        # Multiple calls should return same instance
        instance1 = get_sector_aggregation_1d()
        instance2 = get_sector_aggregation_1d()

        assert instance1 is instance2
        assert isinstance(instance1, SectorAggregation1D)
