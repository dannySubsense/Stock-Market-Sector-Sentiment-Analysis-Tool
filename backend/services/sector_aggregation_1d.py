"""
Sector Aggregation 1D - Step 5: Build Sector Performance Aggregation (1D Only)
Orchestrates Steps 1-4 components for complete sector sentiment analysis
Implements stock-to-sector mapping, weighted aggregation, sentiment classification, and data quality assessment
"""

import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from models.sector_sentiment import ColorClassification
from services.sector_performance_1d import SectorPerformanceCalculator1D, StockData1D
from services.stock_data_retrieval_1d import StockDataRetrieval1D
from services.volume_weighting_1d import VolumeWeightingEngine1D
from services.iwm_benchmark_service_1d import get_iwm_service
from services.persistence_interface import PersistenceLayer, get_persistence_layer
from config.volatility_weights import get_static_weights, get_weight_for_sector

logger = logging.getLogger(__name__)

# Color classification ranges from SDD
COLOR_SENTIMENT_RANGES = {
    ColorClassification.DARK_RED: (-1.0, -0.6),  # Strong bearish
    ColorClassification.LIGHT_RED: (-0.6, -0.2),  # Moderate bearish
    ColorClassification.BLUE_NEUTRAL: (-0.2, 0.2),  # Neutral
    ColorClassification.LIGHT_GREEN: (0.2, 0.6),  # Moderate bullish
    ColorClassification.DARK_GREEN: (0.6, 1.0),  # Strong bullish
}

# Trading signals from SDD
TRADING_SIGNALS = {
    ColorClassification.DARK_RED: "PRIME_SHORTING_ENVIRONMENT",
    ColorClassification.LIGHT_RED: "GOOD_SHORTING_ENVIRONMENT",
    ColorClassification.BLUE_NEUTRAL: "NEUTRAL_CAUTIOUS",
    ColorClassification.LIGHT_GREEN: "AVOID_SHORTS",
    ColorClassification.DARK_GREEN: "DO_NOT_SHORT",
}

# Data quality thresholds
MIN_STOCKS_FOR_HIGH_CONFIDENCE = 5
MIN_STOCKS_FOR_CALCULATION = 1
MIN_DATA_COVERAGE_FOR_CONFIDENCE = 0.6


@dataclass
class SectorStockMapping:
    """Mapping of stocks to sectors from universe database"""

    sector: str
    symbols: List[str]
    total_stocks: int
    active_stocks: int
    coverage_percentage: float


@dataclass
class SectorSentimentResult:
    """Complete sector sentiment analysis result for 1D timeframe"""

    # Core identification
    sector: str
    timeframe: str = "1D"
    timestamp: Optional[datetime] = None

    # Performance metrics
    sentiment_score: float = 0.0  # -1.0 to +1.0
    sector_performance_1d: float = 0.0  # Raw percentage
    iwm_benchmark_1d: float = 0.0  # IWM performance
    alpha: float = 0.0  # Sector vs IWM

    # Classification
    color_classification: ColorClassification = ColorClassification.BLUE_NEUTRAL
    trading_signal: str = "NEUTRAL_CAUTIOUS"
    relative_strength: str = "NEUTRAL"

    # Data quality
    stock_count: int = 0
    data_coverage: float = 0.0  # 0.0 to 1.0
    confidence_level: float = 0.0  # 0.0 to 1.0

    # Calculation metadata
    volatility_multiplier: float = 1.0
    avg_volume_weight: float = 1.0
    calculation_time: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class DataQualityAssessment:
    """Assessment of data quality for sector analysis"""

    sector: str
    total_universe_stocks: int
    api_success_count: int
    valid_data_count: int
    data_coverage: float
    confidence_score: float
    quality_flags: List[str]
    recommendations: List[str]


