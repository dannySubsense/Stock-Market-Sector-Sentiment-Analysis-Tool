"""
IWM Benchmark Service - Step 4: IWM Benchmark Integration (1D Only)
Provides centralized IWM data retrieval, caching, and benchmark calculations
Reuses existing tested mathematical logic for safety and consistency
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from services.sector_performance_1d import StockData1D
from services.stock_data_retrieval_1d import StockDataRetrieval1D
from services.cache_service import get_cache_service
from services.persistence_interface import PersistenceLayer


logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """Configuration for IWM data source retrieval"""

    name: str
    source_type: str
    description: str
    priority: int  # Lower number = higher priority


@dataclass
class TimeframeApproximationConfig:
    """Configuration for multi-timeframe approximations"""

    intraday_30min: float = 0.3  # Conservative intraday estimate
    short_term_3day: float = 2.5  # Short-term momentum multiplier
    weekly_1week: float = 4.0  # Weekly trend estimate

    def __post_init__(self):
        """Validate approximation multipliers"""
        if not (0.1 <= self.intraday_30min <= 0.8):
            raise ValueError(
                f"30min multiplier {self.intraday_30min} outside valid range 0.1-0.8"
            )
        if not (1.5 <= self.short_term_3day <= 4.0):
            raise ValueError(
                f"3day multiplier {self.short_term_3day} outside valid range 1.5-4.0"
            )
        if not (2.0 <= self.weekly_1week <= 6.0):
            raise ValueError(
                f"1week multiplier {self.weekly_1week} outside valid range 2.0-6.0"
            )


@dataclass
class IWMBenchmarkData1D:
    """IWM benchmark data structure for 1D calculations"""

    performance_1d: float  # IWM 1D percentage change
    current_price: float
    previous_close: float
    timestamp: datetime
    data_source: str  # "FMP", "Polygon", or "Cache"
    cache_status: str  # "fresh", "cached", "stale", "none"
    confidence: float  # Data quality confidence (0.0-1.0)


class IWMBenchmarkService1D:
    """
    Centralized service for IWM (Russell 2000) benchmark data and calculations.

    Provides consolidated functionality for:
    - IWM data retrieval with fallback sources
    - Benchmark performance calculations
    - Sector alpha calculations
    - Multi-timeframe approximations
    - Caching and error handling
    """

    IWM_SYMBOL = "IWM"

    # Cache TTL settings (seconds)
    CACHE_TTL_MARKET_HOURS = 300  # 5 minutes during market hours
    CACHE_TTL_AFTER_HOURS = 3600  # 1 hour after market close
    CACHE_TTL_WEEKEND = 7200  # 2 hours on weekends

    # Data validation thresholds
    MIN_PRICE = 50.0  # IWM typically trades above $50
    MAX_PRICE = 500.0  # IWM typically trades below $500
    MAX_DAILY_CHANGE = 20.0  # Maximum reasonable daily change %

    # Relative strength thresholds (moved from SectorPerformanceCalculator1D)
    STRONG_OUTPERFORM_THRESHOLD = 2.0
    OUTPERFORM_THRESHOLD = 0.5
    NEUTRAL_THRESHOLD = -0.5
    UNDERPERFORM_THRESHOLD = -2.0

    def __init__(self, persistence_layer: Optional[PersistenceLayer] = None):
        """
        Initialize IWM benchmark service with optional persistence

        Args:
            persistence_layer: Optional persistence implementation for data storage
                              If None, uses database persistence by default
        """
        self.data_retrieval = StockDataRetrieval1D()
        self.cache_service = get_cache_service()

        # Initialize timeframe approximation configuration with validation
        self.timeframe_config = TimeframeApproximationConfig()

        # Dependency injection for persistence (enables testing and flexibility)
        from services.persistence_interface import get_persistence_layer

        self.persistence = persistence_layer or get_persistence_layer(
            enable_database=True
        )

    def _get_data_source_configs(self) -> List[DataSourceConfig]:
        """Get ordered list of data source configurations for retrieval attempts"""
        return [
            DataSourceConfig(
                name="POLYGON",
                source_type="polygon",
                description="Polygon.io for consistent API usage with sector calculations",
                priority=1,
            ),
            DataSourceConfig(
                name="FMP",
                source_type="fmp",
                description="Financial Modeling Prep fallback",
                priority=2,
            ),
        ]

    async def _retrieve_from_source(
        self, config: DataSourceConfig
    ) -> Optional[StockData1D]:
        """
        Retrieve IWM data from a specific source

        Args:
            config: Data source configuration

        Returns:
            StockData1D if successful, None if failed
        """
        try:
            logger.info(f"Attempting IWM data retrieval from {config.name}")

            iwm_data = await self.data_retrieval.get_1d_stock_data(
                self.IWM_SYMBOL, config.source_type
            )

            if iwm_data and self._validate_iwm_data(iwm_data):
                logger.info(f"Successfully retrieved IWM data from {config.name}")
                return iwm_data
            else:
                logger.warning(f"Invalid data received from {config.name}")
                return None

        except Exception as e:
            logger.warning(f"Failed to retrieve from {config.name}: {e}")
            return None

    def _create_benchmark_data(
        self, iwm_data: StockData1D, config: DataSourceConfig
    ) -> IWMBenchmarkData1D:
        """
        Create IWMBenchmarkData1D from raw stock data

        Args:
            iwm_data: Raw stock data from API
            config: Source configuration used for retrieval

        Returns:
            Formatted IWMBenchmarkData1D
        """
        performance_1d = self.calculate_iwm_benchmark(
            iwm_data.current_price, iwm_data.previous_close
        )
        confidence = self._calculate_data_confidence(iwm_data)

        return IWMBenchmarkData1D(
            performance_1d=performance_1d,
            current_price=iwm_data.current_price,
            previous_close=iwm_data.previous_close,
            timestamp=datetime.utcnow(),
            data_source=config.name,
            cache_status="fresh",
            confidence=confidence,
        )

    async def get_cached_iwm_benchmark_1d(self) -> IWMBenchmarkData1D:
        """
        Get IWM benchmark data with intelligent caching and separated persistence

        Returns:
            IWMBenchmarkData1D with current IWM performance data

        Raises:
            Exception: If all data sources fail and no fallback available
        """
        try:
            # Try cache first
            cached_data = await self.cache_service.get_cached_iwm_benchmark_1d()

            if cached_data and self._is_cache_fresh(cached_data):
                logger.debug("Cache hit for IWM benchmark data")
                return self._parse_cached_iwm_data(cached_data)

            # Cache miss or stale - refresh data (pure calculation)
            logger.info("Refreshing IWM benchmark data")
            fresh_data = await self.refresh_iwm_data()

            # Cache the fresh data (core functionality)
            await self._cache_iwm_data(fresh_data)

            # Separated persistence - non-blocking
            await self._persist_iwm_data_if_enabled(fresh_data)

            return fresh_data

        except Exception as e:
            logger.error(f"Error getting IWM benchmark data: {e}")

            # Try to use stale cache as fallback
            if cached_data:
                logger.warning("Using stale cache data as fallback")
                stale_data = self._parse_cached_iwm_data(cached_data)
                stale_data.cache_status = "stale"
                stale_data.confidence *= 0.7  # Reduce confidence for stale data
                return stale_data

            # Last resort: return neutral benchmark
            return self._get_neutral_benchmark()

    async def refresh_iwm_data(self) -> IWMBenchmarkData1D:
        """
        Refresh IWM data from APIs with fallback logic

        Returns:
            Fresh IWMBenchmarkData1D from API sources

        Raises:
            Exception: If all API sources fail
        """
        start_time = time.time()

        try:
            # Get ordered list of data source configurations
            data_source_configs = self._get_data_source_configs()

            # Attempt to retrieve data from each source in priority order
            for config in data_source_configs:
                iwm_data = await self._retrieve_from_source(config)
                if iwm_data:
                    retrieval_time = time.time() - start_time
                    logger.info(
                        f"Retrieved fresh IWM data from {config.name} in {retrieval_time:.3f}s"
                    )
                    return self._create_benchmark_data(iwm_data, config)

            # All APIs failed
            raise Exception("All IWM data sources failed - POLYGON and FMP")

        except Exception as e:
            logger.error(f"Failed to refresh IWM data: {e}")
            raise

    def calculate_sector_alpha(
        self, sector_performance: float, iwm_performance: float
    ) -> float:
        """
        Calculate sector alpha (sector performance - IWM performance)

        Args:
            sector_performance: Sector performance percentage
            iwm_performance: IWM benchmark performance percentage

        Returns:
            Alpha value (positive = outperformance, negative = underperformance)
        """
        alpha = sector_performance - iwm_performance
        return round(alpha, 3)

    def calculate_iwm_benchmark(self, iwm_current: float, iwm_previous: float) -> float:
        """
        Calculate IWM (Russell 2000) benchmark performance
        Formula: (iwm_current - iwm_previous) / iwm_previous * 100

        Args:
            iwm_current: Current IWM price
            iwm_previous: Previous close IWM price

        Returns:
            IWM performance percentage
        """
        if iwm_previous <= 0:
            raise ValueError(f"Invalid IWM previous close: {iwm_previous}")
        if iwm_current <= 0:
            raise ValueError(f"Invalid IWM current price: {iwm_current}")

        iwm_performance = (iwm_current - iwm_previous) / iwm_previous * 100
        return round(iwm_performance, 3)

    def classify_relative_strength(self, alpha: float) -> str:
        """
        Classify sector relative strength based on alpha vs IWM

        Args:
            alpha: Sector performance - IWM performance

        Returns:
            Relative strength classification string
        """
        if alpha > self.STRONG_OUTPERFORM_THRESHOLD:
            return "STRONG_OUTPERFORM"
        elif alpha > self.OUTPERFORM_THRESHOLD:
            return "OUTPERFORM"
        elif alpha > self.NEUTRAL_THRESHOLD:
            return "NEUTRAL"
        elif alpha > self.UNDERPERFORM_THRESHOLD:
            return "UNDERPERFORM"
        else:
            return "STRONG_UNDERPERFORM"

    async def get_russell_2000_performance(self) -> Dict[str, float]:
        """
        Get Russell 2000 (IWM) performance across multiple timeframes
        with validated approximations

        Returns:
            Dictionary with performance percentages for different timeframes
        """
        try:
            # Get fresh IWM data
            iwm_data = await self.get_cached_iwm_benchmark_1d()

            if iwm_data and iwm_data.performance_1d is not None:
                daily_change = iwm_data.performance_1d
                return self._calculate_timeframe_approximations(daily_change)
        except Exception as e:
            logger.warning(f"Error getting Russell 2000 performance: {e}")

        # Default neutral performance
        return {"30min": 0, "1day": 0, "3day": 0, "1week": 0}

    def _calculate_timeframe_approximations(
        self, daily_change: float
    ) -> Dict[str, float]:
        """
        Calculate timeframe approximations using validated configuration

        Args:
            daily_change: 1D performance percentage

        Returns:
            Dictionary with approximated performance across timeframes
        """
        return {
            "30min": daily_change * self.timeframe_config.intraday_30min,
            "1day": daily_change,
            "3day": daily_change * self.timeframe_config.short_term_3day,
            "1week": daily_change * self.timeframe_config.weekly_1week,
        }

    def calculate_russell_comparison(
        self, timeframe_scores: Dict, russell_benchmark: Optional[Dict]
    ) -> Dict[str, float]:
        """
        Calculate sector performance relative to Russell 2000

        Args:
            timeframe_scores: Sector scores for different timeframes
            russell_benchmark: Russell 2000 benchmark data

        Returns:
            Dictionary with relative performance for each timeframe
        """
        if not russell_benchmark:
            return {"30min": 0, "1day": 0, "3day": 0, "1week": 0}

        comparison = {}
        for timeframe in ["30min", "1day", "3day", "1week"]:
            sector_score = (
                timeframe_scores.get(timeframe, 0) * 100
            )  # Convert to percentage
            russell_score = russell_benchmark.get(timeframe, 0)
            comparison[timeframe] = sector_score - russell_score

        return comparison

    async def get_iwm_health_check(self) -> Dict[str, Any]:
        """
        Get IWM service health status

        Returns:
            Health check results with service status
        """
        try:
            start_time = time.time()

            # Test cache connectivity
            cache_healthy = await self.cache_service.health_check()

            # Test API connectivity (quick test)
            api_test_start = time.time()
            try:
                test_data = await self.data_retrieval.get_1d_stock_data(
                    self.IWM_SYMBOL, "polygon"
                )
                api_healthy = test_data is not None
                api_response_time = (time.time() - api_test_start) * 1000
            except Exception:
                api_healthy = False
                api_response_time = -1

            total_time = (time.time() - start_time) * 1000

            return {
                "status": (
                    "healthy"
                    if (cache_healthy["status"] == "healthy" and api_healthy)
                    else "degraded"
                ),
                "cache_status": cache_healthy["status"],
                "api_status": "healthy" if api_healthy else "unhealthy",
                "api_response_time_ms": api_response_time,
                "total_response_time_ms": total_time,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"IWM health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _validate_iwm_data(self, iwm_data) -> bool:
        """Validate IWM data quality"""
        try:
            if not iwm_data:
                return False

            # Price validation
            if not (self.MIN_PRICE <= iwm_data.current_price <= self.MAX_PRICE):
                logger.warning(f"IWM price out of range: ${iwm_data.current_price}")
                return False

            if not (self.MIN_PRICE <= iwm_data.previous_close <= self.MAX_PRICE):
                logger.warning(
                    f"IWM previous close out of range: ${iwm_data.previous_close}"
                )
                return False

            # Change validation
            change_percent = abs(
                (iwm_data.current_price - iwm_data.previous_close)
                / iwm_data.previous_close
                * 100
            )
            if change_percent > self.MAX_DAILY_CHANGE:
                logger.warning(f"IWM daily change too large: {change_percent:.2f}%")
                return False

            # Volume validation (basic)
            if iwm_data.current_volume < 0:
                logger.warning(f"Invalid IWM volume: {iwm_data.current_volume}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating IWM data: {e}")
            return False

    def _calculate_data_confidence(self, iwm_data) -> float:
        """Calculate confidence score for IWM data"""
        try:
            confidence = 1.0

            # Volume confidence (higher volume = higher confidence)
            if (
                hasattr(iwm_data, "avg_20_day_volume")
                and iwm_data.avg_20_day_volume > 0
            ):
                volume_ratio = iwm_data.current_volume / iwm_data.avg_20_day_volume
                if volume_ratio < 0.3:  # Very low volume
                    confidence *= 0.8
                elif volume_ratio < 0.7:  # Low volume
                    confidence *= 0.9
                elif volume_ratio > 3.0:  # Very high volume
                    confidence *= 0.95
            else:
                confidence *= 0.9  # Reduce confidence if no volume history

            # Price change confidence (extreme changes reduce confidence)
            change_percent = abs(
                (iwm_data.current_price - iwm_data.previous_close)
                / iwm_data.previous_close
                * 100
            )
            if change_percent > 5.0:  # Large changes
                confidence *= 0.9
            if change_percent > 10.0:  # Very large changes
                confidence *= 0.8

            return round(max(0.0, min(1.0, confidence)), 3)

        except Exception as e:
            logger.error(f"Error calculating IWM confidence: {e}")
            return 0.5  # Default moderate confidence

    def _is_cache_fresh(self, cached_data: Dict) -> bool:
        """Check if cached data is still fresh"""
        try:
            cached_at = datetime.fromisoformat(cached_data["cached_at"])
            age_seconds = (datetime.utcnow() - cached_at).total_seconds()

            # Dynamic TTL based on market hours (simplified)
            current_hour = datetime.utcnow().hour
            is_market_hours = 9 <= current_hour <= 16  # Simplified market hours

            if is_market_hours:
                ttl = self.CACHE_TTL_MARKET_HOURS
            else:
                ttl = self.CACHE_TTL_AFTER_HOURS

            return age_seconds < ttl

        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False

    def _parse_cached_iwm_data(self, cached_data: Dict) -> IWMBenchmarkData1D:
        """Parse cached data into IWMBenchmarkData1D object"""
        return IWMBenchmarkData1D(
            performance_1d=cached_data.get("performance_1d", 0.0),
            current_price=cached_data.get("current_price", 0.0),
            previous_close=cached_data.get("previous_close", 0.0),
            timestamp=datetime.fromisoformat(
                cached_data.get("timestamp", datetime.utcnow().isoformat())
            ),
            data_source=cached_data.get("data_source", "CACHE"),
            cache_status="cached",
            confidence=cached_data.get("confidence", 0.5),
        )

    async def _cache_iwm_data(self, iwm_data: IWMBenchmarkData1D) -> bool:
        """Cache IWM data"""
        try:
            cache_data = {
                "performance_1d": iwm_data.performance_1d,
                "current_price": iwm_data.current_price,
                "previous_close": iwm_data.previous_close,
                "timestamp": iwm_data.timestamp.isoformat(),
                "data_source": iwm_data.data_source,
                "confidence": iwm_data.confidence,
                "cached_at": datetime.utcnow().isoformat(),
            }

            return await self.cache_service.cache_iwm_benchmark_1d(cache_data)

        except Exception as e:
            logger.error(f"Error caching IWM data: {e}")
            return False

    async def _persist_iwm_data_if_enabled(self, iwm_data: IWMBenchmarkData1D) -> None:
        """
        Separated persistence logic for IWM benchmark data
        Non-blocking - failures don't affect main IWM calculation
        """
        try:
            success = await self.persistence.store_iwm_benchmark(iwm_data)

            if success:
                logger.debug(
                    f"Successfully persisted IWM benchmark data: {iwm_data.performance_1d:.3f}%"
                )
            else:
                logger.warning("IWM persistence failed (non-blocking)")

        except Exception as e:
            # Persistence failures are logged but don't affect IWM calculation
            logger.warning(f"IWM persistence error (non-blocking): {e}")

    def _get_neutral_benchmark(self) -> IWMBenchmarkData1D:
        """Get neutral benchmark as last resort fallback"""
        logger.warning("Using neutral IWM benchmark as fallback")
        return IWMBenchmarkData1D(
            performance_1d=0.0,
            current_price=200.0,  # Reasonable default
            previous_close=200.0,
            timestamp=datetime.utcnow(),
            data_source="FALLBACK",
            cache_status="none",
            confidence=0.1,  # Very low confidence
        )


# Global instance
_iwm_service: Optional[IWMBenchmarkService1D] = None


def get_iwm_service() -> IWMBenchmarkService1D:
    """Get global IWM service instance"""
    global _iwm_service
    if _iwm_service is None:
        _iwm_service = IWMBenchmarkService1D()
    return _iwm_service
