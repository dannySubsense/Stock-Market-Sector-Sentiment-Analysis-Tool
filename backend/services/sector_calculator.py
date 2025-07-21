"""
Sector Calculator - Core sector sentiment analysis engine
Implements sector performance calculation with volume weighting and Russell 2000 benchmarking
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.database import SessionLocal
from models.sector_sentiment import SectorSentiment, ColorClassification
from models.stock_universe import StockUniverse
from sqlalchemy import and_
from mcp.fmp_client import get_fmp_client
from mcp.polygon_client import get_polygon_client
from config.volatility_weights import get_weight_for_sector
from services.iwm_benchmark_service_1d import get_iwm_service
from services.persistence_interface import PersistenceLayer

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

# Timeframe weights for final scoring
TIMEFRAME_WEIGHTS = {
    "30min": 0.25,  # Current momentum
    "1day": 0.40,  # Most important for daily traders
    "3day": 0.25,  # Recent trend
    "1week": 0.10,  # Background context
}


class SectorPerformanceCalculator:
    """
    Calculates sector sentiment using multi-timeframe analysis
    Implements volume weighting and volatility multipliers from SDD
    """

    def __init__(self, persistence_layer: Optional[PersistenceLayer] = None):
        """
        Initialize sector calculator with optional persistence

        Args:
            persistence_layer: Optional persistence implementation for data storage
                              If None, uses database persistence by default
        """
        self.polygon_client = get_polygon_client()
        self.fmp_client = get_fmp_client()

        # Initialize IWM service immediately - fail fast if issues
        try:
            self._iwm_service = get_iwm_service()
        except ImportError as e:
            raise ImportError(f"Failed to initialize IWM service: {e}")

        # Dependency injection for persistence (enables testing and flexibility)
        from services.persistence_interface import (
            PersistenceLayer,
            get_persistence_layer,
        )

        self.persistence = persistence_layer or get_persistence_layer(
            enable_database=True
        )

    async def calculate_all_sectors(self) -> Dict[str, Any]:
        """Calculate sentiment for all 8 sectors with separated persistence"""
        try:
            logger.info("Starting sector sentiment calculation for all sectors")

            # Get all sectors from universe
            sectors = await self._get_active_sectors()
            logger.info(f"Calculating sentiment for {len(sectors)} sectors")

            results = {}
            # Get Russell 2000 benchmark using consolidated service
            russell_benchmark = await self._get_russell_2000_performance()

            # Pure calculation logic (separated from persistence)
            for sector in sectors:
                logger.info(f"Analyzing sector: {sector}")
                sector_result = await self.calculate_sector_sentiment(
                    sector, russell_benchmark
                )
                results[sector] = sector_result

            # Separated persistence logic - non-blocking
            await self._persist_sector_analysis_if_enabled(
                results, russell_benchmark, sectors
            )

            return {
                "status": "success",
                "sectors": results,
                "benchmark": russell_benchmark,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to calculate all sectors: {e}")
            return {"status": "error", "message": str(e), "sectors": {}}

    async def calculate_sector_sentiment(
        self, sector: str, russell_benchmark: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Calculate sentiment for a specific sector"""
        try:
            # Get stocks in this sector
            sector_stocks = await self._get_sector_stocks(sector)
            if not sector_stocks:
                return self._get_default_sector_result(sector)

            # Get performance data for all timeframes
            performance_data = await self._get_multi_timeframe_performance(
                sector_stocks, sector
            )

            # Calculate volume-weighted performance for each timeframe
            timeframe_scores = {}
            for timeframe in ["30min", "1day", "3day", "1week"]:
                timeframe_scores[timeframe] = (
                    await self._calculate_timeframe_performance(
                        performance_data, timeframe, sector
                    )
                )

            # Calculate final weighted sentiment score
            final_score = self._calculate_final_sentiment_score(timeframe_scores)

            # Classify color and trading signal
            color_classification = self._classify_sentiment_color(final_score)
            trading_signal = TRADING_SIGNALS[color_classification]

            # Calculate confidence level
            confidence = self._calculate_confidence_level(
                timeframe_scores, performance_data
            )

            # Get Russell 2000 comparison
            # Calculate Russell comparison using consolidated service
            russell_comparison = self._calculate_russell_comparison(
                timeframe_scores, russell_benchmark
            )

            return {
                "sector": sector,
                "sentiment_score": final_score,
                "color_classification": color_classification.value,
                "trading_signal": trading_signal,
                "confidence_level": confidence,
                "timeframe_scores": timeframe_scores,
                "russell_comparison": russell_comparison,
                "stock_count": len(sector_stocks),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to calculate sentiment for {sector}: {e}")
            return self._get_default_sector_result(sector)

    async def _get_active_sectors(self) -> List[str]:
        """Get list of active sectors from stock universe"""
        try:
            with SessionLocal() as db:
                sectors = (
                    db.query(StockUniverse.sector)
                    .filter(StockUniverse.is_active)
                    .distinct()
                    .all()
                )
                return [sector[0] for sector in sectors]
        except Exception as e:
            logger.error(f"Error getting active sectors: {e}")
            # Return default 8 sectors from SDD
            return [
                "technology",
                "healthcare",
                "energy",
                "financial",
                "consumer_discretionary",
                "industrials",
                "materials",
                "utilities",
            ]

    async def _get_sector_stocks(self, sector: str) -> List[StockUniverse]:
        """Get all active stocks in a sector"""
        try:
            with SessionLocal() as db:
                stocks = (
                    db.query(StockUniverse)
                    .filter(
                        and_(
                            StockUniverse.sector == sector,
                            StockUniverse.is_active,
                        )
                    )
                    .all()
                )
                return stocks
        except Exception as e:
            logger.error(f"Error getting stocks for sector {sector}: {e}")
            return []

    async def _get_multi_timeframe_performance(
        self, stocks: List[StockUniverse], sector: str
    ) -> Dict[str, Dict]:
        """Get performance data for all stocks across multiple timeframes"""
        performance_data = {}

        for stock in stocks:
            try:
                symbol = stock.symbol

                # Get quote data for current performance
                quote_data = await self._get_stock_quote_data(symbol)
                if not quote_data:
                    continue

                # Get historical data for timeframe calculations
                historical_data = await self._get_historical_data(symbol)

                # Calculate performance for each timeframe
                stock_performance = {
                    "symbol": symbol,
                    "current_price": quote_data.get("price", 0),
                    "volume": quote_data.get("volume", 0),
                    "avg_volume": quote_data.get(
                        "avgVolume", quote_data.get("volume", 0)
                    ),
                    "volatility_multiplier": get_weight_for_sector(sector),
                    "market_cap": stock.market_cap,
                }

                # Calculate timeframe performances
                stock_performance.update(
                    self._calculate_timeframe_changes(historical_data, quote_data)
                )

                performance_data[symbol] = stock_performance

            except Exception as e:
                logger.warning(f"Error getting performance for {stock.symbol}: {e}")
                continue

        return performance_data

    async def _get_stock_quote_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote data for a stock from stored price data first, then API fallback"""
        try:
            # First try to get data from stock_prices_1d table (FAST - no API calls)
            stored_data = await self._get_stored_price_data(symbol)
            if stored_data:
                return stored_data

            # Fallback to API only if no stored data available
            logger.debug(f"No stored data for {symbol}, falling back to API")

            # Try FMP API
            fmp_result = await self.fmp_client.get_quote(symbol)
            if fmp_result["status"] == "success" and fmp_result["quote"]:
                return fmp_result["quote"]

        except Exception as e:
            logger.warning(f"Error getting quote for {symbol}: {e}")

        return None

    async def _get_stored_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the most recent price data from stock_prices_1d table"""
        try:
            with SessionLocal() as db:
                from models.stock_data import StockPrice1D
                from sqlalchemy import desc

                # Get the most recent price record for this symbol
                recent_price = (
                    db.query(StockPrice1D)
                    .filter(StockPrice1D.symbol == symbol)
                    .order_by(desc(StockPrice1D.timestamp))
                    .first()
                )

                if recent_price:
                    # Convert to format expected by sector calculator
                    return {
                        "symbol": recent_price.symbol,
                        "price": recent_price.close_price,
                        "volume": recent_price.volume,
                        "open": recent_price.open_price,
                        "high": recent_price.high_price,
                        "low": recent_price.low_price,
                        "avgVolume": recent_price.volume,  # Use current volume as proxy
                        "timestamp": recent_price.timestamp.isoformat(),
                    }

        except Exception as e:
            logger.debug(f"Error getting stored price data for {symbol}: {e}")

        return None

    async def _get_historical_data(self, symbol: str) -> Dict[str, Any]:
        """Get historical price data for timeframe calculations"""
        try:
            # For now, use current quote data - in production would get actual historical data
            # This is a simplified implementation for Slice 1A
            quote_data = await self._get_stock_quote_data(symbol)
            if quote_data:
                # Simulate historical data based on daily change
                current_price = quote_data.get("price", 0)
                daily_change = quote_data.get("change", 0)
                previous_close = quote_data.get(
                    "previousClose", current_price - daily_change
                )

                return {
                    "current": current_price,
                    "previous_close": previous_close,
                    "1day_ago": previous_close,
                    "3day_ago": previous_close * 0.98,  # Simplified approximation
                    "1week_ago": previous_close * 0.95,  # Simplified approximation
                }
        except Exception as e:
            logger.warning(f"Error getting historical data for {symbol}: {e}")

        return {}

    def _calculate_timeframe_changes(
        self, historical_data: Dict, quote_data: Dict
    ) -> Dict[str, float]:
        """Calculate percentage changes for each timeframe"""
        if not historical_data:
            return {"30min": 0, "1day": 0, "3day": 0, "1week": 0}

        current_price = historical_data.get("current", 0)

        # Calculate changes (simplified for Slice 1A)
        changes = {}

        # 30min change (use intraday data if available, otherwise estimate)
        changes["30min"] = quote_data.get("changesPercentage", 0) * 0.3  # Approximate

        # 1 day change
        day_ago_price = historical_data.get("1day_ago", current_price)
        if day_ago_price > 0:
            changes["1day"] = ((current_price - day_ago_price) / day_ago_price) * 100
        else:
            changes["1day"] = 0

        # 3 day change
        three_day_price = historical_data.get("3day_ago", current_price)
        if three_day_price > 0:
            changes["3day"] = (
                (current_price - three_day_price) / three_day_price
            ) * 100
        else:
            changes["3day"] = 0

        # 1 week change
        week_price = historical_data.get("1week_ago", current_price)
        if week_price > 0:
            changes["1week"] = ((current_price - week_price) / week_price) * 100
        else:
            changes["1week"] = 0

        return changes

    async def _calculate_timeframe_performance(
        self, performance_data: Dict, timeframe: str, sector: str
    ) -> float:
        """Calculate volume-weighted performance for a timeframe"""
        if not performance_data:
            return 0.0

        total_weighted_performance = 0.0
        total_weight = 0.0

        for symbol, data in performance_data.items():
            try:
                # Get timeframe performance
                performance = data.get(timeframe, 0)
                volume = data.get("volume", 0)
                avg_volume = data.get("avg_volume", volume)
                volatility_multiplier = data.get("volatility_multiplier", 1.0)

                # Calculate volume weight (higher volume = more weight)
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                volume_weight = min(volume_ratio, 3.0)  # Cap at 3x weight

                # Apply volatility multiplier for sector
                adjusted_performance = performance * volatility_multiplier

                # Weight by volume and add to totals
                weighted_performance = adjusted_performance * volume_weight
                total_weighted_performance += weighted_performance
                total_weight += volume_weight

            except Exception as e:
                logger.warning(f"Error calculating performance for {symbol}: {e}")
                continue

        # Calculate average weighted performance
        if total_weight > 0:
            avg_performance = total_weighted_performance / total_weight
            # Normalize to -1.0 to +1.0 scale
            return max(-1.0, min(1.0, avg_performance / 100.0))

        return 0.0

    def _calculate_final_sentiment_score(
        self, timeframe_scores: Dict[str, float]
    ) -> float:
        """Calculate final weighted sentiment score"""
        final_score = 0.0

        for timeframe, score in timeframe_scores.items():
            weight = TIMEFRAME_WEIGHTS.get(timeframe, 0)
            final_score += score * weight

        # Ensure score is within bounds
        return max(-1.0, min(1.0, final_score))

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

    def _calculate_confidence_level(
        self, timeframe_scores: Dict[str, float], performance_data: Dict
    ) -> float:
        """Calculate confidence level based on score consistency and data quality"""
        try:
            # Check consistency across timeframes
            scores = list(timeframe_scores.values())
            if not scores:
                return 0.5

            # Calculate variance (lower variance = higher confidence)
            mean_score = sum(scores) / len(scores)
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            consistency_factor = max(0.0, 1.0 - variance)

            # Check data quality (more stocks = higher confidence)
            data_quality_factor = min(
                1.0, len(performance_data) / 50.0
            )  # Normalize to 50 stocks

            # Combine factors
            confidence = (consistency_factor * 0.7) + (data_quality_factor * 0.3)

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.5

    async def _get_russell_2000_performance(self) -> Dict[str, float]:
        """
        ADAPTER METHOD - Delegates to IWM Benchmark Service

        Returns:
            Dictionary with Russell 2000 performance across timeframes
        """
        return await self._iwm_service.get_russell_2000_performance()

    def _calculate_russell_comparison(
        self, sector_performance: float, timeframe: str
    ) -> float:
        """
        ADAPTER METHOD - Delegates to IWM Benchmark Service
        """
        return self._iwm_service.calculate_russell_comparison(
            sector_performance, timeframe
        )

    def _get_default_sector_result(self, sector: str) -> Dict[str, Any]:
        """Get default result for sector with no data"""
        return {
            "sector": sector,
            "sentiment_score": 0.0,
            "color_classification": ColorClassification.BLUE_NEUTRAL.value,
            "trading_signal": TRADING_SIGNALS[ColorClassification.BLUE_NEUTRAL],
            "confidence_level": 0.0,
            "timeframe_scores": {"30min": 0, "1day": 0, "3day": 0, "1week": 0},
            "russell_comparison": {"30min": 0, "1day": 0, "3day": 0, "1week": 0},
            "stock_count": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def _persist_sector_analysis_if_enabled(
        self,
        results: Dict[str, Any],
        russell_benchmark: Dict[str, Any],
        sectors: List[str],
    ) -> None:
        """
        Separated persistence logic for complete sector analysis
        Non-blocking - failures don't affect main calculation
        """
        try:
            analysis_metadata = {
                "trigger": "background_analysis",
                "russell_benchmark": russell_benchmark,
                "sectors_analyzed": len(sectors),
                "timestamp": datetime.utcnow().isoformat(),
            }

            success = await self.persistence.store_sector_sentiment(
                results, analysis_metadata
            )

            if success:
                logger.info(
                    f"Successfully persisted complete sector analysis for {len(results)} sectors"
                )
            else:
                logger.warning("Sector analysis persistence failed (non-blocking)")

        except Exception as e:
            # Persistence failures are logged but don't affect main calculation
            logger.warning(f"Sector analysis persistence error (non-blocking): {e}")


# Global instance
_sector_calculator: Optional[SectorPerformanceCalculator] = None


def get_sector_calculator() -> SectorPerformanceCalculator:
    """Get global sector calculator instance"""
    global _sector_calculator
    if _sector_calculator is None:
        _sector_calculator = SectorPerformanceCalculator()
    return _sector_calculator
