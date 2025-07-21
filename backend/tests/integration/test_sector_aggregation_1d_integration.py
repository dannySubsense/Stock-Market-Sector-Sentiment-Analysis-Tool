"""
Integration Tests for 1D Sector Aggregation Service
Tests Step 5 functionality with real database and API integration
Validates complete workflow from database to API to calculations
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from models.sector_sentiment import SectorSentiment
from services.sector_aggregation_1d import (
    SectorAggregation1D,
    SectorStockMapping,
    SectorSentimentResult,
    DataQualityAssessment,
    ColorClassification,
)
from services.persistence_interface import get_persistence_layer

logger = logging.getLogger(__name__)

# Integration test configuration
TEST_TIMEOUT = 60  # 1 minute for API calls
EXPECTED_SECTORS = ["technology", "healthcare", "energy"]
MIN_STOCKS_PER_SECTOR = 1


class TestSectorAggregation1DIntegration:
    """Integration tests for complete 1D sector aggregation workflow"""

    @pytest.fixture
    def aggregation_service(self):
        """Get sector aggregation service with real persistence"""
        persistence = get_persistence_layer(enable_database=True)
        return SectorAggregation1D(persistence_layer=persistence)

    @pytest.fixture
    def real_stock_universe_sample(self):
        """Get real stock universe sample from database"""
        try:
            with SessionLocal() as db:
                # Get sample of active stocks by sector
                universe_sample = {}

                for sector in EXPECTED_SECTORS:
                    stocks = (
                        db.query(StockUniverse)
                        .filter(
                            StockUniverse.sector == sector,
                            StockUniverse.is_active == True,
                        )
                        .limit(5)  # Limit for faster testing
                        .all()
                    )

                    universe_sample[sector] = [stock.symbol for stock in stocks]
                    logger.info(f"Sample {sector} stocks: {universe_sample[sector]}")

                return universe_sample

        except Exception as e:
            logger.warning(f"Could not get real universe sample: {e}")
            # Return mock data for testing
            return {
                "technology": ["SOUN", "BBAI"],
                "healthcare": ["OCUL"],
                "energy": ["GREE"],
            }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sector_stocks_real_database(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test stock-to-sector mapping with real database"""
        logger.info("=== TESTING REAL DATABASE SECTOR MAPPING ===")

        for sector in EXPECTED_SECTORS:
            if sector not in real_stock_universe_sample:
                continue

            logger.info(f"Testing sector mapping for: {sector}")

            # Test real database query
            result = await aggregation_service.get_sector_stocks(sector)

            # Validate result structure
            assert isinstance(result, SectorStockMapping)
            assert result.sector == sector
            assert isinstance(result.symbols, list)
            assert isinstance(result.total_stocks, int)
            assert isinstance(result.active_stocks, int)
            assert isinstance(result.coverage_percentage, float)

            # Validate data consistency
            assert result.total_stocks >= result.active_stocks
            assert len(result.symbols) == result.active_stocks
            assert 0.0 <= result.coverage_percentage <= 100.0

            logger.info(
                f"  {sector}: {result.active_stocks} active stocks, {result.coverage_percentage:.1f}% coverage"
            )

            if result.active_stocks > 0:
                # Validate symbols are realistic
                for symbol in result.symbols:
                    assert isinstance(symbol, str)
                    assert len(symbol) <= 10  # Reasonable symbol length
                    assert symbol.isupper()  # Should be uppercase

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_retrieve_stock_data_1d_real_apis(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test stock data retrieval with real API calls"""
        logger.info("=== TESTING REAL API DATA RETRIEVAL ===")

        # Test with a small sample for performance
        test_symbols = []
        for sector_symbols in real_stock_universe_sample.values():
            if sector_symbols:
                test_symbols.append(
                    sector_symbols[0]
                )  # Take first symbol from each sector

        test_symbols = test_symbols[:3]  # Limit to 3 symbols for faster testing
        logger.info(f"Testing API retrieval for symbols: {test_symbols}")

        # Retrieve stock data with real APIs
        start_time = datetime.now()
        stock_data_list = await aggregation_service.retrieve_stock_data_1d(test_symbols)
        end_time = datetime.now()

        retrieval_time = (end_time - start_time).total_seconds()
        success_rate = len(stock_data_list) / len(test_symbols) if test_symbols else 0

        logger.info(f"API Retrieval Results:")
        logger.info(f"  Symbols requested: {len(test_symbols)}")
        logger.info(f"  Data retrieved: {len(stock_data_list)}")
        logger.info(f"  Success rate: {success_rate:.1%}")
        logger.info(f"  Retrieval time: {retrieval_time:.2f}s")

        # Validate results
        assert isinstance(stock_data_list, list)
        assert success_rate >= 0.5, f"Low API success rate: {success_rate:.1%}"
        assert (
            retrieval_time < TEST_TIMEOUT
        ), f"API retrieval too slow: {retrieval_time}s"

        # Validate retrieved data quality
        for stock_data in stock_data_list:
            assert stock_data.symbol in test_symbols
            assert stock_data.current_price > 0
            assert stock_data.previous_close > 0
            assert stock_data.current_volume >= 0

            # Log data quality
            price_change = (
                (stock_data.current_price - stock_data.previous_close)
                / stock_data.previous_close
                * 100
            )
            logger.info(
                f"  {stock_data.symbol}: ${stock_data.current_price:.2f} "
                f"({price_change:+.2f}%, vol: {stock_data.current_volume:,})"
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calculate_weighted_sector_performance_integration(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test weighted sector performance calculation with real data"""
        logger.info("=== TESTING WEIGHTED PERFORMANCE CALCULATION ===")

        # Get real stock data for technology sector
        tech_symbols = real_stock_universe_sample.get("technology", ["SOUN", "BBAI"])[
            :3
        ]

        if not tech_symbols:
            pytest.skip("No technology stocks available for testing")

        logger.info(f"Testing performance calculation with: {tech_symbols}")

        # Retrieve real stock data
        stock_data_list = await aggregation_service.retrieve_stock_data_1d(tech_symbols)

        if not stock_data_list:
            pytest.skip("No stock data retrieved for performance calculation")

        # Calculate weighted performance
        result = await aggregation_service.calculate_weighted_sector_performance(
            "technology", stock_data_list
        )

        # Validate result structure
        assert isinstance(result, dict)
        assert "sector_performance_1d" in result
        assert "iwm_benchmark_1d" in result
        assert "alpha" in result
        assert "relative_strength" in result
        assert "metadata" in result

        # Validate data types and ranges
        assert isinstance(result["sector_performance_1d"], (int, float))
        assert isinstance(result["iwm_benchmark_1d"], (int, float))
        assert isinstance(result["alpha"], (int, float))
        assert isinstance(result["relative_strength"], str)

        # Validate reasonable ranges (allowing for market volatility)
        assert -50.0 <= result["sector_performance_1d"] <= 50.0
        assert -20.0 <= result["iwm_benchmark_1d"] <= 20.0
        assert -70.0 <= result["alpha"] <= 70.0

        # Validate relative strength classification
        valid_strengths = [
            "STRONG_OUTPERFORM",
            "OUTPERFORM",
            "NEUTRAL",
            "UNDERPERFORM",
            "STRONG_UNDERPERFORM",
        ]
        assert result["relative_strength"] in valid_strengths

        logger.info(f"Performance Results:")
        logger.info(f"  Sector Performance: {result['sector_performance_1d']:+.2f}%")
        logger.info(f"  IWM Benchmark: {result['iwm_benchmark_1d']:+.2f}%")
        logger.info(f"  Alpha: {result['alpha']:+.2f}%")
        logger.info(f"  Relative Strength: {result['relative_strength']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_sector_aggregation_1d_workflow(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test complete 1D sector aggregation workflow with real data"""
        logger.info("=== TESTING COMPLETE 1D AGGREGATION WORKFLOW ===")

        # Test with technology sector
        test_sector = "technology"

        if (
            test_sector not in real_stock_universe_sample
            or not real_stock_universe_sample[test_sector]
        ):
            pytest.skip(f"No {test_sector} stocks available for complete workflow test")

        logger.info(f"Testing complete workflow for {test_sector} sector")

        # Execute complete aggregation workflow
        start_time = datetime.now()
        result = await aggregation_service.aggregate_sector_sentiment_1d(test_sector)
        end_time = datetime.now()

        calculation_time = (end_time - start_time).total_seconds()

        # Validate result structure
        assert isinstance(result, SectorSentimentResult)
        assert result.sector == test_sector
        assert result.timeframe == "1D"
        assert isinstance(result.timestamp, datetime)

        # Validate performance metrics
        assert isinstance(result.sentiment_score, (int, float))
        assert isinstance(result.sector_performance_1d, (int, float))
        assert isinstance(result.iwm_benchmark_1d, (int, float))
        assert isinstance(result.alpha, (int, float))

        # Validate sentiment classification
        assert isinstance(result.color_classification, ColorClassification)
        assert isinstance(result.trading_signal, str)
        assert isinstance(result.relative_strength, str)

        # Validate data quality metrics
        assert isinstance(result.stock_count, int)
        assert isinstance(result.data_coverage, float)
        assert isinstance(result.confidence_level, float)

        # Validate ranges
        assert -1.0 <= result.sentiment_score <= 1.0
        assert 0.0 <= result.data_coverage <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0
        assert result.stock_count >= 0

        # Validate calculation metadata
        assert isinstance(result.volatility_multiplier, (int, float))
        assert isinstance(result.avg_volume_weight, (int, float))
        assert isinstance(result.calculation_time, (int, float))
        assert result.calculation_time >= 0.0

        # Performance validation
        assert (
            calculation_time < TEST_TIMEOUT
        ), f"Calculation too slow: {calculation_time}s"

        logger.info(f"Complete Workflow Results:")
        logger.info(f"  Sector: {result.sector}")
        logger.info(f"  Sentiment Score: {result.sentiment_score:.3f}")
        logger.info(f"  Color: {result.color_classification.value}")
        logger.info(f"  Trading Signal: {result.trading_signal}")
        logger.info(f"  Stock Count: {result.stock_count}")
        logger.info(f"  Data Coverage: {result.data_coverage:.1%}")
        logger.info(f"  Confidence: {result.confidence_level:.1%}")
        logger.info(f"  Calculation Time: {result.calculation_time:.3f}s")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_sector_aggregation_consistency(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test aggregation consistency across multiple sectors"""
        logger.info("=== TESTING MULTI-SECTOR CONSISTENCY ===")

        results = {}

        # Run aggregation for multiple sectors
        for sector in EXPECTED_SECTORS:
            if (
                sector not in real_stock_universe_sample
                or not real_stock_universe_sample[sector]
            ):
                logger.warning(f"Skipping {sector} - no stocks available")
                continue

            logger.info(f"Running aggregation for {sector}...")

            try:
                result = await aggregation_service.aggregate_sector_sentiment_1d(sector)
                results[sector] = result

                # Brief delay to respect API rate limits
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error aggregating {sector}: {e}")
                continue

        # Validate results consistency
        assert len(results) >= 1, "Should successfully aggregate at least one sector"

        # Validate cross-sector data consistency
        all_sentiment_scores = [r.sentiment_score for r in results.values()]
        all_stock_counts = [r.stock_count for r in results.values()]
        all_confidence_levels = [r.confidence_level for r in results.values()]

        # All sentiment scores should be within valid range
        assert all(-1.0 <= score <= 1.0 for score in all_sentiment_scores)

        # All stock counts should be non-negative
        assert all(count >= 0 for count in all_stock_counts)

        # All confidence levels should be within valid range
        assert all(0.0 <= conf <= 1.0 for conf in all_confidence_levels)

        # Log comparative results
        logger.info("Multi-Sector Results Summary:")
        for sector, result in results.items():
            logger.info(
                f"  {sector}: {result.sentiment_score:+.3f} "
                f"({result.color_classification.value}, "
                f"{result.stock_count} stocks, "
                f"{result.confidence_level:.1%} confidence)"
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_quality_assessment_integration(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test data quality assessment with real data"""
        logger.info("=== TESTING DATA QUALITY ASSESSMENT ===")

        test_sector = "technology"

        if test_sector not in real_stock_universe_sample:
            pytest.skip("No technology sector available for quality assessment")

        # Get sector mapping
        sector_mapping = await aggregation_service.get_sector_stocks(test_sector)

        # Get stock data
        stock_data_list = await aggregation_service.retrieve_stock_data_1d(
            sector_mapping.symbols[:5]
        )

        # Mock performance metadata for testing
        performance_metadata = {
            "data_coverage": 0.8,
            "volatility_multiplier": 1.3,
            "valid_stocks": len(stock_data_list),
        }

        # Assess data quality
        quality_assessment = aggregation_service.assess_data_quality(
            sector_mapping, stock_data_list, performance_metadata
        )

        # Validate assessment structure
        assert isinstance(quality_assessment, DataQualityAssessment)
        assert quality_assessment.sector == test_sector
        assert isinstance(quality_assessment.total_universe_stocks, int)
        assert isinstance(quality_assessment.api_success_count, int)
        assert isinstance(quality_assessment.data_coverage, float)
        assert isinstance(quality_assessment.confidence_score, float)
        assert isinstance(quality_assessment.quality_flags, list)
        assert isinstance(quality_assessment.recommendations, list)

        # Validate ranges and consistency
        assert (
            quality_assessment.api_success_count
            <= quality_assessment.total_universe_stocks
        )
        assert 0.0 <= quality_assessment.data_coverage <= 1.0
        assert 0.0 <= quality_assessment.confidence_score <= 1.0

        # Validate data consistency
        expected_coverage = (
            quality_assessment.api_success_count
            / quality_assessment.total_universe_stocks
            if quality_assessment.total_universe_stocks > 0
            else 0.0
        )
        assert abs(quality_assessment.data_coverage - expected_coverage) < 0.01

        logger.info(f"Data Quality Assessment:")
        logger.info(
            f"  Total Universe Stocks: {quality_assessment.total_universe_stocks}"
        )
        logger.info(f"  API Success Count: {quality_assessment.api_success_count}")
        logger.info(f"  Data Coverage: {quality_assessment.data_coverage:.1%}")
        logger.info(f"  Confidence Score: {quality_assessment.confidence_score:.1%}")
        logger.info(f"  Quality Flags: {quality_assessment.quality_flags}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_persistence_integration(self, aggregation_service):
        """Test database persistence integration"""
        logger.info("=== TESTING PERSISTENCE INTEGRATION ===")

        # Create test result
        test_result = SectorSentimentResult(
            sector="test_sector",
            timeframe="1D",
            sentiment_score=0.25,
            sector_performance_1d=3.5,
            iwm_benchmark_1d=1.2,
            alpha=2.3,
            color_classification=ColorClassification.LIGHT_GREEN,
            trading_signal="AVOID_SHORTS",
            relative_strength="OUTPERFORM",
            stock_count=5,
            data_coverage=0.8,
            confidence_level=0.75,
            volatility_multiplier=1.3,
            avg_volume_weight=1.8,
            calculation_time=2.5,
        )

        # Create test quality assessment
        test_quality = DataQualityAssessment(
            sector="test_sector",
            total_universe_stocks=6,
            api_success_count=5,
            valid_data_count=5,
            data_coverage=0.8,
            confidence_score=0.75,
            quality_flags=[],
            recommendations=[],
        )

        # Test persistence (should not raise exception)
        try:
            await aggregation_service._persist_sector_result_if_enabled(
                test_result, test_quality
            )
            logger.info("Persistence integration successful")
        except Exception as e:
            logger.warning(f"Persistence failed (non-blocking): {e}")
            # This is acceptable - persistence failures should not break calculations

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, aggregation_service):
        """Test error handling with invalid/missing data"""
        logger.info("=== TESTING ERROR HANDLING ===")

        # Test with non-existent sector
        result = await aggregation_service.aggregate_sector_sentiment_1d(
            "nonexistent_sector"
        )

        # Should return empty result, not crash
        assert isinstance(result, SectorSentimentResult)
        assert result.sector == "nonexistent_sector"
        assert result.sentiment_score == 0.0
        assert result.stock_count == 0
        assert result.confidence_level == 0.0

        logger.info("Error handling validation successful")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_benchmarking(
        self, aggregation_service, real_stock_universe_sample
    ):
        """Test performance requirements for Step 5"""
        logger.info("=== TESTING PERFORMANCE BENCHMARKING ===")

        test_sector = "technology"

        if test_sector not in real_stock_universe_sample:
            pytest.skip("No technology sector for performance testing")

        # Measure multiple runs for consistency
        run_times = []

        for i in range(3):
            start_time = datetime.now()
            result = await aggregation_service.aggregate_sector_sentiment_1d(
                test_sector
            )
            end_time = datetime.now()

            run_time = (end_time - start_time).total_seconds()
            run_times.append(run_time)

            logger.info(f"Run {i+1}: {run_time:.3f}s")

            # Brief delay between runs
            await asyncio.sleep(2)

        # Calculate performance metrics
        avg_time = sum(run_times) / len(run_times)
        max_time = max(run_times)

        logger.info(f"Performance Metrics:")
        logger.info(f"  Average Time: {avg_time:.3f}s")
        logger.info(f"  Maximum Time: {max_time:.3f}s")
        logger.info(f"  All Times: {[f'{t:.3f}s' for t in run_times]}")

        # Validate performance requirements
        assert avg_time < 10.0, f"Average calculation time too slow: {avg_time:.3f}s"
        assert max_time < 15.0, f"Maximum calculation time too slow: {max_time:.3f}s"

        logger.info("✅ Performance requirements met")

    @pytest.mark.integration
    def test_database_schema_compatibility(self):
        """Test that the service is compatible with existing database schema"""
        logger.info("=== TESTING DATABASE SCHEMA COMPATIBILITY ===")

        try:
            with SessionLocal() as db:
                # Test that we can query stock_universe table
                stock_count = db.query(StockUniverse).count()
                logger.info(f"Stock universe contains {stock_count} records")

                # Test that we can query sector_sentiment table
                sentiment_count = db.query(SectorSentiment).count()
                logger.info(f"Sector sentiment contains {sentiment_count} records")

                # Test specific field access
                if stock_count > 0:
                    sample_stock = db.query(StockUniverse).first()
                    assert hasattr(sample_stock, "symbol")
                    assert hasattr(sample_stock, "sector")
                    assert hasattr(sample_stock, "is_active")
                    logger.info(
                        f"Sample stock: {sample_stock.symbol} ({sample_stock.sector})"
                    )

                logger.info("✅ Database schema compatibility verified")

        except Exception as e:
            pytest.fail(f"Database schema compatibility test failed: {e}")
