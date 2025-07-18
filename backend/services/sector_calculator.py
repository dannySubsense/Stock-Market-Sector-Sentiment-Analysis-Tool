"""
Sector Performance Calculator - Slice 1A Implementation
Calculates sector sentiment with multi-timeframe analysis and color classification
Uses volume-weighted analysis and volatility multipliers from SDD
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import asyncio
import logging
from datetime import datetime, timedelta
import json

from core.database import SessionLocal
from models.sector_sentiment import SectorSentiment, ColorClassification
from models.stock_universe import StockUniverse
from models.stock_data import StockData
from mcp.polygon_client import get_polygon_client
from mcp.fmp_client import get_fmp_client
from config.volatility_weights import get_weight_for_sector

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

    def __init__(self):
        self.polygon_client = get_polygon_client()
        self.fmp_client = get_fmp_client()
        self.russell_2000_symbol = "IWM"  # Russell 2000 ETF for benchmark

    async def calculate_all_sectors(self) -> Dict[str, Any]:
        """Calculate sentiment for all 8 sectors"""
        try:
            logger.info("Starting sector sentiment calculation for all sectors")

            # Get all sectors from universe
            sectors = await self._get_active_sectors()
            logger.info(f"Calculating sentiment for {len(sectors)} sectors")

            results = {}
            russell_benchmark = await self._get_russell_2000_performance()

            for sector in sectors:
                try:
                    result = await self.calculate_sector_sentiment(
                        sector, russell_benchmark
                    )
                    results[sector] = result
                    logger.info(
                        f"Calculated sentiment for {sector}: {result.get('sentiment_score', 0):.3f}"
                    )
                except Exception as e:
                    logger.error(f"Error calculating sentiment for {sector}: {e}")
                    results[sector] = self._get_default_sector_result(sector)

            # Update database with results
            await self._update_sector_sentiment_table(results)

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
                    .filter(StockUniverse.is_active == True)
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
                            StockUniverse.is_active == True,
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
        """Get current quote data for a stock"""
        try:
            # Try FMP first
            fmp_result = await self.fmp_client.get_quote(symbol)
            if fmp_result["status"] == "success" and fmp_result["quote"]:
                return fmp_result["quote"]
        except Exception as e:
            logger.warning(f"Error getting quote for {symbol}: {e}")

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
        """Get Russell 2000 performance for benchmark comparison"""
        try:
            # Get IWM (Russell 2000 ETF) performance
            quote_data = await self._get_stock_quote_data(self.russell_2000_symbol)
            if quote_data:
                daily_change = quote_data.get("changesPercentage", 0)
                return {
                    "30min": daily_change * 0.3,  # Approximate
                    "1day": daily_change,
                    "3day": daily_change * 2.5,  # Approximate
                    "1week": daily_change * 4.0,  # Approximate
                }
        except Exception as e:
            logger.warning(f"Error getting Russell 2000 performance: {e}")

        # Default neutral performance
        return {"30min": 0, "1day": 0, "3day": 0, "1week": 0}

    def _calculate_russell_comparison(
        self, timeframe_scores: Dict, russell_benchmark: Optional[Dict]
    ) -> Dict[str, float]:
        """Calculate sector performance relative to Russell 2000"""
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

    async def _update_sector_sentiment_table(
        self, sector_results: Dict[str, Dict]
    ) -> None:
        """Update the SectorSentiment table with calculated results"""
        try:
            with SessionLocal() as db:
                for sector, result in sector_results.items():
                    # Check if sector sentiment exists
                    existing = (
                        db.query(SectorSentiment)
                        .filter(SectorSentiment.sector == sector)
                        .first()
                    )

                    timeframe_scores = result.get("timeframe_scores", {})

                    if existing:
                        # Update existing record
                        existing.sentiment_score = result["sentiment_score"]
                        existing.color_classification = result["color_classification"]
                        existing.confidence_level = result["confidence_level"]
                        existing.timeframe_30min = timeframe_scores.get("30min", 0)
                        existing.timeframe_1day = timeframe_scores.get("1day", 0)
                        existing.timeframe_3day = timeframe_scores.get("3day", 0)
                        existing.timeframe_1week = timeframe_scores.get("1week", 0)
                        existing.last_updated = datetime.utcnow()
                    else:
                        # Create new record
                        new_sentiment = SectorSentiment(
                            sector=sector,
                            sentiment_score=result["sentiment_score"],
                            color_classification=result["color_classification"],
                            confidence_level=result["confidence_level"],
                            timeframe_30min=timeframe_scores.get("30min", 0),
                            timeframe_1day=timeframe_scores.get("1day", 0),
                            timeframe_3day=timeframe_scores.get("3day", 0),
                            timeframe_1week=timeframe_scores.get("1week", 0),
                            last_updated=datetime.utcnow(),
                        )
                        db.add(new_sentiment)

                db.commit()
                logger.info(
                    f"Updated sector sentiment for {len(sector_results)} sectors"
                )

        except Exception as e:
            logger.error(f"Failed to update sector sentiment table: {e}")


# Global instance
_sector_calculator: Optional[SectorPerformanceCalculator] = None


def get_sector_calculator() -> SectorPerformanceCalculator:
    """Get global sector calculator instance"""
    global _sector_calculator
    if _sector_calculator is None:
        _sector_calculator = SectorPerformanceCalculator()
    return _sector_calculator