class SectorAggregation1D:
    """
    Step 5: 1D Sector Performance Aggregation

    Orchestrates Steps 1-4 components for complete sector sentiment analysis:
    - Stock-to-Sector Mapping (database queries)
    - Real Data Retrieval (Step 2 integration)
    - Volume Weighting (Step 3 integration)
    - IWM Benchmarking (Step 4 integration)
    - Sentiment Classification & Quality Assessment
    """

    def __init__(self, persistence_layer: Optional[PersistenceLayer] = None):
        """
        Initialize sector aggregation service with dependency injection

        Args:
            persistence_layer: Optional persistence implementation for data storage
                              If None, uses database persistence by default
        """
        # Initialize Step 1-4 components
        volatility_multipliers = get_static_weights()
        self.performance_calculator = SectorPerformanceCalculator1D(
            volatility_multipliers
        )
        self.data_retrieval = StockDataRetrieval1D()
        self.volume_weighting = VolumeWeightingEngine1D(persistence_layer)
        self.iwm_service = get_iwm_service()

        # Dependency injection for persistence (enables testing and flexibility)
        self.persistence = persistence_layer or get_persistence_layer(
            enable_database=True
        )

        # Plan 1: Add persistence service for cleanup operations
        from services.data_persistence_service import get_persistence_service

        self.cleanup_service = get_persistence_service()

        logger.debug(
            "Initialized SectorAggregation1D with all Step 1-4 components and Plan 1 cleanup"
        )

    async def get_sector_stocks(self, sector: str) -> SectorStockMapping:
        """
        Step 5 Task 1: Stock-to-Sector Mapping
        Retrieve stocks by sector from universe database
        """
        try:
            with SessionLocal() as db:
                # Get all stocks in sector
                all_sector_stocks = (
                    db.query(StockUniverse).filter(StockUniverse.sector == sector).all()
                )

                # Get active stocks only
                active_sector_stocks = (
                    db.query(StockUniverse)
                    .filter(
                        and_(
                            StockUniverse.sector == sector,
                            StockUniverse.is_active.is_(True),
                        )
                    )
                    .all()
                )

                # Extract symbols
                active_symbols = [str(stock.symbol) for stock in active_sector_stocks]

                # Calculate coverage
                total_count = len(all_sector_stocks)
                active_count = len(active_sector_stocks)
                coverage = (
                    (active_count / total_count * 100) if total_count > 0 else 0.0
                )

                logger.info(
                    f"Sector {sector}: {active_count}/{total_count} active stocks ({coverage:.1f}% coverage)"
                )

                return SectorStockMapping(
                    sector=sector,
                    symbols=active_symbols,
                    total_stocks=total_count,
                    active_stocks=active_count,
                    coverage_percentage=coverage,
                )

        except Exception as e:
            logger.error(f"Error getting stocks for sector {sector}: {e}")
            return SectorStockMapping(
                sector=sector,
                symbols=[],
                total_stocks=0,
                active_stocks=0,
                coverage_percentage=0.0,
            )

    async def retrieve_stock_data_1d(self, symbols: List[str]) -> List[StockData1D]:
        """
        Step 5 Integration: Retrieve 1D stock data using Step 2 service
        Using Polygon API for unlimited rate limits in sector calculations
        """
        import asyncio

        stock_data_list = []

        for i, symbol in enumerate(symbols):
            try:
                # Use Polygon API for sector calculations (unlimited rate limits)
                stock_data = await self.data_retrieval.get_1d_stock_data(
                    symbol, "polygon"
                )

                if stock_data and self._validate_stock_data(stock_data):
                    stock_data_list.append(stock_data)
                else:
                    logger.warning(f"Failed to retrieve valid data for {symbol}")

            except Exception as e:
                logger.error(f"Exception retrieving data for {symbol}: {e}")

            # Minimal delay for Polygon (handles rate limiting internally)
            if i > 0 and i % 10 == 0:  # Every 10 calls
                await asyncio.sleep(0.01)  # 10ms delay

        logger.info(f"Retrieved data for {len(stock_data_list)}/{len(symbols)} stocks")

        return stock_data_list

    async def calculate_weighted_sector_performance(
        self, sector: str, stock_data_list: List[StockData1D]
    ) -> Dict[str, Any]:
        """
        Step 5 Task 2: Weighted Aggregation Logic
        Calculate sector performance using Step 1 + Step 3 components
        """
        if not stock_data_list:
            logger.warning(f"No stock data available for sector {sector}")
            return self._get_empty_performance_result(sector)

        try:
            # Get IWM benchmark data using Step 4 service
            iwm_data = await self.iwm_service.get_cached_iwm_benchmark_1d()

            # Use Step 1 service for sector aggregation
            sector_performance, metadata = (
                self.performance_calculator.calculate_sector_aggregation(
                    stock_data_list, sector
                )
            )

            # Calculate alpha using Step 4 service
            alpha = self.iwm_service.calculate_sector_alpha(
                sector_performance, iwm_data.performance_1d
            )

            # Get relative strength classification
            relative_strength = self.iwm_service.classify_relative_strength(alpha)

            return {
                "sector_performance_1d": sector_performance,
                "iwm_benchmark_1d": iwm_data.performance_1d,
                "alpha": alpha,
                "relative_strength": relative_strength,
                "iwm_confidence": iwm_data.confidence,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error calculating weighted performance for {sector}: {e}")
            return self._get_empty_performance_result(sector)

    def classify_sector_sentiment(
        self, sector_performance: float, alpha: float
    ) -> Dict[str, Any]:
        """
        Step 5 Task 3: Sector Sentiment Classification
        Map performance percentages to color classifications and trading signals
        """
        try:
            # Normalize performance to sentiment score (-1.0 to +1.0)
            # Use alpha (sector vs IWM) for better classification
            sentiment_score = self._normalize_to_sentiment_score(alpha)

            # Classify color based on sentiment score
            color_classification = self._classify_sentiment_color(sentiment_score)

            # Get trading signal
            trading_signal = TRADING_SIGNALS[color_classification]

            return {
                "sentiment_score": sentiment_score,
                "color_classification": color_classification,
                "trading_signal": trading_signal,
            }

        except Exception as e:
            logger.error(f"Error classifying sector sentiment: {e}")
            return {
                "sentiment_score": 0.0,
                "color_classification": ColorClassification.BLUE_NEUTRAL,
                "trading_signal": TRADING_SIGNALS[ColorClassification.BLUE_NEUTRAL],
            }

    def assess_data_quality(
        self,
        sector_mapping: SectorStockMapping,
        stock_data_list: List[StockData1D],
        performance_metadata: Dict[str, Any],
    ) -> DataQualityAssessment:
        """
        Step 5 Task 4: Data Quality Assessment
        Track stock counts, data coverage, and confidence levels
        """
        quality_flags = []
        recommendations = []

        # Calculate data coverage
        api_success_count = len(stock_data_list)
        total_universe_stocks = sector_mapping.active_stocks
        data_coverage = (
            (api_success_count / total_universe_stocks)
            if total_universe_stocks > 0
            else 0.0
        )

        # Assess stock count adequacy
        if api_success_count < MIN_STOCKS_FOR_CALCULATION:
            quality_flags.append("INSUFFICIENT_STOCKS")
            recommendations.append("Need at least 1 stock for calculation")
        elif api_success_count < MIN_STOCKS_FOR_HIGH_CONFIDENCE:
            quality_flags.append("LOW_STOCK_COUNT")
            recommendations.append(
                f"Low stock count ({api_success_count}), consider sector consolidation"
            )

        # Assess data coverage
        if data_coverage < MIN_DATA_COVERAGE_FOR_CONFIDENCE:
            quality_flags.append("LOW_DATA_COVERAGE")
            recommendations.append(
                f"Low data coverage ({data_coverage:.1%}), API issues possible"
            )

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            api_success_count,
            total_universe_stocks,
            data_coverage,
            performance_metadata,
        )

        return DataQualityAssessment(
            sector=sector_mapping.sector,
            total_universe_stocks=total_universe_stocks,
            api_success_count=api_success_count,
            valid_data_count=api_success_count,  # All retrieved data is valid
            data_coverage=data_coverage,
            confidence_score=confidence_score,
            quality_flags=quality_flags,
            recommendations=recommendations,
        )

    async def aggregate_sector_sentiment_1d(self, sector: str) -> SectorSentimentResult:
        """
        Main orchestration method for complete 1D sector sentiment analysis
        Plan 1 Enhanced: Includes mandatory cleanup before data retrieval

        Workflow:
        0. Plan 1: Cleanup stale data for this timeframe (mandatory)
        1. Get stocks for sector (database query)
        2. Retrieve 1D price/volume data (Step 2)
        3. Calculate volume-weighted performance (Step 3)
        4. Apply IWM benchmark comparison (Step 4)
        5. Classify sentiment and confidence (Step 1 + new logic)
        6. Persist results (optional, non-blocking)
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting 1D sector aggregation for {sector} with Plan 1 cleanup"
            )

            # Plan 1 Step 0: Mandatory cleanup before data retrieval
            logger.debug(f"Plan 1: Cleaning stale 1D data before {sector} analysis")
            cleanup_success = await self.cleanup_service.cleanup_before_analysis("1d")

            if not cleanup_success:
                logger.warning(
                    f"Plan 1 cleanup failed for {sector} but continuing with analysis"
                )
            else:
                logger.debug(f"Plan 1 cleanup completed for {sector}")

            # Task 1: Stock-to-Sector Mapping
            sector_mapping = await self.get_sector_stocks(sector)

            if not sector_mapping.symbols:
                logger.warning(f"No active stocks found for sector {sector}")
                return self._get_empty_sector_result(sector, time.time() - start_time)

            # Task 2: Data Retrieval (Step 2 integration)
            stock_data_list = await self.retrieve_stock_data_1d(sector_mapping.symbols)

            # VALIDATION: 95% Success Rate Check for this specific sector
            total_requested = len(sector_mapping.symbols)
            successful_count = len(stock_data_list)
            success_rate = (
                (successful_count / total_requested * 100) if total_requested > 0 else 0
            )

            logger.info(
                f"Sector {sector}: {successful_count}/{total_requested} stocks retrieved ({success_rate:.1f}%)"
            )

            # Error check: Below 95% success rate indicates sector-specific issues
            if success_rate < 95.0:
                failed_symbols = [
                    symbol
                    for symbol in sector_mapping.symbols
                    if not any(stock.symbol == symbol for stock in stock_data_list)
                ]
                error_msg = (
                    f"CRITICAL: Sector {sector} data success rate {success_rate:.1f}% below 95% threshold. "
                    f"Failed symbols: {failed_symbols[:10]}{'...' if len(failed_symbols) > 10 else ''}. "
                    f"This may indicate API issues, sector-specific problems, or data coverage gaps."
                )
                logger.error(error_msg)

                # For now, log as error but continue processing with available data
                # In production, you might want to raise an exception or flag the sector
                # raise ValueError(error_msg)

            elif success_rate < 98.0:
                failed_symbols = [
                    symbol
                    for symbol in sector_mapping.symbols
                    if not any(stock.symbol == symbol for stock in stock_data_list)
                ]
                logger.warning(
                    f"Sector {sector} data success rate {success_rate:.1f}% is acceptable but below optimal. "
                    f"Failed {len(failed_symbols)} stocks: {failed_symbols}"
                )
            else:
                logger.info(
                    f"Excellent data success rate for sector {sector}: {success_rate:.1f}%"
                )

            if not stock_data_list:
                logger.warning(f"No valid stock data retrieved for sector {sector}")
                return self._get_empty_sector_result(sector, time.time() - start_time)

            # Task 3: Weighted Aggregation (Step 1 + Step 3 + Step 4 integration)
            performance_result = await self.calculate_weighted_sector_performance(
                sector, stock_data_list
            )

            # Task 4: Sentiment Classification
            sentiment_result = self.classify_sector_sentiment(
                performance_result["sector_performance_1d"], performance_result["alpha"]
            )

            # Task 5: Data Quality Assessment
            quality_assessment = self.assess_data_quality(
                sector_mapping, stock_data_list, performance_result["metadata"]
            )

            # Create final result
            calculation_time = time.time() - start_time
            result = SectorSentimentResult(
                sector=sector,
                timeframe="1D",
                timestamp=datetime.utcnow(),
                # Performance metrics
                sentiment_score=sentiment_result["sentiment_score"],
                sector_performance_1d=performance_result["sector_performance_1d"],
                iwm_benchmark_1d=performance_result["iwm_benchmark_1d"],
                alpha=performance_result["alpha"],
                # Classification
                color_classification=sentiment_result["color_classification"],
                trading_signal=sentiment_result["trading_signal"],
                relative_strength=performance_result["relative_strength"],
                # Data quality
                stock_count=len(stock_data_list),
                data_coverage=quality_assessment.data_coverage,
                confidence_level=quality_assessment.confidence_score,
                # Calculation metadata
                volatility_multiplier=performance_result["metadata"].get(
                    "volatility_multiplier", 1.0
                ),
                avg_volume_weight=performance_result["metadata"].get(
                    "avg_volume_weight", 1.0
                ),
                calculation_time=calculation_time,
            )

            # Task 6: Persistence (optional, non-blocking)
            await self._persist_sector_result_if_enabled(result, quality_assessment)

            logger.info(
                f"Completed 1D aggregation for {sector}: {result.sentiment_score:.3f} "
                f"({result.color_classification.value}) in {calculation_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Error in 1D sector aggregation for {sector}: {e}")
            return self._get_empty_sector_result(sector, time.time() - start_time)

    # Helper methods

    def _validate_stock_data(self, stock_data: StockData1D) -> bool:
        """Validate stock data quality"""
        return (
            stock_data.current_price > 0
            and stock_data.previous_close > 0
            and stock_data.current_volume >= 0
        )

    def _normalize_to_sentiment_score(self, alpha: float) -> float:
        """Convert alpha percentage to sentiment score (-1.0 to +1.0)"""
        # Alpha is already a percentage, normalize to reasonable range
        # ±10% alpha = ±1.0 sentiment (with compression for extreme values)
        if alpha == 0:
            return 0.0

        # Apply logarithmic compression for extreme values
        import math

        sign = 1 if alpha > 0 else -1
        abs_alpha = abs(alpha)

        if abs_alpha <= 10.0:
            # Linear mapping for normal range
            normalized = abs_alpha / 10.0
        else:
            # Logarithmic compression for extreme values
            normalized = 0.8 + (0.2 * (1 - math.exp(-(abs_alpha - 10.0) / 20.0)))

        return sign * min(1.0, normalized)

    def _classify_sentiment_color(self, sentiment_score: float) -> ColorClassification:
        """Classify sentiment score into color category"""
        for color, (min_score, max_score) in COLOR_SENTIMENT_RANGES.items():
            if min_score <= sentiment_score < max_score:
                return color

        # Handle edge case for exactly 1.0
        if sentiment_score >= 1.0:
            return ColorClassification.DARK_GREEN

        # Default fallback
        return ColorClassification.BLUE_NEUTRAL

    def _calculate_confidence_score(
        self,
        api_success_count: int,
        total_universe_stocks: int,
        data_coverage: float,
        performance_metadata: Dict[str, Any],
    ) -> float:
        """Calculate confidence score based on data quality factors"""
        try:
            # Factor 1: Stock count adequacy (0.0-1.0)
            stock_count_factor = min(
                1.0, api_success_count / MIN_STOCKS_FOR_HIGH_CONFIDENCE
            )

            # Factor 2: Data coverage (0.0-1.0)
            coverage_factor = data_coverage

            # Factor 3: Metadata quality (0.0-1.0)
            metadata_factor = performance_metadata.get("data_coverage", 0.0)

            # Weighted combination
            confidence = (
                stock_count_factor * 0.4 + coverage_factor * 0.4 + metadata_factor * 0.2
            )

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence

    def _get_empty_performance_result(self, sector: str) -> Dict[str, Any]:
        """Get empty performance result for error cases"""
        return {
            "sector_performance_1d": 0.0,
            "iwm_benchmark_1d": 0.0,
            "alpha": 0.0,
            "relative_strength": "NEUTRAL",
            "iwm_confidence": 0.0,
            "metadata": {
                "volatility_multiplier": get_weight_for_sector(sector),
                "avg_volume_weight": 1.0,
                "data_coverage": 0.0,
                "valid_stocks": 0,
            },
        }

    def _get_empty_sector_result(
        self, sector: str, calculation_time: float
    ) -> SectorSentimentResult:
        """Get empty sector result for error cases"""
        return SectorSentimentResult(
            sector=sector,
            timeframe="1D",
            timestamp=datetime.utcnow(),
            calculation_time=calculation_time,
        )

    async def _persist_sector_result_if_enabled(
        self, result: SectorSentimentResult, quality_assessment: DataQualityAssessment
    ) -> None:
        """
        Separated persistence logic for sector results
        Non-blocking - failures don't affect main calculation
        """
        try:
            # Convert to persistence format
            persistence_data = {
                "sector": result.sector,
                "timeframe": result.timeframe,
                "sentiment_score": result.sentiment_score,
                "color_classification": result.color_classification.value,
                "trading_signal": result.trading_signal,
                "confidence_level": result.confidence_level,
                "stock_count": result.stock_count,
                "data_coverage": result.data_coverage,
                "timestamp": result.timestamp,
                "quality_assessment": quality_assessment,
            }

            success = await self.persistence.store_sector_sentiment(persistence_data)

            if success:
                logger.debug(
                    f"Successfully persisted 1D sector result for {result.sector}"
                )
            else:
                logger.warning("Sector result persistence failed (non-blocking)")

        except Exception as e:
            # Persistence failures are logged but don't affect main calculation
            logger.warning(f"Sector result persistence error (non-blocking): {e}")


# Global instance
_sector_aggregation_1d: Optional[SectorAggregation1D] = None


def get_sector_aggregation_1d() -> SectorAggregation1D:
    """Get global sector aggregation service instance"""
    global _sector_aggregation_1d
    if _sector_aggregation_1d is None:
        _sector_aggregation_1d = SectorAggregation1D()
    return _sector_aggregation_1d
