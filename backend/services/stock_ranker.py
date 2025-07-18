"""
Stock Ranking Engine - Slice 1A Implementation
Ranks stocks within each sector to identify top 3 bullish/bearish
Uses gap magnitude, volume confirmation, sector alignment, and shortability
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
import asyncio
import logging
from datetime import datetime, timedelta
import json

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from models.stock_data import StockData
from models.sector_sentiment import SectorSentiment
from mcp.polygon_client import get_polygon_client
from mcp.fmp_client import get_fmp_client

logger = logging.getLogger(__name__)

# Ranking criteria weights from SDD
RANKING_WEIGHTS = {
    "gap_magnitude": 0.40,  # Biggest price moves
    "volume_confirmation": 0.30,  # Volume validation
    "sector_alignment": 0.20,  # Direction matches sector sentiment
    "shortability_score": 0.10,  # Float and liquidity for shorts
}

# Volume thresholds for confirmation
VOLUME_THRESHOLDS = {
    "high_confirmation": 2.5,  # 2.5x+ average volume
    "medium_confirmation": 1.5,  # 1.5x+ average volume
    "low_confirmation": 1.0,  # Normal volume
}


class StockRanker:
    """
    Ranks stocks within each sector for top 3 bullish/bearish identification
    Implements multi-factor scoring based on SDD criteria
    """

    def __init__(self):
        self.polygon_client = get_polygon_client()
        self.fmp_client = get_fmp_client()

    async def rank_all_sectors(self) -> Dict[str, Any]:
        """Rank stocks for all sectors"""
        try:
            logger.info("Starting stock ranking for all sectors")

            # Get all active sectors
            sectors = await self._get_active_sectors()

            results = {}
            for sector in sectors:
                try:
                    ranking_result = await self.rank_sector_stocks(sector)
                    results[sector] = ranking_result
                    logger.info(
                        f"Ranked stocks for {sector}: {len(ranking_result.get('top_bullish', []))} bullish, {len(ranking_result.get('top_bearish', []))} bearish"
                    )
                except Exception as e:
                    logger.error(f"Error ranking stocks for {sector}: {e}")
                    results[sector] = self._get_default_ranking_result(sector)

            # Update database with rankings
            await self._update_stock_rankings(results)

            # Update sector sentiment table with top stocks
            await self._update_sector_top_stocks(results)

            return {
                "status": "success",
                "sectors": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to rank all sectors: {e}")
            return {"status": "error", "message": str(e), "sectors": {}}

    async def rank_sector_stocks(self, sector: str) -> Dict[str, Any]:
        """Rank stocks within a specific sector"""
        try:
            # Get sector sentiment for alignment scoring
            sector_sentiment = await self._get_sector_sentiment(sector)

            # Get all stocks in sector with current performance data
            sector_stocks = await self._get_sector_stock_performance(sector)

            if not sector_stocks:
                return self._get_default_ranking_result(sector)

            # Calculate ranking scores for all stocks
            scored_stocks = []
            for stock_data in sector_stocks:
                score = await self._calculate_ranking_score(
                    stock_data, sector_sentiment
                )
                stock_data["ranking_score"] = score
                scored_stocks.append(stock_data)

            # Separate and rank bullish vs bearish based on sector sentiment
            top_bullish, top_bearish = self._select_top_stocks(
                scored_stocks, sector_sentiment
            )

            return {
                "sector": sector,
                "sector_sentiment": sector_sentiment,
                "total_stocks": len(scored_stocks),
                "top_bullish": top_bullish[:3],  # Top 3 bullish
                "top_bearish": top_bearish[:3],  # Top 3 bearish
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to rank stocks for {sector}: {e}")
            return self._get_default_ranking_result(sector)

    async def _get_active_sectors(self) -> List[str]:
        """Get list of active sectors"""
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

    async def _get_sector_sentiment(self, sector: str) -> Dict[str, Any]:
        """Get current sector sentiment for alignment scoring"""
        try:
            with SessionLocal() as db:
                sentiment = (
                    db.query(SectorSentiment)
                    .filter(SectorSentiment.sector == sector)
                    .first()
                )

                if sentiment:
                    return {
                        "sentiment_score": sentiment.sentiment_score,
                        "color_classification": sentiment.color_classification,
                        "is_bullish": sentiment.sentiment_score > 0,
                        "is_bearish": sentiment.sentiment_score < 0,
                    }
        except Exception as e:
            logger.error(f"Error getting sector sentiment for {sector}: {e}")

        # Default neutral sentiment
        return {
            "sentiment_score": 0.0,
            "color_classification": "blue_neutral",
            "is_bullish": False,
            "is_bearish": False,
        }

    async def _get_sector_stock_performance(self, sector: str) -> List[Dict[str, Any]]:
        """Get performance data for all stocks in sector"""
        try:
            with SessionLocal() as db:
                # Get stocks from universe
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

                stock_performance_data = []
                for stock in stocks:
                    try:
                        # Get current quote data
                        quote_data = await self._get_stock_quote_data(stock.symbol)
                        if not quote_data:
                            continue

                        # Calculate performance metrics
                        performance_data = self._calculate_stock_performance_metrics(
                            stock, quote_data
                        )
                        stock_performance_data.append(performance_data)

                    except Exception as e:
                        logger.warning(
                            f"Error getting performance for {stock.symbol}: {e}"
                        )
                        continue

                return stock_performance_data

        except Exception as e:
            logger.error(f"Error getting sector stock performance for {sector}: {e}")
            return []

    async def _get_stock_quote_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote data for ranking"""
        try:
            # Try FMP first
            fmp_result = await self.fmp_client.get_quote(symbol)
            if fmp_result["status"] == "success" and fmp_result["quote"]:
                return fmp_result["quote"]
        except Exception as e:
            logger.warning(f"Error getting quote for {symbol}: {e}")

        return None

    def _calculate_stock_performance_metrics(
        self, stock: StockUniverse, quote_data: Dict
    ) -> Dict[str, Any]:
        """Calculate performance metrics for ranking"""
        current_price = quote_data.get("price", 0)
        previous_close = quote_data.get("previousClose", current_price)
        volume = quote_data.get("volume", 0)
        avg_volume = quote_data.get("avgVolume", volume)

        # Calculate price change metrics
        price_change = current_price - previous_close
        price_change_percent = (
            (price_change / previous_close * 100) if previous_close > 0 else 0
        )

        # Calculate gap metrics (simplified for Slice 1A)
        gap_size = abs(price_change_percent)
        is_gap_up = price_change > 0

        # Calculate volume metrics
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # Calculate shortability score (simplified)
        shortability_score = self._calculate_shortability_score(
            stock, current_price, volume
        )

        return {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "current_price": current_price,
            "previous_close": previous_close,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "gap_size": gap_size,
            "is_gap_up": is_gap_up,
            "volume": volume,
            "avg_volume": avg_volume,
            "volume_ratio": volume_ratio,
            "market_cap": stock.market_cap,
            "float_shares": stock.float_shares,
            "shortability_score": shortability_score,
            "volatility_multiplier": stock.volatility_multiplier,
        }

    def _calculate_shortability_score(
        self, stock: StockUniverse, price: float, volume: int
    ) -> float:
        """Calculate shortability score (0-10 scale)"""
        try:
            score = 0.0

            # Float size factor (larger float = easier to short)
            if stock.float_shares:
                if stock.float_shares > 50_000_000:  # Large float
                    score += 3.0
                elif stock.float_shares > 20_000_000:  # Medium float
                    score += 2.0
                elif stock.float_shares > 5_000_000:  # Small float
                    score += 1.0
                # Very small float gets 0 points (harder to short)

            # Price factor (higher price = easier to short)
            if price > 10:
                score += 2.0
            elif price > 5:
                score += 1.0

            # Volume factor (higher volume = more liquid)
            if volume > 2_000_000:
                score += 2.0
            elif volume > 1_000_000:
                score += 1.0

            # Market cap factor (larger companies = easier to short)
            if stock.market_cap > 1_000_000_000:  # $1B+
                score += 2.0
            elif stock.market_cap > 500_000_000:  # $500M+
                score += 1.0

            return min(10.0, score)  # Cap at 10

        except Exception as e:
            logger.warning(f"Error calculating shortability for {stock.symbol}: {e}")
            return 5.0  # Default medium score

    async def _calculate_ranking_score(
        self, stock_data: Dict, sector_sentiment: Dict
    ) -> float:
        """Calculate composite ranking score based on SDD criteria"""
        try:
            total_score = 0.0

            # Gap magnitude score (40% weight)
            gap_score = self._calculate_gap_score(stock_data)
            total_score += gap_score * RANKING_WEIGHTS["gap_magnitude"]

            # Volume confirmation score (30% weight)
            volume_score = self._calculate_volume_score(stock_data)
            total_score += volume_score * RANKING_WEIGHTS["volume_confirmation"]

            # Sector alignment score (20% weight)
            alignment_score = self._calculate_alignment_score(
                stock_data, sector_sentiment
            )
            total_score += alignment_score * RANKING_WEIGHTS["sector_alignment"]

            # Shortability score (10% weight)
            shortability_score = (
                stock_data.get("shortability_score", 5.0) / 10.0
            )  # Normalize to 0-1
            total_score += shortability_score * RANKING_WEIGHTS["shortability_score"]

            return total_score

        except Exception as e:
            logger.warning(
                f"Error calculating ranking score for {stock_data.get('symbol', 'unknown')}: {e}"
            )
            return 0.0

    def _calculate_gap_score(self, stock_data: Dict) -> float:
        """Calculate gap magnitude score (0-1 scale)"""
        gap_size = abs(stock_data.get("price_change_percent", 0))

        if gap_size >= 30:  # Extreme gap
            return 1.0
        elif gap_size >= 15:  # Large gap
            return 0.8
        elif gap_size >= 10:  # Medium gap
            return 0.6
        elif gap_size >= 5:  # Small gap
            return 0.4
        elif gap_size >= 2:  # Minor gap
            return 0.2
        else:  # No significant gap
            return 0.0

    def _calculate_volume_score(self, stock_data: Dict) -> float:
        """Calculate volume confirmation score (0-1 scale)"""
        volume_ratio = stock_data.get("volume_ratio", 1.0)

        if volume_ratio >= VOLUME_THRESHOLDS["high_confirmation"]:
            return 1.0
        elif volume_ratio >= VOLUME_THRESHOLDS["medium_confirmation"]:
            return 0.7
        elif volume_ratio >= VOLUME_THRESHOLDS["low_confirmation"]:
            return 0.4
        else:
            return 0.0

    def _calculate_alignment_score(
        self, stock_data: Dict, sector_sentiment: Dict
    ) -> float:
        """Calculate sector alignment score (0-1 scale)"""
        stock_change = stock_data.get("price_change_percent", 0)
        is_stock_bullish = stock_change > 0
        is_stock_bearish = stock_change < 0

        sector_is_bullish = sector_sentiment.get("is_bullish", False)
        sector_is_bearish = sector_sentiment.get("is_bearish", False)

        # Perfect alignment
        if (is_stock_bullish and sector_is_bullish) or (
            is_stock_bearish and sector_is_bearish
        ):
            return 1.0

        # Opposite alignment (might be contrarian opportunity)
        if (is_stock_bullish and sector_is_bearish) or (
            is_stock_bearish and sector_is_bullish
        ):
            return 0.3

        # Neutral
        return 0.5

    def _select_top_stocks(
        self, scored_stocks: List[Dict], sector_sentiment: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """Select top bullish and bearish stocks based on sector sentiment"""
        # Sort by ranking score (highest first)
        sorted_stocks = sorted(
            scored_stocks, key=lambda x: x["ranking_score"], reverse=True
        )

        bullish_stocks = []
        bearish_stocks = []

        for stock in sorted_stocks:
            price_change = stock.get("price_change_percent", 0)

            if price_change > 0:  # Stock is up
                bullish_stocks.append(self._format_stock_for_display(stock, "bullish"))
            elif price_change < 0:  # Stock is down
                bearish_stocks.append(self._format_stock_for_display(stock, "bearish"))

        return bullish_stocks, bearish_stocks

    def _format_stock_for_display(
        self, stock_data: Dict, direction: str
    ) -> Dict[str, Any]:
        """Format stock data for frontend display"""
        return {
            "symbol": stock_data["symbol"],
            "company_name": stock_data["company_name"],
            "current_price": stock_data["current_price"],
            "price_change": stock_data["price_change"],
            "price_change_percent": stock_data["price_change_percent"],
            "volume": stock_data["volume"],
            "volume_ratio": stock_data["volume_ratio"],
            "gap_size": stock_data["gap_size"],
            "shortability_score": stock_data["shortability_score"],
            "ranking_score": stock_data["ranking_score"],
            "direction": direction,
            "market_cap": stock_data["market_cap"],
        }

    def _get_default_ranking_result(self, sector: str) -> Dict[str, Any]:
        """Get default ranking result for sector with no data"""
        return {
            "sector": sector,
            "sector_sentiment": {
                "sentiment_score": 0.0,
                "color_classification": "blue_neutral",
            },
            "total_stocks": 0,
            "top_bullish": [],
            "top_bearish": [],
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def _update_stock_rankings(self, sector_results: Dict[str, Dict]) -> None:
        """Update StockData table with ranking information"""
        try:
            with SessionLocal() as db:
                # Clear existing rankings
                db.query(StockData).update(
                    {"bullish_rank": None, "bearish_rank": None, "ranking_score": None}
                )

                for sector, results in sector_results.items():
                    # Update bullish rankings
                    for i, stock in enumerate(results.get("top_bullish", [])[:3]):
                        existing_stock = (
                            db.query(StockData)
                            .filter(StockData.symbol == stock["symbol"])
                            .first()
                        )

                        if existing_stock:
                            existing_stock.bullish_rank = i + 1
                            existing_stock.ranking_score = stock["ranking_score"]
                        else:
                            # Create new StockData record
                            new_stock = StockData(
                                symbol=stock["symbol"],
                                current_price=stock["current_price"],
                                previous_close=stock["current_price"]
                                - stock["price_change"],
                                open_price=stock["current_price"],
                                high_price=stock["current_price"],
                                low_price=stock["current_price"],
                                volume=stock["volume"],
                                price_change=stock["price_change"],
                                price_change_percent=stock["price_change_percent"],
                                sector=sector,
                                bullish_rank=i + 1,
                                ranking_score=stock["ranking_score"],
                            )
                            db.add(new_stock)

                    # Update bearish rankings
                    for i, stock in enumerate(results.get("top_bearish", [])[:3]):
                        existing_stock = (
                            db.query(StockData)
                            .filter(StockData.symbol == stock["symbol"])
                            .first()
                        )

                        if existing_stock:
                            existing_stock.bearish_rank = i + 1
                            if not existing_stock.ranking_score:
                                existing_stock.ranking_score = stock["ranking_score"]
                        else:
                            # Create new StockData record
                            new_stock = StockData(
                                symbol=stock["symbol"],
                                current_price=stock["current_price"],
                                previous_close=stock["current_price"]
                                - stock["price_change"],
                                open_price=stock["current_price"],
                                high_price=stock["current_price"],
                                low_price=stock["current_price"],
                                volume=stock["volume"],
                                price_change=stock["price_change"],
                                price_change_percent=stock["price_change_percent"],
                                sector=sector,
                                bearish_rank=i + 1,
                                ranking_score=stock["ranking_score"],
                            )
                            db.add(new_stock)

                db.commit()
                logger.info("Updated stock rankings in database")

        except Exception as e:
            logger.error(f"Failed to update stock rankings: {e}")

    async def _update_sector_top_stocks(self, sector_results: Dict[str, Dict]) -> None:
        """Update SectorSentiment table with top stock lists"""
        try:
            with SessionLocal() as db:
                for sector, results in sector_results.items():
                    sentiment_record = (
                        db.query(SectorSentiment)
                        .filter(SectorSentiment.sector == sector)
                        .first()
                    )

                    if sentiment_record:
                        # Format top stocks for JSON storage
                        top_bullish = [
                            {
                                "symbol": stock["symbol"],
                                "change_percent": stock["price_change_percent"],
                                "volume_ratio": stock["volume_ratio"],
                            }
                            for stock in results.get("top_bullish", [])[:3]
                        ]

                        top_bearish = [
                            {
                                "symbol": stock["symbol"],
                                "change_percent": stock["price_change_percent"],
                                "volume_ratio": stock["volume_ratio"],
                            }
                            for stock in results.get("top_bearish", [])[:3]
                        ]

                        sentiment_record.top_bullish_stocks = json.dumps(top_bullish)
                        sentiment_record.top_bearish_stocks = json.dumps(top_bearish)

                db.commit()
                logger.info("Updated sector top stocks in sentiment table")

        except Exception as e:
            logger.error(f"Failed to update sector top stocks: {e}")


# Global instance
_stock_ranker: Optional[StockRanker] = None


def get_stock_ranker() -> StockRanker:
    """Get global stock ranker instance"""
    global _stock_ranker
    if _stock_ranker is None:
        _stock_ranker = StockRanker()
    return _stock_ranker
