"""
1D Volume Weighting Engine - Step 3 Implementation
Calculates volume-weighted sector sentiment for 1D timeframe only
Implements robust volume ratio calculation with edge case handling
Uses dependency injection for clean separation of concerns
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

from config.volatility_weights import get_weight_for_sector
from services.persistence_interface import PersistenceLayer, get_persistence_layer

logger = logging.getLogger(__name__)

# Volume weighting configuration
VOLUME_RATIO_MIN = 0.1  # Minimum volume ratio (10% of average)
VOLUME_RATIO_MAX = 10.0  # Maximum volume ratio (10x average)
VOLUME_RATIO_CAP = 3.0  # Cap volume weighting at 3x
MIN_VOLUME_THRESHOLD = 1000  # Minimum daily volume to include stock
DEFAULT_AVG_VOLUME_MULTIPLIER = 1.0  # If no average volume data
OUTLIER_DETECTION_THRESHOLD = 5.0  # Mark as outlier if > 5x average


@dataclass
class StockVolumeData:
    """Stock volume data for weighting calculations"""

    symbol: str
    current_volume: int
    avg_volume_20d: Optional[int]
    price_change_1d: float  # Percentage change
    market_cap: Optional[float] = None

    @property
    def volume_ratio(self) -> float:
        """Calculate current volume vs 20-day average ratio"""
        if not self.avg_volume_20d or self.avg_volume_20d <= 0:
            return DEFAULT_AVG_VOLUME_MULTIPLIER

        ratio = self.current_volume / self.avg_volume_20d
        # Apply bounds to prevent extreme values
        return max(VOLUME_RATIO_MIN, min(VOLUME_RATIO_MAX, ratio))

    @property
    def is_sufficient_volume(self) -> bool:
        """Check if stock has sufficient volume for inclusion"""
        return self.current_volume >= MIN_VOLUME_THRESHOLD

    @property
    def is_volume_outlier(self) -> bool:
        """Detect if current volume is an extreme outlier"""
        if not self.avg_volume_20d or self.avg_volume_20d <= 0:
            return False
        return self.current_volume > (self.avg_volume_20d * OUTLIER_DETECTION_THRESHOLD)


@dataclass
class WeightedSectorResult:
    """Result of volume-weighted sector calculation"""

    sector: str
    weighted_performance: float
    total_weight: float
    stock_count: int
    outlier_count: int
    volatility_multiplier: float
    confidence_score: float


class VolumeWeightingEngine1D:
    """
    1D Volume Weighting Engine with separated concerns
    Calculates volume-weighted sector sentiment with optional data persistence
    """

    def __init__(self, persistence_layer: Optional[PersistenceLayer] = None):
        """
        Initialize volume weighting engine with optional persistence

        Args:
            persistence_layer: Optional persistence implementation for data storage
                              If None, uses database persistence by default
        """
        self.persistence = persistence_layer or get_persistence_layer(
            enable_database=True
        )
        self.logger = logging.getLogger(__name__)

    async def calculate_weighted_sector_sentiment(
        self, sector: str, stock_volume_data: List[StockVolumeData]
    ) -> WeightedSectorResult:
        """
        Calculate volume-weighted sector sentiment for 1D timeframe
        Pure calculation logic separated from persistence concerns

        Args:
            sector: Sector name for analysis
            stock_volume_data: List of stock volume data for the sector

        Returns:
            WeightedSectorResult with volume-weighted sentiment calculation
        """
        # PURE CALCULATION LOGIC (easily testable, no side effects)
        result = await self._perform_volume_weighting_calculation(
            sector, stock_volume_data
        )

        # SEPARATED PERSISTENCE (optional, non-blocking, can be mocked)
        await self._persist_data_if_enabled(stock_volume_data, sector)

        return result

    async def _perform_volume_weighting_calculation(
        self, sector: str, stock_volume_data: List[StockVolumeData]
    ) -> WeightedSectorResult:
        """
        Pure volume weighting calculation logic - no side effects
        Easily testable without database dependencies
        """
        # Filter out stocks with insufficient volume
        valid_stocks = [
            stock for stock in stock_volume_data if stock.is_sufficient_volume
        ]

        if not valid_stocks:
            logger.warning(
                f"No valid stocks with sufficient volume for sector {sector}"
            )
            return self._create_empty_result(sector)

        # Calculate volume-weighted performance
        total_weighted_performance = 0.0
        total_weights = 0.0
        outlier_count = 0

        for stock in valid_stocks:
            # Get volume weight with bounds checking
            volume_weight = self._calculate_volume_weight(stock)

            # Track outliers for analysis quality
            if stock.is_volume_outlier:
                outlier_count += 1
                logger.debug(
                    f"Volume outlier detected: {stock.symbol} ({stock.volume_ratio:.2f}x average)"
                )

            # Apply weight to performance
            weighted_performance = stock.price_change_1d * volume_weight
            total_weighted_performance += weighted_performance
            total_weights += volume_weight

        # Calculate average weighted performance
        if total_weights > 0:
            sector_performance = total_weighted_performance / total_weights
        else:
            logger.warning(f"Zero total weights for sector {sector}")
            return self._create_empty_result(sector)

        # Apply sector volatility multiplier
        volatility_multiplier = get_weight_for_sector(sector)
        final_performance = sector_performance * volatility_multiplier

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence_score(
            valid_stocks, outlier_count, total_weights
        )

        return WeightedSectorResult(
            sector=sector,
            weighted_performance=final_performance,
            total_weight=total_weights,
            stock_count=len(valid_stocks),
            outlier_count=outlier_count,
            volatility_multiplier=volatility_multiplier,
            confidence_score=confidence,
        )

    async def _persist_data_if_enabled(
        self, stock_volume_data: List[StockVolumeData], sector: str
    ) -> None:
        """
        Separated persistence logic - non-blocking and optional
        Failures in persistence do not affect calculation results
        """
        try:
            # Convert to format expected by persistence layer
            stock_data_list = self._convert_to_stock_data_1d(stock_volume_data)

            # Attempt to persist (non-blocking for main calculation)
            success = await self.persistence.store_stock_data(stock_data_list)

            if success:
                logger.debug(
                    f"Successfully persisted {len(stock_data_list)} stock records for sector {sector}"
                )
            else:
                logger.warning(f"Persistence failed for sector {sector} (non-blocking)")

        except Exception as e:
            # Persistence failures are logged but don't affect main calculation
            logger.warning(f"Persistence error for sector {sector} (non-blocking): {e}")

    def _convert_to_stock_data_1d(
        self, stock_volume_data: List[StockVolumeData]
    ) -> List:
        """
        Convert StockVolumeData to StockData1D format for persistence

        Args:
            stock_volume_data: Volume data from calculation

        Returns:
            List of StockData1D objects for persistence
        """
        from services.sector_performance_1d import StockData1D

        stock_data_list = []
        for stock in stock_volume_data:
            if stock.is_sufficient_volume:  # Only store stocks with sufficient volume
                # Calculate current price from percentage change
                # This is an approximation - in real implementation you'd have actual prices
                estimated_previous_close = 100.0  # Placeholder - would come from API
                estimated_current_price = estimated_previous_close * (
                    1 + stock.price_change_1d / 100
                )

                stock_data_1d = StockData1D(
                    symbol=stock.symbol,
                    current_price=estimated_current_price,
                    previous_close=estimated_previous_close,
                    current_volume=stock.current_volume,
                    avg_20_day_volume=stock.avg_volume_20d or stock.current_volume,
                    sector="",  # Will be populated later
                )
                stock_data_list.append(stock_data_1d)

        return stock_data_list

    def _calculate_volume_weight(self, stock: StockVolumeData) -> float:
        """
        Calculate volume weight for a stock with proper bounds

        Args:
            stock: Stock volume data

        Returns:
            Volume weight (capped at VOLUME_RATIO_CAP)
        """
        try:
            # Handle edge cases first
            if stock.current_volume <= 0:
                return 0.0  # Zero weight for zero volume

            # Calculate base volume ratio
            volume_ratio = stock.volume_ratio

            # Apply volume weight cap to prevent extreme weighting
            volume_weight = min(volume_ratio, VOLUME_RATIO_CAP)

            # Ensure minimum weight for valid stocks
            return max(0.1, volume_weight)

        except Exception as e:
            self.logger.warning(
                f"Error calculating volume weight for {stock.symbol}: {e}"
            )
            return 1.0  # Default weight on error

    def _calculate_confidence_score(
        self,
        valid_stocks: List[StockVolumeData],
        outlier_count: int,
        total_weight: float,
    ) -> float:
        """
        Calculate confidence score based on data quality metrics

        Args:
            valid_stocks: List of stocks with sufficient volume
            outlier_count: Number of volume outliers
            total_weight: Total volume weight

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not valid_stocks:
                return 0.0

            # Base confidence from stock count (more stocks = higher confidence)
            stock_count_factor = min(1.0, len(valid_stocks) / 20.0)

            # Penalize high outlier ratio
            outlier_ratio = outlier_count / len(valid_stocks)
            outlier_penalty = max(0.0, 1.0 - (outlier_ratio * 2))

            # Reward balanced volume weighting (avoid extreme concentration)
            if total_weight > 0:
                avg_weight = total_weight / len(valid_stocks)
                weight_balance_factor = min(1.0, avg_weight / 2.0)
            else:
                weight_balance_factor = 0.0

            # Check volume data availability
            stocks_with_avg_volume = sum(
                1
                for stock in valid_stocks
                if stock.avg_volume_20d and stock.avg_volume_20d > 0
            )
            data_quality_factor = stocks_with_avg_volume / len(valid_stocks)

            # Combine factors with weights
            confidence = (
                stock_count_factor * 0.3
                + outlier_penalty * 0.3
                + weight_balance_factor * 0.2
                + data_quality_factor * 0.2
            )

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            self.logger.warning(f"Error calculating confidence score: {e}")
            return 0.5  # Default medium confidence

    def _create_empty_result(self, sector: str) -> WeightedSectorResult:
        """Create empty result for sectors with no valid data"""
        return WeightedSectorResult(
            sector=sector,
            weighted_performance=0.0,
            total_weight=0.0,
            stock_count=0,
            outlier_count=0,
            volatility_multiplier=get_weight_for_sector(sector),
            confidence_score=0.0,
        )

    def validate_volume_data(
        self, stock_volume_data: List[StockVolumeData]
    ) -> Tuple[List[StockVolumeData], List[str]]:
        """
        Validate and filter stock volume data

        Args:
            stock_volume_data: Raw stock volume data

        Returns:
            Tuple of (valid_stocks, error_messages)
        """
        valid_stocks = []
        errors = []

        for stock in stock_volume_data:
            try:
                # Check for required data
                if not stock.symbol:
                    errors.append("Stock missing symbol")
                    continue

                if stock.current_volume < 0:
                    errors.append(f"{stock.symbol}: Negative volume")
                    continue

                if stock.avg_volume_20d and stock.avg_volume_20d < 0:
                    errors.append(f"{stock.symbol}: Negative average volume")
                    continue

                # Check for reasonable price change (prevent data errors)
                if abs(stock.price_change_1d) > 50:  # More than 50% change
                    errors.append(
                        f"{stock.symbol}: Extreme price change {stock.price_change_1d}%"
                    )
                    # Still include but log warning

                valid_stocks.append(stock)

            except Exception as e:
                errors.append(f"{stock.symbol}: Validation error - {e}")
                continue

        return valid_stocks, errors
