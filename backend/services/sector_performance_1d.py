"""
1D Sector Performance Calculator - Mathematical Implementation
Implements exact formulas defined in 1D_Performance_Calculation_Specification.md
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import time


logger = logging.getLogger(__name__)


@dataclass
class StockData1D:
    """Individual stock data for 1D calculation"""

    symbol: str
    current_price: float
    previous_close: float
    current_volume: int
    avg_20_day_volume: int
    sector: str


@dataclass
class SectorPerformance1D:
    """1D sector performance calculation result"""

    # Core performance data
    sector_name: str
    performance_1d: float  # Final sector performance percentage
    timestamp: datetime

    # Benchmark comparison
    iwm_benchmark: float  # IWM 1D performance
    alpha: float  # Sector performance - IWM performance
    relative_strength: str  # STRONG_OUTPERFORM, OUTPERFORM, etc.

    # Calculation metadata
    stock_count: int  # Number of stocks included
    confidence: float  # 0.0 to 1.0 based on data quality
    volatility_multiplier: float  # Applied multiplier

    # Data quality indicators
    avg_volume_weight: float  # Average volume weight applied
    data_coverage: float  # Percentage of universe with valid data
    calculation_time: float  # Seconds to calculate


class SectorPerformanceCalculator1D:
    """
    1D Sector Performance Calculator
    Implements mathematical formulas from specification document
    """

    # Volume weighting constraints
    MIN_VOLUME_WEIGHT = 0.1  # Minimum volume weight
    MAX_VOLUME_WEIGHT = 10.0  # Maximum volume weight
    MIN_STOCKS_FOR_CONFIDENCE = 3  # Minimum stocks for high confidence

    # Mathematical constants
    MAX_PERFORMANCE_CHANGE = 50.0  # Cap extreme moves at ±50%

    def __init__(self, volatility_multipliers: Dict[str, float]):
        """
        Initialize calculator with sector volatility multipliers

        Args:
            volatility_multipliers: Dict mapping sector names to multipliers
        """
        self.volatility_multipliers = volatility_multipliers
        self._validate_volatility_multipliers()

        # Initialize IWM service immediately - fail fast if issues
        try:
            from services.iwm_benchmark_service_1d import get_iwm_service

            self._iwm_service = get_iwm_service()
        except ImportError as e:
            raise ImportError(f"Failed to initialize IWM service: {e}")

    def _validate_volatility_multipliers(self) -> None:
        """Validate volatility multipliers are within acceptable range"""
        for sector, multiplier in self.volatility_multipliers.items():
            if not (0.5 <= multiplier <= 2.0):
                raise ValueError(
                    f"Volatility multiplier for {sector} ({multiplier}) "
                    f"outside range 0.5-2.0"
                )

    def calculate_stock_performance(self, stock_data: StockData1D) -> float:
        """
        Calculate individual stock 1D performance
        Formula: (current_price - previous_close) / previous_close * 100

        Args:
            stock_data: Stock price and volume data

        Returns:
            Stock performance percentage (capped at ±50%)
        """
        # Input validation
        if stock_data.current_price <= 0:
            raise ValueError(
                f"Invalid current price for {stock_data.symbol}: "
                f"{stock_data.current_price}"
            )
        if stock_data.previous_close <= 0:
            raise ValueError(
                f"Invalid previous close for {stock_data.symbol}: "
                f"{stock_data.previous_close}"
            )

        # Calculate raw performance
        raw_performance = (
            (stock_data.current_price - stock_data.previous_close)
            / stock_data.previous_close
            * 100
        )

        # Apply performance cap from specification
        capped_performance = max(
            -self.MAX_PERFORMANCE_CHANGE,
            min(self.MAX_PERFORMANCE_CHANGE, raw_performance),
        )

        return round(capped_performance, 3)  # 3 decimal places per spec

    def calculate_volume_weight(self, stock_data: StockData1D) -> float:
        """
        Calculate volume weighting for stock
        Formula: volume_weight = min(max(current_volume / avg_volume, 0.1), 10.0)

        Args:
            stock_data: Stock data with volume information

        Returns:
            Volume weight between 0.1 and 10.0
        """
        # Handle edge cases
        if stock_data.current_volume == 0:
            return 1.0  # Use neutral weight for zero volume

        if stock_data.avg_20_day_volume <= 0:
            return 1.0  # Use neutral weight if no average volume

        # Calculate volume ratio
        volume_ratio = stock_data.current_volume / stock_data.avg_20_day_volume

        # Apply caps from specification
        volume_weight = max(
            self.MIN_VOLUME_WEIGHT, min(self.MAX_VOLUME_WEIGHT, volume_ratio)
        )

        return round(volume_weight, 3)

    def calculate_sector_aggregation(
        self, stocks_data: List[StockData1D], sector_name: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Aggregate individual stock performances into sector performance

        Args:
            stocks_data: List of stock data for the sector
            sector_name: Sector name for volatility multiplier lookup

        Returns:
            Tuple of (final_sector_performance, metadata_dict)
        """
        if not stocks_data:
            return 0.0, {"error": "No stocks provided for sector"}

        total_weighted_performance = 0.0
        total_weights = 0.0
        valid_stocks = 0
        volume_weights = []

        for stock_data in stocks_data:
            try:
                # Calculate individual stock performance
                stock_performance = self.calculate_stock_performance(stock_data)
                volume_weight = self.calculate_volume_weight(stock_data)

                # Apply volume weighting
                weighted_performance = stock_performance * volume_weight

                total_weighted_performance += weighted_performance
                total_weights += volume_weight
                volume_weights.append(volume_weight)
                valid_stocks += 1

            except Exception as e:
                logger.warning(
                    f"Error calculating performance for {stock_data.symbol}: {e}"
                )
                continue

        if total_weights == 0 or valid_stocks == 0:
            return 0.0, {"error": "No valid stocks for aggregation"}

        # Calculate sector raw performance
        sector_raw_performance = total_weighted_performance / total_weights

        # Apply volatility multiplier
        volatility_multiplier = self.volatility_multipliers.get(sector_name, 1.0)
        sector_final_performance = sector_raw_performance * volatility_multiplier

        # Calculate metadata
        metadata = {
            "valid_stocks": valid_stocks,
            "total_stocks": len(stocks_data),
            "avg_volume_weight": (
                sum(volume_weights) / len(volume_weights) if volume_weights else 1.0
            ),
            "volatility_multiplier": volatility_multiplier,
            "data_coverage": valid_stocks / len(stocks_data) if stocks_data else 0.0,
        }

        return round(sector_final_performance, 3), metadata

    def calculate_iwm_benchmark(self, iwm_current: float, iwm_previous: float) -> float:
        """
        ADAPTER METHOD - Delegates to IWM Benchmark Service

        Args:
            iwm_current: Current IWM price
            iwm_previous: Previous close IWM price

        Returns:
            IWM performance percentage
        """
        return self._iwm_service.calculate_iwm_benchmark(iwm_current, iwm_previous)

    def classify_relative_strength(self, alpha: float) -> str:
        """
        ADAPTER METHOD - Delegates to IWM Benchmark Service

        Args:
            alpha: Sector performance - IWM performance

        Returns:
            Relative strength classification string
        """
        return self._iwm_service.classify_relative_strength(alpha)

    def calculate_confidence(self, metadata: Dict[str, float]) -> float:
        """
        Calculate confidence score based on data quality

        Args:
            metadata: Dictionary with calculation metadata

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence on data coverage
        data_coverage = metadata.get("data_coverage", 0.0)
        valid_stocks = metadata.get("valid_stocks", 0)

        # Reduce confidence if too few stocks
        stock_confidence = min(1.0, valid_stocks / self.MIN_STOCKS_FOR_CONFIDENCE)

        # Combine factors
        confidence = (data_coverage * 0.7) + (stock_confidence * 0.3)

        return round(max(0.0, min(1.0, confidence)), 3)

    def calculate_sector_performance_1d(
        self,
        stocks_data: List[StockData1D],
        sector_name: str,
        iwm_current: float,
        iwm_previous: float,
    ) -> SectorPerformance1D:
        """
        Complete 1D sector performance calculation

        Args:
            stocks_data: List of stock data for the sector
            sector_name: Sector name
            iwm_current: Current IWM price
            iwm_previous: Previous IWM close

        Returns:
            Complete sector performance calculation result
        """
        start_time = time.time()

        try:
            # Calculate sector performance
            sector_performance, metadata = self.calculate_sector_aggregation(
                stocks_data, sector_name
            )

            # Calculate IWM benchmark
            iwm_benchmark = self.calculate_iwm_benchmark(iwm_current, iwm_previous)

            # Calculate alpha and relative strength
            alpha = sector_performance - iwm_benchmark
            relative_strength = self.classify_relative_strength(alpha)

            # Calculate confidence
            confidence = self.calculate_confidence(metadata)

            # Calculate timing
            calculation_time = time.time() - start_time

            return SectorPerformance1D(
                sector_name=sector_name,
                performance_1d=sector_performance,
                timestamp=datetime.utcnow(),
                iwm_benchmark=iwm_benchmark,
                alpha=round(alpha, 3),
                relative_strength=relative_strength,
                stock_count=int(metadata.get("valid_stocks", 0)),
                confidence=confidence,
                volatility_multiplier=metadata.get("volatility_multiplier", 1.0),
                avg_volume_weight=metadata.get("avg_volume_weight", 1.0),
                data_coverage=metadata.get("data_coverage", 0.0),
                calculation_time=round(calculation_time, 3),
            )

        except Exception as e:
            logger.error(f"Error calculating 1D performance for {sector_name}: {e}")
            raise
