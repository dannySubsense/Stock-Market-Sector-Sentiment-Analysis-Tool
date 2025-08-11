"""
Data Persistence Service - TimescaleDB Integration
Stores stock data, sector sentiment, and IWM benchmark data for historical analysis
Maintains cache-first performance while adding persistent storage capability
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from sqlalchemy import and_, desc, text

from core.database import SessionLocal
from models.sector_sentiment import SectorSentiment  # Legacy - for backward compatibility
from models.sector_sentiment_1d import SectorSentiment1D  # New 1D-specific model
from typing import Dict as _DictForHint  # prevent name clash in annotations
# Avoid importing IWM benchmark service at module import time to prevent
# pulling optional dependencies during non-IWM code paths
if TYPE_CHECKING:
    from services.iwm_benchmark_service_1d import IWMBenchmarkData1D

logger = logging.getLogger(__name__)


class DataPersistenceService:
    """
    Hybrid data persistence service for TimescaleDB
    Stores market data for historical analysis while maintaining cache performance
    """

    def __init__(self):
        self.db_session_factory = SessionLocal

    async def store_stock_price_data(self, stock_data_list: List[_DictForHint[str, Any]]) -> bool:
        """
        Store real-time stock price data to TimescaleDB stock_prices_1D table

        Args:
            stock_data_list: List of StockData1D objects from API calls

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as db:
                # Use TimescaleDB-optimized batch insert
                insert_data = []
                current_time = datetime.now(UTC)

                for stock_data in stock_data_list:
                    # Convert StockData1D to TimescaleDB stock_prices_1D format
                    price_record = {
                        "symbol": stock_data.symbol,
                        "timestamp": current_time,
                        "close_price": stock_data.current_price,
                        "open_price": stock_data.current_price,  # Current price as proxy
                        "high_price": stock_data.current_price,
                        "low_price": stock_data.current_price,
                        "volume": stock_data.current_volume,
                        "created_at": current_time,
                    }
                    insert_data.append(price_record)

                # Batch insert for performance
                if insert_data:
                    db.execute(
                        text(
                            """
                        INSERT INTO stock_prices_1D
                        (symbol, timestamp, open_price, high_price, low_price,
                         close_price, volume, created_at)
                        VALUES (:symbol, :timestamp, :open_price, :high_price,
                                :low_price, :close_price, :volume, :created_at)
                        """
                        ),
                        insert_data,
                    )
                    db.commit()
                    logger.info(
                        f"Stored {len(insert_data)} stock price records to TimescaleDB"
                    )

                return True

        except Exception as e:
            logger.error(f"Error storing stock price data: {e}")
            return False

    async def store_fmp_batch_price_data(
        self, fmp_quotes: List[Dict[str, Any]]
    ) -> bool:
        """
        Store FMP batch quote data directly to stock_prices_1d table
        Optimized for FMP batch workflow performance and data format

        Args:
            fmp_quotes: List of FMP quote dictionaries from batch API

        Returns:
            True if successful, False otherwise
        """
        try:
            if not fmp_quotes:
                logger.warning("No FMP quotes provided for storage")
                return True

            with self.db_session_factory() as db:
                insert_data = []
                current_time = datetime.now(UTC)
                skipped_count = 0

                for quote in fmp_quotes:
                    try:
                        # Validate required FMP quote fields
                        if not all(
                            key in quote for key in ["symbol", "price", "previousClose"]
                        ):
                            logger.warning(
                                f"Skipping quote with missing fields: {quote.get('symbol', 'N/A')}"
                            )
                            skipped_count += 1
                            continue

                        # Extract and validate FMP data
                        symbol = quote["symbol"].upper()
                        current_price = float(quote["price"] or 0)
                        previous_close = float(quote["previousClose"] or 0)
                        current_volume = int(quote.get("volume") or 0)

                        # Extract OHLC data if available, otherwise use current price
                        open_price = float(quote.get("open") or current_price)
                        high_price = float(quote.get("dayHigh") or current_price)
                        low_price = float(quote.get("dayLow") or current_price)

                        # Skip invalid price data
                        if current_price <= 0 or previous_close <= 0:
                            logger.warning(f"Skipping {symbol} - invalid price data")
                            skipped_count += 1
                            continue

                        # Create FMP Multiple Company Prices API record
                        price_record = {
                            "symbol": symbol,
                            "fmp_timestamp": int(current_time.timestamp()),
                            "name": quote.get("name"),
                            "price": current_price,
                            "changes_percentage": float(quote.get("changesPercentage") or 0),
                            "change": float(quote.get("change") or 0),
                            "day_low": float(quote.get("dayLow") or current_price),
                            "day_high": float(quote.get("dayHigh") or current_price),
                            "year_high": float(quote.get("yearHigh") or current_price),
                            "year_low": float(quote.get("yearLow") or current_price),
                            "market_cap": int(quote.get("marketCap") or 0),
                            "price_avg_50": float(quote.get("priceAvg50") or 0),
                            "price_avg_200": float(quote.get("priceAvg200") or 0),
                            "exchange": quote.get("exchange"),
                            "volume": current_volume,
                            "avg_volume": int(quote.get("avgVolume") or current_volume),
                            "open_price": open_price,
                            "previous_close": previous_close,
                            "eps": float(quote.get("eps") or 0),
                            "pe": float(quote.get("pe") or 0),
                            "earnings_announcement": None,  # FMP doesn't provide this in quotes
                            "shares_outstanding": int(quote.get("sharesOutstanding") or 0),
                            "recorded_at": current_time,
                        }
                        insert_data.append(price_record)

                    except (ValueError, TypeError, KeyError) as e:
                        logger.warning(
                            f"Error processing quote for {quote.get('symbol', 'N/A')}: {e}"
                        )
                        skipped_count += 1
                        continue

                # Batch insert for optimal performance
                if insert_data:
                    db.execute(
                        text(
                            """
                        INSERT INTO stock_prices_1d
                        (symbol, fmp_timestamp, name, price, changes_percentage, change,
                         day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                         price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                         eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                        VALUES (:symbol, :fmp_timestamp, :name, :price, :changes_percentage, :change,
                                :day_low, :day_high, :year_high, :year_low, :market_cap, :price_avg_50,
                                :price_avg_200, :exchange, :volume, :avg_volume, :open_price, :previous_close,
                                :eps, :pe, :earnings_announcement, :shares_outstanding, :recorded_at)
                        """
                        ),
                        insert_data,
                    )
                    db.commit()

                    logger.info(
                        f"Stored {len(insert_data)} FMP price records to stock_prices_1d table"
                    )
                    if skipped_count > 0:
                        logger.info(
                            f"Skipped {skipped_count} invalid quotes during storage"
                        )

                    return True
                else:
                    logger.warning("No valid FMP quotes to store")
                    return False

        except Exception as e:
            logger.error(f"Error storing FMP batch price data: {e}")
            return False

    async def store_sector_sentiment_data(
        self,
        sector_results: Dict[str, Any],
        analysis_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store sector sentiment analysis results using atomic batch operations
        Validates complete 11-sector batch before storage

        Args:
            sector_results: Results from sector sentiment calculation
            analysis_metadata: Additional metadata about the analysis

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from services.sector_batch_validator import get_batch_validator

            # Validate and prepare atomic batch
            batch_validator = get_batch_validator()

            # Filter out unknown_sector before validation (expects exactly 11 sectors)
            filtered_sector_results = {
                sector: data for sector, data in sector_results.items() 
                if sector != "unknown_sector"
            }

            # Ensure sentiment scores are valid while keeping minimal 1D schema
            for sector_data in filtered_sector_results.values():
                sentiment_score = sector_data.get("sentiment_score", 0.0)
                
                # Only clean if sentiment_score is actually invalid (NaN, None, or extreme values)
                if (sentiment_score is None or 
                    not isinstance(sentiment_score, (int, float)) or
                    abs(sentiment_score) > 100.0):  # Extreme values beyond reasonable range
                    logger.warning(f"Cleaning invalid sentiment score: {sentiment_score} → 0.0")
                    sector_data["sentiment_score"] = 0.0
                # Drop non-1D fields if present to avoid ORM mismatches
                for extraneous in ("bullish_count", "bearish_count", "total_volume", "top_bullish_rankings", "top_bearish_rankings"):
                    if extraneous in sector_data:
                        sector_data.pop(extraneous, None)

            # Check if this is a single sector or full batch
            if len(filtered_sector_results) == 1:
                # Single sector - store directly without batch validation (minimal 1D schema)
                logger.info(f"Storing single sector: {list(filtered_sector_results.keys())[0]}")
                return await self._store_single_sector(filtered_sector_results, analysis_metadata)
            else:
                # Full batch - use batch validation
                try:
                    validated_batch = batch_validator.prepare_batch(
                        filtered_sector_results,
                        timeframe="1day",
                        analysis_metadata=analysis_metadata,
                    )
                except Exception as validation_error:
                    logger.error(f"Batch validation failed: {validation_error}")
                    return False

                # Store the complete validated batch atomically
                with self.db_session_factory() as db:
                    # Add all records in single transaction
                    for record in validated_batch:
                        db.add(record)

                    db.commit()

                    # Get batch summary for logging
                    batch_summary = batch_validator.get_batch_summary(validated_batch)
                    logger.info(
                        f"✅ Stored complete sector batch: {batch_summary['batch_id']} "
                        f"({batch_summary['sector_count']} sectors, "
                        f"avg sentiment: {batch_summary['avg_sentiment']:.3f})"
                    )

                    return True

        except Exception as e:
            logger.error(f"Error storing sector sentiment batch: {e}")
            return False

    async def _store_single_sector(
        self, sector_results: Dict[str, Any], analysis_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a single sector result without batch validation
        """
        try:
            from models.sector_sentiment_1d import SectorSentiment1D
            import json

            with self.db_session_factory() as db:
                for sector_name, sector_data in sector_results.items():
                    # Create sector sentiment record (minimal 1D schema)
                    record = SectorSentiment1D(
                        sector=sector_name,
                        batch_id="step6_single_sector",
                        sentiment_score=sector_data.get("sentiment_score", 0.0),
                        timestamp=sector_data.get("timestamp"),
                    )
                    
                    db.add(record)

                db.commit()
                logger.info(f"✅ Stored single sector: {list(sector_results.keys())[0]}")
                return True

        except Exception as e:
            logger.error(f"Error storing single sector: {e}")
            return False

    async def store_sector_sentiment(
        self,
        sector_results: Dict[str, Any], 
        analysis_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store sector sentiment analysis results (method called by SectorCalculator)
        Delegates to store_sector_sentiment_data for actual implementation
        
        Args:
            sector_results: Results from sector sentiment calculation
            analysis_metadata: Additional metadata about the analysis
            
        Returns:
            True if successful, False otherwise
        """
        return await self.store_sector_sentiment_data(sector_results, analysis_metadata)

    async def store_iwm_benchmark_data(self, iwm_data: "IWMBenchmarkData1D") -> bool:
        """
        Store IWM benchmark data for historical Russell 2000 tracking

        Args:
            iwm_data: IWM benchmark data from Step 4

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as db:
                # Store as stock price data with special IWM handling
                current_time = datetime.now(UTC)

                iwm_price_record = {
                    "symbol": "IWM",
                    "fmp_timestamp": int(current_time.timestamp() * 1000),  # FMP timestamp format
                    "name": "iShares Russell 2000 ETF",
                    "price": iwm_data.current_price,
                    "changes_percentage": iwm_data.performance_1d,
                    "change": iwm_data.current_price - iwm_data.previous_close,
                    "day_low": iwm_data.current_price,
                    "day_high": iwm_data.current_price,
                    "year_high": iwm_data.current_price,
                    "year_low": iwm_data.current_price,
                    "market_cap": 1000000000,  # Placeholder for ETF
                    "price_avg_50": iwm_data.current_price,
                    "price_avg_200": iwm_data.current_price,
                    "exchange": "NASDAQ",
                    "volume": 0,  # ETF volume not critical for our analysis
                    "avg_volume": 0,
                    "open_price": iwm_data.previous_close,
                    "previous_close": iwm_data.previous_close,
                    "eps": 0.0,
                    "pe": 0.0,
                    "earnings_announcement": None,
                    "shares_outstanding": 100000000,
                    "recorded_at": current_time,
                }

                db.execute(
                    text(
                        """
                    INSERT INTO stock_prices_1d
                    (symbol, fmp_timestamp, name, price, changes_percentage, change,
                     day_low, day_high, year_high, year_low, market_cap, price_avg_50,
                     price_avg_200, exchange, volume, avg_volume, open_price, previous_close,
                     eps, pe, earnings_announcement, shares_outstanding, recorded_at)
                    VALUES (:symbol, :fmp_timestamp, :name, :price, :changes_percentage, :change,
                            :day_low, :day_high, :year_high, :year_low, :market_cap, :price_avg_50,
                            :price_avg_200, :exchange, :volume, :avg_volume, :open_price, :previous_close,
                            :eps, :pe, :earnings_announcement, :shares_outstanding, :recorded_at)
                    """
                    ),
                    iwm_price_record,
                )

                db.commit()
                logger.info(
                    f"Stored IWM benchmark data: {iwm_data.performance_1d:.3f}%"
                )
                return True

        except Exception as e:
            logger.error(f"Error storing IWM benchmark data: {e}")
            return False

    async def get_historical_sector_data(
        self, sector: str, timeframe: str = "1day", days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical sector sentiment data for analysis

        Args:
            sector: Sector name to query
            timeframe: Timeframe to query (default: "1day")
            days_back: Number of days to look back

        Returns:
            List of historical sector sentiment records
        """
        try:
            with self.db_session_factory() as db:
                start_date = datetime.now(UTC) - timedelta(days=days_back)

                historical_data = (
                    db.query(SectorSentiment)
                    .filter(
                        and_(
                            SectorSentiment.sector == sector,
                            SectorSentiment.timeframe == timeframe,
                            SectorSentiment.timestamp >= start_date,
                        )
                    )
                    .order_by(desc(SectorSentiment.timestamp))
                    .all()
                )

                # Convert to dictionaries for analysis
                result = []
                for record in historical_data:
                    result.append(
                        {
                            "sector": record.sector,
                            "timeframe": record.timeframe,
                            "timestamp": record.timestamp,
                            "sentiment_score": record.sentiment_score,
                            "bullish_count": record.bullish_count,
                            "bearish_count": record.bearish_count,
                            "total_volume": record.total_volume,
                        }
                    )

                logger.info(
                    f"Retrieved {len(result)} historical records for {sector} ({timeframe})"
                )
                return result

        except Exception as e:
            logger.error(f"Error retrieving historical sector data: {e}")
            return []

    async def get_historical_stock_prices(
        self, symbol: str, days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical stock price data from TimescaleDB

        Args:
            symbol: Stock symbol to query
            days_back: Number of days to look back

        Returns:
            List of historical price records
        """
        try:
            with self.db_session_factory() as db:
                start_date = datetime.now(UTC) - timedelta(days=days_back)

                # Use TimescaleDB-optimized query
                query = text(
                    """
                    SELECT symbol, timestamp, open_price, high_price, low_price, close_price, volume
                    FROM stock_prices_1D
                    WHERE symbol = :symbol
                    AND timestamp >= :start_date
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """
                )

                result = db.execute(
                    query, {"symbol": symbol, "start_date": start_date}
                ).fetchall()

                # Convert to dictionaries
                price_history = []
                for row in result:
                    price_history.append(
                        {
                            "symbol": row.symbol,
                            "timestamp": row.timestamp,
                            "open_price": float(row.open_price or 0),
                            "high_price": float(row.high_price or 0),
                            "low_price": float(row.low_price or 0),
                            "close_price": float(row.close_price or 0),
                            "volume": int(row.volume or 0),
                        }
                    )

                logger.info(
                    f"Retrieved {len(price_history)} price records for {symbol}"
                )
                return price_history

        except Exception as e:
            logger.error(f"Error retrieving historical stock prices: {e}")
            return []

    async def cleanup_old_data(self, retention_days: int = 90) -> bool:
        """
        Clean up old data based on retention policy

        Args:
            retention_days: Number of days to retain data

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as db:
                cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

                # Clean up old sector sentiment data
                deleted_sentiment = (
                    db.query(SectorSentiment)
                    .filter(SectorSentiment.created_at < cutoff_date)
                    .delete()
                )

                # Clean up old stock price data using TimescaleDB
                deleted_prices = db.execute(
                    text("DELETE FROM stock_prices_1d WHERE timestamp < :cutoff_date"),
                    {"cutoff_date": cutoff_date},
                ).rowcount

                db.commit()

                logger.info(
                    f"Cleaned up {deleted_sentiment} sentiment records and "
                    f"{deleted_prices} price records"
                )
                return True

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

    async def cleanup_before_analysis(self, timeframe: str) -> bool:
        """
        Plan 1: Mandatory cleanup before timeframe analysis
        Removes stale data that could affect sector calculations

        Args:
            timeframe: Timeframe for analysis (1d, 30min, 3d, 1w)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as db:
                current_time = datetime.now(UTC)

                # Define timeframe-specific stale data thresholds
                stale_thresholds = {
                    "1d": timedelta(hours=24),  # 1D data older than 24 hours
                    "30min": timedelta(hours=4),  # 30min data older than 4 hours
                    "3d": timedelta(days=4),  # 3D data older than 4 days
                    "1w": timedelta(days=8),  # 1W data older than 8 days
                }

                threshold = stale_thresholds.get(timeframe, timedelta(hours=24))
                cutoff_time = current_time - threshold

                # Clean timeframe-specific price data
                deleted_prices = 0
                if timeframe == "1d":
                    # Convert datetime to Unix timestamp for comparison with fmp_timestamp
                    cutoff_timestamp = int(cutoff_time.timestamp())
                    deleted_prices = db.execute(
                        text(
                            "DELETE FROM stock_prices_1d WHERE fmp_timestamp < :cutoff_timestamp"
                        ),
                        {"cutoff_timestamp": cutoff_timestamp},
                    ).rowcount
                # Future: elif timeframe == "30min": cleanup stock_prices_30min
                # Future: elif timeframe == "3d": cleanup stock_prices_3d
                # Future: elif timeframe == "1w": cleanup stock_prices_1w

                # Clean stale sector sentiment for this timeframe
                # Note: Using sector_sentiment_1d table, not the old sector_sentiment table
                deleted_sentiment = db.execute(
                    text(
                        "DELETE FROM sector_sentiment_1d WHERE timestamp < :cutoff_time"
                    ),
                    {"cutoff_time": cutoff_time},
                ).rowcount

                db.commit()

                logger.info(
                    f"Pre-analysis cleanup for {timeframe}: removed "
                    f"{deleted_prices} price records and {deleted_sentiment} "
                    f"sentiment records older than {threshold}"
                )
                return True

        except Exception as e:
            logger.error(f"Error in pre-analysis cleanup for {timeframe}: {e}")
            return False

    async def cleanup_stale_session_data(self, timeframe: str) -> bool:
        """
        Plan 1: Remove data from previous trading session
        Ensures fresh start for new analysis cycle

        Args:
            timeframe: Timeframe for analysis (1d, 30min, 3d, 1w)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_session_factory() as db:
                current_time = datetime.now(UTC)

                # Define session-based cutoffs (previous trading day)
                session_cutoff = current_time.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                # For intraday timeframes, be more aggressive
                if timeframe in ["30min"]:
                    session_cutoff = current_time - timedelta(hours=6)  # 6 hours ago
                elif timeframe == "1d":
                    session_cutoff = current_time - timedelta(hours=18)  # Previous day

                # Clean session-specific data
                deleted_prices = 0
                if timeframe == "1d":
                    # Convert datetime to Unix timestamp for comparison with fmp_timestamp
                    session_cutoff_timestamp = int(session_cutoff.timestamp())
                    deleted_prices = db.execute(
                        text(
                            "DELETE FROM stock_prices_1d WHERE fmp_timestamp < :session_cutoff_timestamp"
                        ),
                        {"session_cutoff_timestamp": session_cutoff_timestamp},
                    ).rowcount

                # Clean session sentiment data
                # Note: Using sector_sentiment_1d table, not the old sector_sentiment table
                deleted_sentiment = db.execute(
                    text(
                        "DELETE FROM sector_sentiment_1d WHERE timestamp < :session_cutoff"
                    ),
                    {"session_cutoff": session_cutoff},
                ).rowcount

                db.commit()

                logger.info(
                    f"Session cleanup for {timeframe}: removed {deleted_prices} "
                    f"price records and {deleted_sentiment} sentiment records "
                    f"from previous session"
                )
                return True

        except Exception as e:
            logger.error(f"Error in session cleanup for {timeframe}: {e}")
            return False


# Global service instance
_persistence_service = None


def get_persistence_service() -> DataPersistenceService:
    """Get singleton persistence service instance"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = DataPersistenceService()
    return _persistence_service
